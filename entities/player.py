import random
import uuid

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
from entities.player_input import PlayerInputState


def color_from_uuid(player_id: str) -> pygame.Color:
  seed = int(player_id[:8], 16)
  hue = seed % 360
  saturation = 75 + (seed % 20)  # keep colors vibrant but distinct
  value = 85 + (seed // 20 % 15)
  color = pygame.Color(0)
  color.hsva = (hue, min(saturation, 100), min(value, 100), 100)
  return color

class Player(CircleShape):
  def __init__(self, x, y, player_id=None):
    super().__init__(x, y, PLAYER_RADIUS)
    self.player_id = player_id or uuid.uuid4().hex
    self.color = color_from_uuid(self.player_id)
    self.rotation = 0
    self.shot_cooldown = 0
    self._paused = False
    self.velocity = pygame.Vector2()
    self.thrust_particles = []
    self._thrust_emit_residual = 0.0
    self.input_state = PlayerInputState()

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
    pygame.draw.polygon(screen, self.color, self.triangle(), 2)

  def get_polygon(self):
    return self.triangle()
    
  def rotate(self, dt):
    self.rotation += PLAYER_TURN_SPEED * dt
    
  def update(self, dt):
    if self._paused:
      return

    if self.shot_cooldown > 0:
      self.shot_cooldown -= dt

    if self.input_state.shoot and self.shot_cooldown <= 0:
      self.shoot()

    move_direction = int(self.input_state.thrust) - int(self.input_state.reverse)

    self.move(dt, move_direction)
    self._emit_thrust(dt, move_direction)
    self._update_thrust_particles(dt)

    if self.input_state.rotate_left:
      self.rotate(-dt)
    if self.input_state.rotate_right:
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
    shot = Shot(self.position[0], self.position[1], color=self.color)
    shot.velocity = pygame.Vector2(0, 1).rotate(self.rotation) * PROJECTILE_SPEED
    self.shot_cooldown = 0.3

  def set_paused(self, paused: bool):
    self._paused = paused

  def is_paused(self):
    return self._paused

  def set_input_state(self, input_state: PlayerInputState):
    self.input_state = input_state
    
