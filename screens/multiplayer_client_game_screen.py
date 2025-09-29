import pygame

from constants import PLAYER_RADIUS, SHOT_RADIUS
from entities.player_input import PlayerInputState
from services.multiplayer import MultiplayerClientSession


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

    self.hud_font = pygame.font.SysFont("monospace", 32, bold=True)
    self.info_font = pygame.font.SysFont("monospace", 24, bold=True)

    self._last_input_state = PlayerInputState()

  def _ensure_session_stopped(self):
    if self._session_closed or self.session is None:
      return
    self.session.stop()
    self._session_closed = True

  def handle_event(self, event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
      self._ensure_session_stopped()
      return ("return_to_menu", None)
    return None

  def update(self, dt):
    if self.player_id is None and self.session.player_id is not None:
      self.player_id = self.session.player_id

    state = self.session.consume_state()
    if state is not None:
      self._apply_state(state)

    event = self.session.consume_event()
    if event is not None and event.get("type") == "game_over":
      self._ensure_session_stopped()
      payload = {"score": event.get("score", 0)}
      return ("game_over", payload)

    current_input = PlayerInputState.from_keyboard()
    if current_input != self._last_input_state:
      self.session.publish_input(current_input)
      self._last_input_state = current_input

    caption = f"Asteroids - Session {self.config.session_id}"
    if self.player_id:
      caption += f" - Player {self.player_id}"
    pygame.display.set_caption(caption)
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
      pygame.draw.circle(surface, "white", (int(position.x), int(position.y)), SHOT_RADIUS, 2)

    for player in self.players.values():
      forward = pygame.Vector2(0, 1).rotate(player["rotation"])
      right = pygame.Vector2(0, 1).rotate(player["rotation"] + 90) * PLAYER_RADIUS / 1.5
      a = player["position"] + forward * PLAYER_RADIUS
      b = player["position"] - forward * PLAYER_RADIUS - right
      c = player["position"] - forward * PLAYER_RADIUS + right
      pygame.draw.polygon(surface, "white", [(a.x, a.y), (b.x, b.y), (c.x, c.y)], 2)

    score_surface = self.hud_font.render(f"Score: {self.score}", True, "gray")
    surface.blit(score_surface, (30, surface.get_height() - score_surface.get_height() - 20))

    info_lines = [
      f"Broker: {self.config.broker}:{self.config.port}",
      f"Session: {self.config.session_id}",
    ]
    if self.player_id:
      info_lines.append(f"You are player {self.player_id}")
    info_lines.append("Press ESC to leave the session")

    if self.player_id and self.player_id not in self.players:
      info_lines.append("Waiting for respawn... press any control once ready")

    for index, line in enumerate(info_lines):
      label = self.info_font.render(line, True, "gray")
      surface.blit(label, (20, 20 + index * 24))

  def _apply_state(self, state):
    self.score = state.get("score", 0)

    new_players = {}
    for player in state.get("players", []):
      player_id = player.get("id")
      if not player_id:
        continue
      position = pygame.Vector2(*player.get("position", (0.0, 0.0)))
      new_players[player_id] = {
        "position": position,
        "rotation": player.get("rotation", 0.0),
      }
    self.players = new_players

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
      new_shots[shot_id] = {"position": position}
    self.shots = new_shots

  def __del__(self):
    if hasattr(self, "session"):
      self._ensure_session_stopped()
