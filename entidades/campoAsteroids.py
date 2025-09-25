import pygame
import random
from .asteroid import Asteroid
from constants import *


class CampoAsteroids(pygame.sprite.Sprite):
    edges = [
        [
            pygame.Vector2(1, 0),
            lambda y: pygame.Vector2(-MAIOR_ASTEROID, y * ALTURA_TELA),
        ],
        [
            pygame.Vector2(-1, 0),
            lambda y: pygame.Vector2(
                LARGURA_TELA + MAIOR_ASTEROID, y * ALTURA_TELA
            ),
        ],
        [
            pygame.Vector2(0, 1),
            lambda x: pygame.Vector2(x * LARGURA_TELA, -MAIOR_ASTEROID),
        ],
        [
            pygame.Vector2(0, -1),
            lambda x: pygame.Vector2(
                x * LARGURA_TELA, ALTURA_TELA + MAIOR_ASTEROID
            ),
        ],
    ]

    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.spawn_timer = 0.0

    def spawn(self, radius, position, velocity):
        asteroid = Asteroid(position.x, position.y, radius)
        asteroid.velocity = velocity

    def update(self, dt):
        self.spawn_timer += dt
        if self.spawn_timer > TEMPO_DE_GERACAO_ASTEROID:
            self.spawn_timer = 0

            edge = random.choice(self.edges)
            speed = random.randint(40, 100)
            velocity = edge[0] * speed
            velocity = velocity.rotate(random.randint(-30, 30))
            position = edge[1](random.uniform(0, 1))
            self.spawn(random.randint(MENOR_ASTEROID, MAIOR_ASTEROID), position, velocity)
