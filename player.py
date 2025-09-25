import pygame
from circleshape import CircleShape
from constants import PLAYER_RADIUS, PLAYER_SHOT_SPEED, PLAYER_TURN_SPEED, PLAYER_SPEED
from shot import Shot

class Player(CircleShape):
  def __init__(self, x, y, *, color="white", is_local=True, player_id=None, on_shoot=None):
    super().__init__(x, y, PLAYER_RADIUS)
    self.rotation = 0
    self.shot_cooldown = 0
    self.color = color
    self.is_local = is_local
    self.player_id = player_id
    self._on_shoot = on_shoot
    self.alive = True

  def triangle(self):
    forward = pygame.Vector2(0, 1).rotate(self.rotation)
    right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
    a = self.position + forward * self.radius
    b = self.position - forward * self.radius - right
    c = self.position - forward * self.radius + right
    return [a, b, c]
  
  def draw(self, screen):
    if not self.alive:
      return
    pygame.draw.polygon(screen, self.color, self.triangle(), 2)
    
  def rotate(self, dt):
    self.rotation += PLAYER_TURN_SPEED * dt
    
  def update(self, dt):
    if not self.is_local or not self.alive:
      return
    keys = pygame.key.get_pressed()

    if self.shot_cooldown > 0:
      self.shot_cooldown -= dt
    else:
      if keys[pygame.K_SPACE]:
        self.shoot()

    if keys[pygame.K_w]:
      self.move(dt)
    if keys[pygame.K_s]:
      self.move(-dt)

    if keys[pygame.K_a]:
      self.rotate(-dt)
    if keys[pygame.K_d]:
      self.rotate(dt)
      
  def move(self, dt): #TODO: acceleration in movement
    forward = pygame.Vector2(0, 1).rotate(self.rotation)
    self.position += forward * PLAYER_SPEED * dt
    
  def shoot(self):
    # If an external shoot handler is set, use it to decide how to shoot
    if self._on_shoot is not None:
      handled = self._on_shoot(self)
      if handled:
        self.shot_cooldown = 0.3
        return
    shot = Shot(self.position[0], self.position[1])
    shot.velocity = pygame.Vector2(0, 1).rotate(self.rotation) * PLAYER_SHOT_SPEED
    self.shot_cooldown = 0.3

  def die(self):
    self.alive = False
    # remove from sprite groups so it no longer updates/draws
    self.kill()
    
