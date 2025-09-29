import pygame


class MultiplayerMenuScreen:

  def __init__(self):
    self.options = ["Host Game", "Join Game", "Back"]
    self.selected = 0

    self.title_font = pygame.font.SysFont("monospace", 60, bold=True)
    self.option_font = pygame.font.SysFont("monospace", 40, bold=True)

  def handle_event(self, event):
    if event.type != pygame.KEYDOWN:
      return None

    if event.key in (pygame.K_UP, pygame.K_w):
      self.selected = (self.selected - 1) % len(self.options)
    elif event.key in (pygame.K_DOWN, pygame.K_s):
      self.selected = (self.selected + 1) % len(self.options)
    elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
      return ("return_to_menu", None)
    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
      choice = self.options[self.selected]
      if choice == "Host Game":
        return ("setup_host_game", None)
      if choice == "Join Game":
        return ("setup_join_game", None)
      if choice == "Back":
        return ("return_to_menu", None)

    return None

  def update(self, dt):
    pygame.display.set_caption("Asteroids - Multiplayer")
    return None

  def draw(self, surface):
    surface.fill("black")

    title = self.title_font.render("Multiplayer", True, "white")
    title_rect = title.get_rect(center=(surface.get_width() // 2, surface.get_height() // 5))
    surface.blit(title, title_rect)

    base_y = surface.get_height() // 2
    spacing = 60

    for index, option in enumerate(self.options):
      is_selected = index == self.selected
      color = "white" if is_selected else "gray"
      option_surface = self.option_font.render(option, True, color)
      option_rect = option_surface.get_rect(center=(surface.get_width() // 2, base_y + index * spacing))
      surface.blit(option_surface, option_rect)
