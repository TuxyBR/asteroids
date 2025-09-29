import random
import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, MIN_ASTEROID_RADIUS, MAX_ASTEROID_RADIUS
from entities.asteroid import Asteroid


class MenuScreen:

  def __init__(self):
    self.menu_options = ["Play", "Multiplayer", "Scores", "Quit"] #TODO: implement multiplayer and scores
    self.selected_option = 0

    self.title_font = pygame.font.SysFont("monospace", 72, bold=True)
    self.menu_font = pygame.font.SysFont("monospace", 42, bold=True)
    self.hud_font = pygame.font.SysFont("monospace", 36, bold=True)

    self.background_asteroids = pygame.sprite.Group()
    self._init_background()

  def handle_event(self, event):
    if event.type != pygame.KEYDOWN:
      return None

    if event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
      self.selected_option = (self.selected_option - 1) % len(self.menu_options)
    elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
      self.selected_option = (self.selected_option + 1) % len(self.menu_options)
    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
      choice = self.menu_options[self.selected_option]
      if choice == "Play":
        return ("start_game", None)
      if choice == "Scores":
        return ("show_scores", None)
      if choice == "Quit":
        return ("quit", None)

    return None

  def update(self, dt):
    self.background_asteroids.update(dt)
    self._resolve_background_collisions()
    self._wrap_background_asteroids()
    pygame.display.set_caption("Asteroids by TuxyBR")
    return None

  def draw(self, surface):
    surface.fill("black")

    for asteroid in self.background_asteroids:
      asteroid.draw(surface)

    title_text = self.title_font.render("ASTEROIDS", True, "white")
    title_rect = title_text.get_rect(center=((SCREEN_WIDTH // 2), SCREEN_HEIGHT // 5))
    surface.blit(title_text, title_rect)
    
    menu_x = 80
    menu_y = SCREEN_HEIGHT - 80
    item_spacing = 48

    for index, option in enumerate(self.menu_options):
      color = "white" if index == self.selected_option else "gray"
      option_surface = self.menu_font.render(option, True, color)
      offset = len(self.menu_options) - index - 1
      option_rect = option_surface.get_rect(midleft=(menu_x, (menu_y - offset * item_spacing)))
      surface.blit(option_surface, option_rect)

  def _init_background(self):
    Asteroid.containers = (self.background_asteroids,)
    for _ in range(10):
      asteroid = Asteroid(
        random.uniform(0, SCREEN_WIDTH),
        random.uniform(0, SCREEN_HEIGHT),
        random.randint(MIN_ASTEROID_RADIUS, MAX_ASTEROID_RADIUS),
      )
      speed = random.uniform(20, 80)
      direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
      if direction.length_squared() == 0:
        direction = pygame.Vector2(1, 0)
      asteroid.velocity = direction.normalize() * speed

  def _wrap_background_asteroids(self):
    for asteroid in self.background_asteroids:
      asteroid.wrap_position()

  def _resolve_background_collisions(self):
    asteroids = list(self.background_asteroids)
    total = len(asteroids)

    for i in range(total):
      asteroid_a = asteroids[i]
      for j in range(i + 1, total):
        asteroid_b = asteroids[j]

        delta = asteroid_b.position - asteroid_a.position
        distance = delta.length()
        min_distance = asteroid_a.radius + asteroid_b.radius

        if distance == 0:
          delta = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
          distance = delta.length() or 1.0

        if distance >= min_distance:
          continue

        normal = delta / distance
        overlap = min_distance - distance
        correction = normal * (overlap / 2)
        asteroid_a.position -= correction
        asteroid_b.position += correction

        relative_velocity = asteroid_a.velocity - asteroid_b.velocity
        if relative_velocity.length_squared() < 1e-6:
          impulse_strength = random.uniform(20, 40)
          impulse = normal * impulse_strength
          asteroid_a.velocity += impulse
          asteroid_b.velocity -= impulse
          continue

        asteroid_a.velocity = asteroid_a.velocity.reflect(normal)
        asteroid_b.velocity = asteroid_b.velocity.reflect(-normal)

        min_normal_speed = 20
        a_speed = asteroid_a.velocity.dot(-normal)
        if a_speed < min_normal_speed:
          asteroid_a.velocity += -normal * (min_normal_speed - a_speed)

        b_speed = asteroid_b.velocity.dot(normal)
        if b_speed < min_normal_speed:
          asteroid_b.velocity += normal * (min_normal_speed - b_speed)
