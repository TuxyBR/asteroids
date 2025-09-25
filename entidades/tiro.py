import pygame
from .formaCirculo import FormaCirculo
from constants import TAMANHO_TIRO

class Tiro(FormaCirculo):
  def __init__(self, x, y):
    super().__init__(x, y, TAMANHO_TIRO)
  
  def draw(self, screen):
    pygame.draw.circle(screen, "white", self.position, self.radius, 2)
    
  def update(self, dt):
    self.move(dt)
    
  def move(self, dt):
    self.position += self.velocidade * dt
    
  def rotate(self, dt):
    pass
