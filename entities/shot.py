import pygame
from .circle_shape import FormaCirculo
from constants import SHOT_RADIUS

class Tiro(FormaCirculo):
  def __init__(self, x, y):
    super().__init__(x, y, SHOT_RADIUS)
  
  def draw(self, screen):
    pygame.draw.circle(screen, "white", self.position, self.radius, 2)
    
  def update(self, dt):
    self.move(dt)
    
  def move(self, dt):
    self.position += self.velocity * dt
    
  def rotate(self, dt):
    pass
