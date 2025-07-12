import sys
import pygame

from constants import *

from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot

def main():
  pygame.init()
  
  update_group = pygame.sprite.Group()
  draw_group = pygame.sprite.Group()
  asteroid_group = pygame.sprite.Group()
  shot_group = pygame.sprite.Group()
  
  Player.containers = (update_group, draw_group)
  Asteroid.containers = (asteroid_group, update_group, draw_group)
  AsteroidField.containers = (update_group)
  Shot.containers = (shot_group, update_group, draw_group)
  
  dt = 0
  score = 0
  fps_limit = 60
  clock = pygame.time.Clock()
  
  screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
  asteroid_field = AsteroidField()
  font = pygame.font.SysFont("monospace", 36, bold=True)

  while True:
    pygame.display.set_caption(f"Asteroids by TuxyBR - Score: {score}")
    score_text = font.render(f"Score: {score}", True, "gray")
    text_rect = score_text.get_rect()
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        return

    screen.fill("black")
    update_group.update(dt)
    for asteroid in asteroid_group:
      if asteroid.colision(player):
        print(f"Game Over! - Final score: {score}")
        sys.exit()
      for shot in shot_group:
        if asteroid.colision(shot):
          score += asteroid.split()
          shot.kill()
    for drawable in draw_group:
      drawable.draw(screen)
    screen.blit(score_text, (30, SCREEN_HEIGHT - text_rect.height - 15))

    dt = clock.tick(fps_limit) / 1000
    pygame.display.flip()


if __name__ == "__main__":
  main()