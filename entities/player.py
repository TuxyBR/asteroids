import pygame
from .circle_shape import FormaCirculo
from constants import (
  PLAYER_ACCELERATION,
  PLAYER_BACKWARD_ACCELERATION,
  PLAYER_DECELERATION_MULTIPLIER,
  PLAYER_RADIUS,
  PLAYER_SPEED,
  PLAYER_TURN_SPEED,
  PROJECTILE_SPEED,
)
from entities.shot import Tiro

class Jogador(FormaCirculo):
  def __init__(self, x, y):
    super().__init__(x, y, PLAYER_RADIUS)
    self.rotation = 0
    self.shot_cooldown = 0
    self._paused = False
    self.velocity = pygame.Vector2()

  def triangle(self):
    forward = pygame.Vector2(0, 1).rotate(self.rotation)
    right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
    a = self.position + forward * self.radius
    b = self.position - forward * self.radius - right
    c = self.position - forward * self.radius + right
    return [a, b, c]
  
  def draw(self, screen):
    pygame.draw.polygon(screen, "white", self.triangle(), 2)
    
  def rotate(self, dt):
    self.rotation += PLAYER_TURN_SPEED * dt
    
  def update(self, dt):
    if self._paused:
      return

    keys = pygame.key.get_pressed()

    if self.shot_cooldown > 0:
      self.shot_cooldown -= dt
    else:
      if keys[pygame.K_SPACE]:
        self.shoot()

    forward_pressed = keys[pygame.K_w] or keys[pygame.K_UP]
    backward_pressed = keys[pygame.K_s] or keys[pygame.K_DOWN]
    move_direction = int(forward_pressed) - int(backward_pressed)

    self.move(dt, move_direction)

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
      self.rotate(-dt)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
      self.rotate(dt)
      
  def move(self, dt, direction):
    forward = pygame.Vector2(0, 1).rotate(self.rotation)

    if direction != 0:
      acceleration = PLAYER_ACCELERATION
      if direction < 0:
        acceleration *= PLAYER_BACKWARD_ACCELERATION
      thrust = forward * (acceleration * direction * dt)
      self.velocity += thrust
      speed = self.velocity.length()
      if speed > PLAYER_SPEED:
        self.velocity.scale_to_length(PLAYER_SPEED)
    else:
      speed = self.velocity.length()
      if speed > 0:
        deceleration = PLAYER_ACCELERATION * PLAYER_DECELERATION_MULTIPLIER * dt
        new_speed = max(0, speed - deceleration)
        if new_speed == 0:
          self.velocity.update(0, 0)
        else:
          self.velocity.scale_to_length(new_speed)
        if new_speed < 0.01:
          self.velocity.update(0, 0)

    self.position += self.velocity * dt
    
  def shoot(self):
    shot = Tiro(self.position[0], self.position[1])
    shot.velocity = pygame.Vector2(0, 1).rotate(self.rotation) * PROJECTILE_SPEED
    self.shot_cooldown = 0.3

  def set_paused(self, paused: bool):
    self._paused = paused

  def is_paused(self):
    return self._paused
    
