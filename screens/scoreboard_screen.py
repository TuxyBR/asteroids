import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from services.score_manager import load_scores


class ScoreboardScreen:

  def __init__(self):
    self.title_font = pygame.font.SysFont("monospace", 72, bold=True)
    self.row_font = pygame.font.SysFont("monospace", 42, bold=True)
    self.hint_font = pygame.font.SysFont("monospace", 28, bold=True)

    self.records = load_scores()
    self.visible_count = 7
    self.scroll_offset = 0

  def handle_event(self, event):
    if event.type != pygame.KEYDOWN:
      return None

    if len(self.records) > self.visible_count:
      if event.key in (pygame.K_UP, pygame.K_w):
        self.scroll_offset = max(0, self.scroll_offset - 1)
        return None
      if event.key in (pygame.K_DOWN, pygame.K_s):
        max_offset = max(0, len(self.records) - self.visible_count)
        self.scroll_offset = min(max_offset, self.scroll_offset + 1)
        return None
      if event.key == pygame.K_PAGEUP:
        self.scroll_offset = max(0, self.scroll_offset - self.visible_count)
        return None
      if event.key == pygame.K_PAGEDOWN:
        max_offset = max(0, len(self.records) - self.visible_count)
        self.scroll_offset = min(max_offset, self.scroll_offset + self.visible_count)
        return None

    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
      return ("return_to_menu", None)

    return None

  def update(self, dt):
    pygame.display.set_caption("Asteroids by TuxyBR - Scores")
    return None

  def draw(self, surface):
    surface.fill("black")

    title_surface = self.title_font.render("SCORES", True, "white")
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 5))
    surface.blit(title_surface, title_rect)

    if not self.records:
      empty_surface = self.row_font.render("No Scores Set", True, "gray")
      empty_rect = empty_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
      surface.blit(empty_surface, empty_rect)
    else:
      start_y = SCREEN_HEIGHT // 3
      spacing = 50
      visible_records = self.records[self.scroll_offset:self.scroll_offset + self.visible_count]
      for index, record in enumerate(visible_records, start=1 + self.scroll_offset):
        row_text = f"{index:02d}. {record.name} - {record.score}"
        if record.timestamp:
          row_text += f" — {record.timestamp}"
        row_surface = self.row_font.render(row_text, True, "gray")
        row_rect = row_surface.get_rect(
          center=(SCREEN_WIDTH // 2, start_y + (index - (self.scroll_offset + 1)) * spacing)
        )
        surface.blit(row_surface, row_rect)

    hint_text = "Press Enter/Esc to return"
    if len(self.records) > self.visible_count:
      hint_text += " • Use arrows/Page keys to scroll"
    hint_surface = self.hint_font.render(hint_text, True, "darkgray")
    hint_rect = hint_surface.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.85)))
    surface.blit(hint_surface, hint_rect)
