import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class PauseMenu:
  def __init__(self):
    self.options = ["Continue", "Quit"]
    self.selected_index = 0

    self.title_font = pygame.font.SysFont("monospace", 64, bold=True)
    self.option_font = pygame.font.SysFont("monospace", 42, bold=True)
    self.hint_font = pygame.font.SysFont("monospace", 28, bold=True)

  def handle_event(self, event):
    if event.type != pygame.KEYDOWN:
      return None

    if event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
      self.selected_index = (self.selected_index - 1) % len(self.options)
    elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
      self.selected_index = (self.selected_index + 1) % len(self.options)
    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
      choice = self.options[self.selected_index]
      if event.key == pygame.K_ESCAPE or choice == "Continue":
        return ("resume", None)
      if choice == "Quit":
        return ("return_to_menu", None)

    return None

  def update(self, dt):
    return None

  def draw(self, surface):
    title_surface = self.title_font.render("Paused", True, "white")
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    surface.blit(title_surface, title_rect)

    spacing = 70
    start_y = SCREEN_HEIGHT // 2

    for index, option in enumerate(self.options):
      color = "white" if index == self.selected_index else "gray"
      option_surface = self.option_font.render(option, True, color)
      option_rect = option_surface.get_rect(center=(SCREEN_WIDTH // 2, start_y + index * spacing))
      surface.blit(option_surface, option_rect)
