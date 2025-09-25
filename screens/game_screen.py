import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from entities.player import Jogador
from entities.asteroid import Asteroid
from entities.asteroid_field import CampoAsteroids
from entities.shot import Tiro
from entities.explosion import Explosao
from screens.pause_menu import MenuPause


class TelaJogo:

  def __init__(self):
    self.update_group = pygame.sprite.Group()
    self.draw_group = pygame.sprite.Group()
    self.asteroid_group = pygame.sprite.Group()
    self.shot_group = pygame.sprite.Group()

    Jogador.containers = (self.update_group, self.draw_group)
    Asteroid.containers = (self.asteroid_group, self.update_group, self.draw_group)
    CampoAsteroids.containers = self.update_group
    Tiro.containers = (self.shot_group, self.update_group, self.draw_group)
    Explosao.containers = (self.update_group, self.draw_group)

    self.player = Jogador(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    self.asteroid_field = CampoAsteroids()

    self.players = [self.player]
    self.explosions = []
    self.score = 0

    self.hud_font = pygame.font.SysFont("monospace", 36, bold=True)
    self.pause_menu = None

  def _set_all_players_paused(self, paused):
    for player in self.players:
      player.set_paused(paused)

  def _all_players_paused(self):
    return all(player.is_paused() for player in self.players)

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
      # For now, treat the primary player as the one requesting a pause.
      if self.players:
        self.players[0].set_paused(True)
      if self._all_players_paused() and self.pause_menu is None:
        self.pause_menu = MenuPause()

    return None

  def update(self, dt):
    if self.pause_menu is not None:
      self.pause_menu.update(dt)
      return None

    pygame.display.set_caption(f"Asteroids by TuxyBR - Score: {self.score}")

    self.update_group.update(dt)

    for asteroid in list(self.asteroid_group):
      for player in self.players:
        if asteroid.collides_with(player):
          return ("game_over", {"score": self.score})

      for shot in list(self.shot_group):
        if asteroid.collides_with(shot):
          self.score += asteroid.split()
          self.explosions.append(Explosao(asteroid.position))
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
