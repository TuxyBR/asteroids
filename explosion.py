import pygame
import random

class Explosion(pygame.sprite.Sprite):
  def __init__(self, pos):
    if hasattr(self, "containers"):
      super().__init__(self.containers)
    else:
      super().__init__()
    self.particles = [ExplosionParticle(pos) for _ in range(int(random.uniform(15,40)))]

  def update(self, dt):
    for particle in self.particles:
      particle.update(dt)
    self.particles = [particle for particle in self.particles if not particle.is_dead()]

  def draw(self, surface):
    for particle in self.particles:
      particle.draw(surface)

  def is_dead(self):
    return len(self.particles) == 0


class ExplosionParticle:
  def __init__(self, pos):
    self.pos = pygame.Vector2(pos)
    self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)) * random.uniform(50, 150)
    self.lifetime = random.uniform(0.6, 0.9)
    self.age = 0
    self.color = pygame.Color("white")

  def update(self, dt):
    self.pos += self.velocity * dt
    self.age += dt
    fade = max(0, 255 * (1 - self.age / self.lifetime))
    self.color.a = int(fade)

  def draw(self, surface):
    if self.color.a > 0:
      start_pos = ((self.pos.x), (self.pos.y))
      end_pos = ((self.pos.x - self.velocity.x * 0.05), (self.pos.y - self.velocity.y * 0.05))
      pygame.draw.line(surface, self.color, start_pos, end_pos, 2)

  def is_dead(self):
    return self.age >= self.lifetime
