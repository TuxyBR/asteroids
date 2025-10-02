import random

import pygame

from constants import (
  PLAYER_BACKWARD_ACCELERATION,
  PLAYER_RADIUS,
  PLAYER_THRUST_IDLE_PARTICLE_RATE,
  PLAYER_THRUST_PARTICLE_BASE_OFFSET,
  PLAYER_THRUST_PARTICLE_RATE,
  SHOT_RADIUS,
)
from entities.player_input import PlayerInputState
from entities.thrust_particle import ThrustParticle
from entities.explosion import Explosion
from screens.pause_menu import PauseMenu
from services.multiplayer import MultiplayerClientSession


class _RemoteThrustEmitter:

  def __init__(self):
    self.particles = []
    self._residual = 0.0

  def update(self, dt, position, rotation, velocity, input_state: PlayerInputState):
    forward = pygame.Vector2(0, 1).rotate(rotation)
    backward_direction = -forward

    speed = velocity.length()

    thrusting = input_state.thrust
    reversing = input_state.reverse

    emission_strength = 0.0
    emission_rate = 0.0

    if thrusting:
      emission_strength = 1.0
      emission_rate = PLAYER_THRUST_PARTICLE_RATE
    elif reversing:
      emission_strength = max(0.2, PLAYER_BACKWARD_ACCELERATION)
      emission_rate = PLAYER_THRUST_PARTICLE_RATE * 0.7
    elif speed > 20:
      emission_strength = 0.35
      emission_rate = PLAYER_THRUST_IDLE_PARTICLE_RATE
    elif speed > 5:
      emission_strength = 0.2
      emission_rate = PLAYER_THRUST_IDLE_PARTICLE_RATE * 0.5
    else:
      emission_strength = 0.1
      emission_rate = PLAYER_THRUST_IDLE_PARTICLE_RATE * 0.25

    if emission_rate > 0:
      emit_offset = PLAYER_RADIUS + PLAYER_THRUST_PARTICLE_BASE_OFFSET * (0.25 + 0.75 * emission_strength)
      emit_pos_base = position - forward * emit_offset
      lateral_offset = forward.rotate(90)

      self._residual += emission_rate * dt
      while self._residual >= 1.0:
        self._residual -= 1.0
        jitter = lateral_offset * random.uniform(-PLAYER_RADIUS * 0.4, PLAYER_RADIUS * 0.4)
        emit_pos = emit_pos_base + jitter
        particle = ThrustParticle(emit_pos, backward_direction, emission_strength, velocity)
        self.particles.append(particle)

    for particle in self.particles:
      particle.update(dt)
    self.particles = [particle for particle in self.particles if not particle.is_dead()]

  def draw(self, surface):
    for particle in self.particles:
      particle.draw(surface)


class MultiplayerClientGameScreen:

  def __init__(self, config):
    self.config = config
    self.session = None
    self._session_closed = True
    self.session = MultiplayerClientSession(config)
    self.session.start()
    self._session_closed = False

    self.player_id = None
    self.players = {}
    self.asteroids = {}
    self.shots = {}
    self.score = 0
    self.thrust_emitters = {}
    self.remote_explosions = {}
    self.local_pause_menu = None
    self.global_pause_menu = None
    self.local_paused = False
    self._desired_pause = False
    self._leave_sent = False
    self._host_all_paused = False

    self.hud_font = pygame.font.SysFont("monospace", 32, bold=True)
    self.info_font = pygame.font.SysFont("monospace", 24, bold=True)

    self._last_input_state = PlayerInputState()

  def _ensure_session_stopped(self):
    if self._session_closed or self.session is None:
      return
    self._send_leave()
    self.session.stop()
    self._session_closed = True

  def _send_leave(self):
    if self._leave_sent or self.session is None:
      return
    self.session.publish_leave()
    self._leave_sent = True

  def _set_local_pause(self, paused: bool, force: bool = False):
    paused = bool(paused)
    if not force and self._desired_pause == paused:
      return
    self._desired_pause = paused
    if paused and self.local_pause_menu is None:
      self.local_pause_menu = PauseMenu()
    if not paused and self.local_pause_menu is not None:
      self.local_pause_menu = None
    if not self._session_closed:
      self.session.publish_pause_state(paused)
    self.local_paused = paused

  def handle_event(self, event):
    if self.local_pause_menu is not None:
      transition = self.local_pause_menu.handle_event(event)
      if transition is None:
        return None

      action, payload = transition
      if action == "resume":
        self._set_local_pause(False, force=True)
        return None

      if action == "return_to_menu":
        self._set_local_pause(False, force=True)
        self._send_leave()
        self._ensure_session_stopped()
        return ("return_to_menu", None)

      return None

    if self.global_pause_menu is not None:
      transition = self.global_pause_menu.handle_event(event)
      if transition is None:
        return None

      action, payload = transition
      if action == "resume":
        self._set_local_pause(False, force=True)
        self.global_pause_menu = None
        return None

      if action == "return_to_menu":
        self._set_local_pause(False, force=True)
        self._send_leave()
        self._ensure_session_stopped()
        self.global_pause_menu = None
        return ("return_to_menu", None)

      return None

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
      self._set_local_pause(True)
      return None
    return None

  def update(self, dt):
    if self.player_id is None and self.session.player_id is not None:
      self.player_id = self.session.player_id
      if self._desired_pause and not self._session_closed:
        self.session.publish_pause_state(True)

    state = self.session.consume_state()
    if state is not None:
      self._apply_state(state)

    event = self.session.consume_event()
    if event is not None and event.get("type") == "game_over":
      self._ensure_session_stopped()
      payload = {"score": event.get("score", 0)}
      return ("game_over", payload)

    raw_input = PlayerInputState.from_keyboard()
    if self.local_pause_menu is None and self.global_pause_menu is None:
      current_input = raw_input
    else:
      current_input = PlayerInputState()
    if current_input != self._last_input_state:
      self.session.publish_input(current_input)
      self._last_input_state = current_input

    caption = f"Asteroids - Session {self.config.session_id}"
    if self.player_id:
      caption += f" - Player {self.player_id}"
    pygame.display.set_caption(caption)

    if self.local_pause_menu is not None:
      self.local_pause_menu.update(dt)
    if self.global_pause_menu is not None:
      self.global_pause_menu.update(dt)

    for player_id in list(self.thrust_emitters.keys()):
      if player_id not in self.players:
        del self.thrust_emitters[player_id]

    for player_id, player_state in self.players.items():
      emitter = self.thrust_emitters.setdefault(player_id, _RemoteThrustEmitter())
      velocity = player_state["velocity"]
      input_state = player_state["input"]
      if player_state.get("paused"):
        emitter.update(dt, player_state["position"], player_state["rotation"], pygame.Vector2(), PlayerInputState())
      else:
        emitter.update(dt, player_state["position"], player_state["rotation"], velocity, input_state)

    for explosion_id, explosion in list(self.remote_explosions.items()):
      explosion.update(dt)
      if explosion.is_dead():
        del self.remote_explosions[explosion_id]

    return None

  def draw(self, surface):
    surface.fill("black")

    for asteroid in self.asteroids.values():
      points = []
      for point in asteroid["points"]:
        rotated = point.rotate(asteroid["rotation"])
        final_point = asteroid["position"] + rotated
        points.append((final_point.x, final_point.y))
      if points:
        pygame.draw.polygon(surface, "white", points, 1)

    for shot in self.shots.values():
      position = shot["position"]
      color = shot.get("color", (255, 255, 255))
      pygame.draw.circle(surface, color, (int(position.x), int(position.y)), SHOT_RADIUS, 2)

    for explosion in self.remote_explosions.values():
      explosion.draw(surface)

    for emitter in self.thrust_emitters.values():
      emitter.draw(surface)

    for player in self.players.values():
      forward = pygame.Vector2(0, 1).rotate(player["rotation"])
      right = pygame.Vector2(0, 1).rotate(player["rotation"] + 90) * PLAYER_RADIUS / 1.5
      a = player["position"] + forward * PLAYER_RADIUS
      b = player["position"] - forward * PLAYER_RADIUS - right
      c = player["position"] - forward * PLAYER_RADIUS + right
      color = player.get("color", (255, 255, 255))
      pygame.draw.polygon(surface, color, [(a.x, a.y), (b.x, b.y), (c.x, c.y)], 2)

    score_surface = self.hud_font.render(f"Score: {self.score}", True, "gray")
    surface.blit(score_surface, (30, surface.get_height() - score_surface.get_height() - 20))

    info_lines = []
    if self.player_id:
      info_lines.append(f"You are player {self.player_id}")
    info_lines.append("Press ESC to open the pause menu")

    if self.player_id and self.player_id not in self.players:
      info_lines.append("Waiting for respawn... press any control once ready")

    if self.global_pause_menu is not None:
      info_lines.append("Game paused")

    for index, line in enumerate(info_lines):
      label = self.info_font.render(line, True, "gray")
      surface.blit(label, (20, 20 + index * 24))

    if self.local_pause_menu is not None:
      overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
      overlay.fill((0, 0, 0, 180))
      surface.blit(overlay, (0, 0))
      self.local_pause_menu.draw(surface)
    elif self.global_pause_menu is not None:
      overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
      overlay.fill((0, 0, 0, 180))
      surface.blit(overlay, (0, 0))
      self.global_pause_menu.draw(surface)

  def _apply_state(self, state):
    self.score = state.get("score", 0)

    new_players = {}
    for player in state.get("players", []):
      player_id = player.get("id")
      if not player_id:
        continue
      position = pygame.Vector2(*player.get("position", (0.0, 0.0)))
      velocity = pygame.Vector2(*player.get("velocity", (0.0, 0.0)))
      input_state = PlayerInputState.from_dict(player.get("input", {}))
      color_data = player.get("color")
      if isinstance(color_data, (list, tuple)) and len(color_data) >= 3:
        color = tuple(int(color_data[i]) for i in range(3))
      else:
        color = (255, 255, 255)

      new_players[player_id] = {
        "position": position,
        "rotation": player.get("rotation", 0.0),
        "velocity": velocity,
        "input": input_state,
        "paused": bool(player.get("paused", False)),
        "color": color,
      }

    self.players = new_players

    if self.player_id and self.player_id in new_players:
      self.local_paused = bool(new_players[self.player_id]["paused"])
    else:
      self.local_paused = False

    host_all_paused = bool(new_players) and all(player.get("paused") for player in new_players.values())
    self._host_all_paused = host_all_paused
    if host_all_paused:
      if self.global_pause_menu is None:
        self.global_pause_menu = PauseMenu()
    else:
      self.global_pause_menu = None

    if self._desired_pause and self.local_pause_menu is None and not host_all_paused:
      self.local_pause_menu = PauseMenu()
    if not self._desired_pause and self.local_pause_menu is not None and not host_all_paused:
      self.local_pause_menu = None

    new_asteroids = {}
    for asteroid in state.get("asteroids", []):
      asteroid_id = asteroid.get("id")
      if not asteroid_id:
        continue
      position = pygame.Vector2(*asteroid.get("position", (0.0, 0.0)))
      points = [pygame.Vector2(*point) for point in asteroid.get("points", [])]
      new_asteroids[asteroid_id] = {
        "position": position,
        "rotation": asteroid.get("rotation", 0.0),
        "points": points,
      }
    self.asteroids = new_asteroids

    new_shots = {}
    for shot in state.get("shots", []):
      shot_id = shot.get("id")
      if not shot_id:
        continue
      position = pygame.Vector2(*shot.get("position", (0.0, 0.0)))
      color_data = shot.get("color")
      if isinstance(color_data, (list, tuple)) and len(color_data) >= 3:
        color = tuple(int(color_data[i]) for i in range(3))
      else:
        color = (255, 255, 255)
      new_shots[shot_id] = {"position": position, "color": color}
    self.shots = new_shots

    effects = state.get("effects", {})
    for explosion in effects.get("new_explosions", []):
      explosion_id = explosion.get("id")
      if not explosion_id or explosion_id in self.remote_explosions:
        continue
      position = pygame.Vector2(*explosion.get("position", (0.0, 0.0)))
      self.remote_explosions[explosion_id] = Explosion(position, entity_id=explosion_id)

  def __del__(self):
    if hasattr(self, "session"):
      self._ensure_session_stopped()
