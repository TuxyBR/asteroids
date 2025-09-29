import uuid

import pygame
from .circle_shape import CircleShape
from constants import SHOT_RADIUS

class Shot(CircleShape):
  def __init__(self, x, y, entity_id=None):
    super().__init__(x, y, SHOT_RADIUS)
    self.entity_id = entity_id or uuid.uuid4().hex
  
  def draw(self, screen):
    pygame.draw.circle(screen, "white", self.position, self.radius, 2)
    
  def update(self, dt):
    self.move(dt)
    
  def move(self, dt):
    self.position += self.velocity * dt
    
  def rotate(self, dt):
    pass
