import random

import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from entities.player import Player
from entities.player_input import PlayerInputState
from entities.asteroid import Asteroid
from entities.asteroid_field import AsteroidField
from entities.shot import Shot
from entities.explosion import Explosion
from screens.pause_menu import PauseMenu


class GameScreen:

  def __init__(self, asteroid_field=None):
    self.update_group = pygame.sprite.Group()
    self.draw_group = pygame.sprite.Group()
    self.asteroid_group = pygame.sprite.Group()
    self.shot_group = pygame.sprite.Group()

    Player.containers = (self.update_group, self.draw_group)
    Asteroid.containers = (self.asteroid_group, self.update_group, self.draw_group)
    Shot.containers = (self.shot_group, self.update_group, self.draw_group)
    Explosion.containers = (self.update_group, self.draw_group)

    self.players = []
    self.player_registry = {}
    self.player_inputs = {}
    self.pending_respawns = {}
    self.allow_respawns = False
    self.respawn_delay = 3.0
    self._new_explosions = []

    self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    self._register_player(self.player)
    self.asteroid_field = asteroid_field
    if self.asteroid_field is None:
      self.asteroid_field = AsteroidField(self.asteroid_group, self.update_group)
    else:
      self.asteroid_field.asteroid_group = self.asteroid_group
      self.asteroid_field.add(self.update_group)

    self.explosions = []
    self.score = 0

    self.hud_font = pygame.font.SysFont("monospace", 36, bold=True)
    self.pause_menu = None
    self.uses_local_keyboard = True

  def _set_all_players_paused(self, paused):
    for player in self.players:
      player.set_paused(paused)

  def _all_players_paused(self):
    return all(player.is_paused() for player in self.players)

  def _register_player(self, player: Player):
    self.players.append(player)
    self.player_registry[player.player_id] = player
    self.player_inputs.setdefault(player.player_id, player.input_state)
    return player

  def spawn_player(self, x=None, y=None, player_id=None):
    if x is None:
      x = random.uniform(SCREEN_WIDTH * 0.25, SCREEN_WIDTH * 0.75)
    if y is None:
      y = random.uniform(SCREEN_HEIGHT * 0.25, SCREEN_HEIGHT * 0.75)

    player = Player(x, y, player_id=player_id)
    return self._register_player(player)

  def get_player(self, player_id):
    return self.player_registry.get(player_id)

  def set_player_input(self, player_id, input_state):
    self.player_inputs[player_id] = input_state
    player = self.player_registry.get(player_id)
    if player is not None:
      player.set_input_state(input_state)
      return

    respawn_info = self.pending_respawns.get(player_id)
    if respawn_info and respawn_info.get("awaiting_input"):
      if self._input_requests_respawn(input_state):
        self._respawn_player(player_id)

  def remove_player(self, player_id):
    player = self.player_registry.pop(player_id, None)
    if player is None:
      return
    if player in self.players:
      self.players.remove(player)
    player.kill()

  def handle_event(self, event):
    if self.pause_menu is not None:
      transition = self.pause_menu.handle_event(event)
      if transition is None:
        return None

      action, payload = transition
      if action == "resume":
        self._set_all_players_paused(False)
        self.pause_menu = None
        return None

      if action == "return_to_menu":
        self._set_all_players_paused(False)
        self.pause_menu = None
        return ("return_to_menu", payload)

      return None

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
      if self.players:
        self._set_all_players_paused(True)
      if self._all_players_paused() and self.pause_menu is None:
        self.pause_menu = PauseMenu()

    return None

  def update(self, dt):
    if self.pause_menu is not None:
      self.pause_menu.update(dt)
      return None

    pygame.display.set_caption(f"Asteroids by TuxyBR - Score: {self.score}")

    if self.uses_local_keyboard and self.players:
      primary_player = self.players[0]
      primary_state = PlayerInputState.from_keyboard()
      self.set_player_input(primary_player.player_id, primary_state)

    self._update_respawns(dt)
    self.update_group.update(dt)

    for asteroid in list(self.asteroid_group):
      for player in list(self.players):
        if asteroid.collides_with(player):
          if self.allow_respawns:
            self._handle_player_death(player)
            break
          return ("game_over", {"score": self.score})

      for shot in list(self.shot_group):
        if asteroid.collides_with(shot):
          self.score += asteroid.split()
          explosion = Explosion(asteroid.position)
          self.explosions.append(explosion)
          self._new_explosions.append(explosion)
          shot.kill()

    self.explosions = [explosion for explosion in self.explosions if not explosion.is_dead()]

    return None

  def draw(self, surface):
    surface.fill("black")

    for drawable in self.draw_group:
      drawable.draw(surface)

    score_text = self.hud_font.render(f"Score: {self.score}", True, "gray")
    text_rect = score_text.get_rect()
    surface.blit(score_text, (30, SCREEN_HEIGHT - text_rect.height - 15))

    if self.pause_menu is not None:
      overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
      overlay.fill((0, 0, 0, 180))
      surface.blit(overlay, (0, 0))
      self.pause_menu.draw(surface)

  def _handle_player_death(self, player: Player):
    player_id = player.player_id
    self.remove_player(player_id)
    self.pending_respawns[player_id] = {
      "time_left": self.respawn_delay,
      "awaiting_input": False,
    }

  def _update_respawns(self, dt):
    to_respawn = []
    for player_id, info in list(self.pending_respawns.items()):
      if not info["awaiting_input"]:
        info["time_left"] -= dt
        if info["time_left"] <= 0:
          info["time_left"] = 0
          info["awaiting_input"] = True

      if info["awaiting_input"]:
        input_state = self.player_inputs.get(player_id)
        if input_state and self._input_requests_respawn(input_state):
          to_respawn.append(player_id)

    for player_id in to_respawn:
      self._respawn_player(player_id)

  def _respawn_player(self, player_id):
    input_state = self.player_inputs.get(player_id, PlayerInputState())
    player = self.spawn_player(player_id=player_id)
    player.set_input_state(input_state)
    self.player_inputs[player_id] = input_state
    self.pending_respawns.pop(player_id, None)

  def _input_requests_respawn(self, input_state: PlayerInputState) -> bool:
    return bool(
      input_state.shoot
      or input_state.thrust
      or input_state.reverse
      or input_state.rotate_left
      or input_state.rotate_right
    )

  def get_respawn_status(self):
    status = []
    for player_id, info in self.pending_respawns.items():
      if info["awaiting_input"]:
        message = "Press any control to respawn"
      else:
        message = f"Respawn in {info['time_left']:.1f}s"
      status.append((player_id, message))
    return status

  def consume_new_explosions(self):
    pending = self._new_explosions
    self._new_explosions = []
    return pending
