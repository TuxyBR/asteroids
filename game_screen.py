import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot
from explosion import Explosion


class TelaJogo:

  def __init__(self):
    self.update_group = pygame.sprite.Group()
    self.draw_group = pygame.sprite.Group()
    self.asteroid_group = pygame.sprite.Group()
    self.shot_group = pygame.sprite.Group()

    Player.containers = (self.update_group, self.draw_group)
    Asteroid.containers = (self.asteroid_group, self.update_group, self.draw_group)
    AsteroidField.containers = self.update_group
    Shot.containers = (self.shot_group, self.update_group, self.draw_group)
    Explosion.containers = (self.update_group, self.draw_group)

    self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    self.asteroid_field = AsteroidField()

    self.explosions = []
    self.score = 0

    self.hud_font = pygame.font.SysFont("monospace", 36, bold=True)

  def handle_event(self, event):
    return None

  def update(self, dt):
    pygame.display.set_caption(f"Asteroids by TuxyBR - Score: {self.score}")

    self.update_group.update(dt)

    for asteroid in list(self.asteroid_group):
      if asteroid.colision(self.player):
        return ("game_over", {"score": self.score})

      for shot in list(self.shot_group):
        if asteroid.colision(shot):
          self.score += asteroid.split()
          self.explosions.append(Explosion(asteroid.position))
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
