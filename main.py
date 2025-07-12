from constants import *

import pygame

from player import Player

def main():
  pygame.init()
  update_group = pygame.sprite.Group()
  draw_group = pygame.sprite.Group()
  Player.containers = (update_group, draw_group)
  fps = pygame.time.Clock()
  dt = 0
  fps_limit = 60
  screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

  while True:
    pygame.display.set_caption(f"Asteroids - Frame: {fps}")
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        return

    screen.fill("black")
    update_group.update(dt)
    for drawable in draw_group:
      drawable.draw(screen)

    dt = fps.tick(fps_limit) / 1000
    pygame.display.flip()


if __name__ == "__main__":
  main()