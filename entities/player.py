import random

import pygame
from .circle_shape import CircleShape
from constants import (
  PLAYER_ACCELERATION,
  PLAYER_BACKWARD_ACCELERATION,
  PLAYER_DECELERATION_MULTIPLIER,
  PLAYER_RADIUS,
  PLAYER_SPEED,
  PLAYER_TURN_SPEED,
  PLAYER_THRUST_IDLE_PARTICLE_RATE,
  PLAYER_THRUST_PARTICLE_BASE_OFFSET,
  PLAYER_THRUST_PARTICLE_RATE,
  PROJECTILE_SPEED,
)
from entities.shot import Shot
from entities.thrust_particle import ThrustParticle

class Player(CircleShape):
  def __init__(self, x, y):
    super().__init__(x, y, PLAYER_RADIUS)
    self.rotation = 0
    self.shot_cooldown = 0
    self._paused = False
    self.velocity = pygame.Vector2()
    self.thrust_particles = []
    self._thrust_emit_residual = 0.0

  def triangle(self):
    forward = pygame.Vector2(0, 1).rotate(self.rotation)
    right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
    a = self.position + forward * self.radius
    b = self.position - forward * self.radius - right
    c = self.position - forward * self.radius + right
    return [a, b, c]
  
  def draw(self, screen):
    for particle in self.thrust_particles:
      particle.draw(screen)
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
    self._emit_thrust(dt, move_direction)
    self._update_thrust_particles(dt)

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
    self.wrap_position()

  def _emit_thrust(self, dt, direction):
    forward = pygame.Vector2(0, 1).rotate(self.rotation)
    backward_direction = -forward

    speed = self.velocity.length()
    emission_strength = 0.0
    emission_rate = 0.0

    if direction > 0:
      emission_strength = 1.0
      emission_rate = PLAYER_THRUST_PARTICLE_RATE
    elif direction < 0:
      emission_strength = max(0.2, PLAYER_BACKWARD_ACCELERATION)
      emission_rate = PLAYER_THRUST_PARTICLE_RATE * 0.7
    elif speed > 20:
      emission_strength = 0.35
      emission_rate = PLAYER_THRUST_IDLE_PARTICLE_RATE
    elif speed > 5:
      emission_strength = 0.2
      emission_rate = PLAYER_THRUST_IDLE_PARTICLE_RATE * 0.5
    else:
      emission_strength = 0.1
      emission_rate = PLAYER_THRUST_IDLE_PARTICLE_RATE * 0.25

    if emission_rate <= 0:
      return

    emit_offset = self.radius + PLAYER_THRUST_PARTICLE_BASE_OFFSET * (0.25 + 0.75 * emission_strength)
    emit_pos_base = self.position - forward * emit_offset
    lateral_offset = forward.rotate(90)

    self._thrust_emit_residual += emission_rate * dt
    while self._thrust_emit_residual >= 1.0:
      self._thrust_emit_residual -= 1.0
      jitter = lateral_offset * random.uniform(-self.radius * 0.4, self.radius * 0.4)
      emit_pos = emit_pos_base + jitter
      particle = ThrustParticle(emit_pos, backward_direction, emission_strength, self.velocity)
      self.thrust_particles.append(particle)

  def _update_thrust_particles(self, dt):
    for particle in self.thrust_particles:
      particle.update(dt)
    self.thrust_particles = [particle for particle in self.thrust_particles if not particle.is_dead()]
    
  def shoot(self):
    shot = Shot(self.position[0], self.position[1])
    shot.velocity = pygame.Vector2(0, 1).rotate(self.rotation) * PROJECTILE_SPEED
    self.shot_cooldown = 0.3

  def set_paused(self, paused: bool):
    self._paused = paused

  def is_paused(self):
    return self._paused
    
