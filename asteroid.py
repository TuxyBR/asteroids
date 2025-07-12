import pygame
import random
from circleshape import CircleShape
from constants import ASTEROID_MIN_RADIUS, PLAYER_RADIUS

class Asteroid(CircleShape):
  def __init__(self, x, y, radius):
    super().__init__(x, y, radius)
    self.rotation = 0
    self.move_direction = 0
  
  def draw(self, screen): #TODO: sprite based system
    pygame.draw.circle(screen, "white", self.position, self.radius, 2)
    
  def update(self, dt):
    self.move(dt)
    
  def move(self, dt):
    self.position += self.velocity * dt
    
  def rotate(self, dt):
    pass
  
  def split(self):
    self.kill()
    angle = random.uniform(20, 50)
    if self.radius > ASTEROID_MIN_RADIUS:
      for i in range(random.randrange(1, 5)):
        angle *= random.uniform(1, 2)
        new_vector = self.velocity.rotate(angle)
        new_radius = self.radius - random.uniform(15, self.radius-25)
        new_asteroid = Asteroid(self.position[0], self.position[1], new_radius)
        new_asteroid.velocity = new_vector * random.uniform(1.2, 1.5)
        