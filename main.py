from constants import *

import pygame

def main():
    pygame.init()
    fps = pygame.time.Clock()
    dt = 0
    fps_limit = 60
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    while True:
        pygame.display.set_caption(f"Asteroids - Frame: {fps}")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        
        screen.fill("black")
        
        dt = fps.tick(fps_limit) / 1000
        pygame.display.flip()


if __name__ == "__main__":
    main()
