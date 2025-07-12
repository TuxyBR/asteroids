import pygame
from circleshape import CircleShape
from constants import PLAYER_RADIUS

class Asteroid(CircleShape):
  def __init__(self, x, y, radius):
    super().__init__(x, y, radius)
    self.rotation = 0
    self.move_direction = 0
  
  def draw(self, screen):
    pygame.draw.circle(screen, "white", self.position, self.radius, 2)
    
  def update(self, dt):
    self.move(dt)
    
  def move(self, dt):
    self.position += self.velocity * dt
    
  def rotate(self, dt):
    pass