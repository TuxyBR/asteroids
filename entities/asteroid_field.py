import pygame
import random

from .asteroid import Asteroid
from constants import (
    ASTEROID_SPAWN_INTERVAL,
    MAX_ASTEROID_RADIUS,
    MAX_MEDIUM_ASTEROIDS,
    MIN_ASTEROID_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class AsteroidField(pygame.sprite.Sprite):
    edges = [
        [
            pygame.Vector2(1, 0),
            lambda y: pygame.Vector2(-MAX_ASTEROID_RADIUS, y * SCREEN_HEIGHT),
        ],
        [
            pygame.Vector2(-1, 0),
            lambda y: pygame.Vector2(
                SCREEN_WIDTH + MAX_ASTEROID_RADIUS, y * SCREEN_HEIGHT
            ),
        ],
        [
            pygame.Vector2(0, 1),
            lambda x: pygame.Vector2(x * SCREEN_WIDTH, -MAX_ASTEROID_RADIUS),
        ],
        [
            pygame.Vector2(0, -1),
            lambda x: pygame.Vector2(
                x * SCREEN_WIDTH, SCREEN_HEIGHT + MAX_ASTEROID_RADIUS
            ),
        ],
    ]

    def __init__(self, asteroid_group, *groups):
        super().__init__(*groups)
        self.spawn_timer = 0.0
        self.asteroid_group = asteroid_group

    def spawn(self, radius, position, velocity):
        asteroid = Asteroid(position.x, position.y, radius)
        asteroid.velocity = velocity

    def update(self, dt):
        self.spawn_timer += dt
        if self.spawn_timer > ASTEROID_SPAWN_INTERVAL:
            self.spawn_timer -= ASTEROID_SPAWN_INTERVAL

            if not self._can_spawn_more_medium():
                return

            edge = random.choice(self.edges)
            speed = random.randint(40, 100)
            velocity = edge[0] * speed
            velocity = velocity.rotate(random.randint(-30, 30))
            position = edge[1](random.uniform(0, 1))
            self.spawn(random.randint(MIN_ASTEROID_RADIUS, MAX_ASTEROID_RADIUS), position, velocity)

    def _can_spawn_more_medium(self):
        if self.asteroid_group is None:
            return True

        threshold = MAX_ASTEROID_RADIUS / 2
        medium_count = sum(1 for asteroid in self.asteroid_group if asteroid.radius >= threshold)
        return medium_count < MAX_MEDIUM_ASTEROIDS
