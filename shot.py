import pygame
from circleshape import CircleShape
from constants import SHOT_RADIUS

class Shot(CircleShape):
  _id_counter = 1
  def __init__(self, x, y, *, shot_id=None, host_controlled=False):
    super().__init__(x, y, SHOT_RADIUS)
    if shot_id is None:
      shot_id = Shot._id_counter
      Shot._id_counter += 1
    self.shot_id = shot_id
    self.host_controlled = host_controlled
  
  def draw(self, screen):
    pygame.draw.circle(screen, "white", self.position, self.radius, 2)
    
  def update(self, dt):
    # When host-controlled is False (on clients), position is updated by MQTT
    if self.host_controlled:
      self.move(dt)
    
  def move(self, dt):
    self.position += self.velocity * dt
    
  def rotate(self, dt):
    pass
