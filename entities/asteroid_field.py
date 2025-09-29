import pygame
import random

from .asteroid import Asteroid
from .collision_utils import polygon_collision_mtv
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

            if self._can_spawn_more_medium():
                edge = random.choice(self.edges)
                speed = random.randint(40, 100)
                velocity = edge[0] * speed
                velocity = velocity.rotate(random.randint(-30, 30))
                position = edge[1](random.uniform(0, 1))
                self.spawn(random.randint(MIN_ASTEROID_RADIUS, MAX_ASTEROID_RADIUS), position, velocity)

        self._resolve_collisions()

    def _can_spawn_more_medium(self):
        if self.asteroid_group is None:
            return True

        threshold = MAX_ASTEROID_RADIUS / 2
        medium_count = sum(1 for asteroid in self.asteroid_group if asteroid.radius >= threshold)
        return medium_count < MAX_MEDIUM_ASTEROIDS

    def _resolve_collisions(self):
        if self.asteroid_group is None:
            return

        asteroids = list(self.asteroid_group)
        total = len(asteroids)
        for i in range(total):
            asteroid_a = asteroids[i]
            for j in range(i + 1, total):
                asteroid_b = asteroids[j]

                points_a = asteroid_a.get_polygon()
                points_b = asteroid_b.get_polygon()
                mtv = polygon_collision_mtv(points_a, points_b)

                if mtv is None:
                    continue

                normal, overlap = mtv
                correction = normal * (overlap / 2)
                asteroid_a.position -= correction
                asteroid_b.position += correction

                relative_velocity = asteroid_a.velocity - asteroid_b.velocity
                toward_speed = relative_velocity.dot(normal)

                if toward_speed <= 0:
                    if abs(toward_speed) < 1e-6:
                        impulse_strength = random.uniform(30, 60)
                        impulse = normal * impulse_strength
                        asteroid_a.velocity -= impulse
                        asteroid_b.velocity += impulse
                    continue

                asteroid_a.velocity = asteroid_a.velocity.reflect(normal)
                asteroid_b.velocity = asteroid_b.velocity.reflect(-normal)

                min_normal_speed = 40
                a_speed = asteroid_a.velocity.dot(-normal)
                if a_speed < min_normal_speed:
                    asteroid_a.velocity += -normal * (min_normal_speed - a_speed)

                b_speed = asteroid_b.velocity.dot(normal)
                if b_speed < min_normal_speed:
                    asteroid_b.velocity += normal * (min_normal_speed - b_speed)
