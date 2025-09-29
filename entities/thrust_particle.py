import random

import pygame

from constants import PLAYER_THRUST_PARTICLE_SPREAD


class ThrustParticle:
  def __init__(self, pos, backward_direction, strength, inherited_velocity):
    self.pos = pygame.Vector2(pos)
    direction = backward_direction.normalize() if backward_direction.length_squared() > 0 else pygame.Vector2(0, 1)
    angle_offset = random.uniform(-PLAYER_THRUST_PARTICLE_SPREAD, PLAYER_THRUST_PARTICLE_SPREAD) * (0.5 + 0.5 * strength)
    travel_direction = direction.rotate(angle_offset)

    speed_min = 80
    speed_max = 150
    speed = random.uniform(speed_min, speed_max) * (0.6 + 0.4 * strength)
    self.velocity = travel_direction * speed + inherited_velocity * 0.25

    lifetime_min = 0.25
    lifetime_max = 0.5
    self.lifetime = random.uniform(lifetime_min, lifetime_max) * (0.75 + 0.35 * strength)
    self.age = 0.0

    base_size = 1
    max_extra = 1
    self.size = base_size + int(max_extra * strength)

    self._brightness = 255

  def update(self, dt):
    self.pos += self.velocity * dt
    self.age += dt

    progress = min(1.0, self.age / self.lifetime)
    self._brightness = int(max(0, 255 * (1 - progress)))

  def draw(self, surface):
    if self._brightness <= 0:
      return

    color_value = self._brightness
    color = (color_value, color_value, color_value)
    center = (int(self.pos.x), int(self.pos.y))
    pygame.draw.circle(surface, color, center, max(1, self.size))

  def is_dead(self):
    return self.age >= self.lifetime or self._brightness <= 0
