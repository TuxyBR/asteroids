import pygame
import random
from .circle_shape import CircleShape
from constants import MIN_ASTEROID_RADIUS, MAX_ASTEROID_RADIUS

class Asteroid(CircleShape):
  def __init__(self, x, y, radius):
    super().__init__(x, y, radius)
    
    self.rotation = 0
    self.rotation_speed = random.randrange(-15, 15)
    
    self.sides = random.randrange(8, 20)
    self.jaggedness = random.uniform(0.2, 0.4)
    self.points = self.rng_polygon()
  
  def rng_polygon(self):
    points = []
    angle_step = 360 / self.sides
    for i in range(self.sides):
      angle = i * angle_step
      direction = pygame.Vector2(0, -1).rotate(angle)
      point = direction * self.radius * random.uniform(1 - self.jaggedness, 1 + self.jaggedness)
      points.append(point)
    return points
  
  def draw(self, screen):
    points = []
    for point in self.points:
      rotated = point.rotate(self.rotation)
      points.append(self.position + rotated)
    pygame.draw.polygon(screen, "white", points, 1)

    
  def update(self, dt):
    self.rotate(dt)
    self.move(dt)
    
  def move(self, dt):
    self.position += self.velocity * dt
    self.wrap_position()
    
  def rotate(self, dt):
    self.rotation += (self.rotation_speed * dt) % 360
  
  def split(self):
    score = int(MAX_ASTEROID_RADIUS - self.radius + MIN_ASTEROID_RADIUS)
    current_position = pygame.Vector2(self.position)
    current_velocity = pygame.Vector2(self.velocity)
    self.kill()

    if self.radius > MIN_ASTEROID_RADIUS * 2:
      asteroid_amount = random.randrange(2, 3)
      base_direction = current_velocity.normalize() if current_velocity.length_squared() > 0 else pygame.Vector2(0, -1).rotate(random.uniform(0, 360))
      base_angle = random.uniform(20, 50)
      base_speed = max(current_velocity.length(), 60)

      for index in range(asteroid_amount):
        direction = base_direction.rotate(base_angle * (-1 if index % 2 else 1) * random.uniform(0.8, 1.4))
        if direction.length_squared() == 0:
          direction = pygame.Vector2(0, -1)
        direction = direction.normalize()

        new_radius = max(MIN_ASTEROID_RADIUS, (self.radius / asteroid_amount) + random.uniform(-5, 5))
        offset_distance = (self.radius + new_radius) * 0.6
        spawn_position = current_position + direction * offset_distance

        new_speed = base_speed * random.uniform(0.7, 1.3)
        new_velocity = direction * new_speed

        new_asteroid = Asteroid(spawn_position.x, spawn_position.y, new_radius)
        new_asteroid.velocity = new_velocity

    return score
        
