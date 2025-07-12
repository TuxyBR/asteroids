import pygame
import random
from circleshape import CircleShape
from constants import ASTEROID_MIN_RADIUS, ASTEROID_MAX_RADIUS

class Asteroid(CircleShape):
  def __init__(self, x, y, radius):
    super().__init__(x, y, radius)
    
    self.rotation = 0
    self.rotation_speed = random.randrange(-15, 15)
    
    self.sides = random.randrange(8, 20)
    self.jaggedness = random.uniform(0.2, 0.4)
    self.points = self.rand_polygon()
  
  def rand_polygon(self):
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
    
  def rotate(self, dt):
    self.rotation += (self.rotation_speed * dt) % 360
  
  def split(self):
    score = int(ASTEROID_MAX_RADIUS - self.radius + ASTEROID_MIN_RADIUS)
    self.kill()
    angle = random.uniform(20, 50)
    if self.radius > ASTEROID_MIN_RADIUS*2:
      asteroid_amount = random.randrange(2, 3)
      for _ in range(asteroid_amount):
        new_vector = self.velocity.rotate(angle)
        angle *= random.uniform(1, 2)
        new_radius = (self.radius / asteroid_amount) + (random.uniform(-5, 5))
        new_asteroid = Asteroid(self.position.x, self.position.y, new_radius)
        new_asteroid.velocity = new_vector * random.uniform(1, 1.6)
    return(score)
        