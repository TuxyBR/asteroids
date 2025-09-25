import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from services.score_manager import record_score


class NewScoreScreen:

  def __init__(self, score):
    self.score = score
    self.name = ""
    self.title_font = pygame.font.SysFont("monospace", 64, bold=True)
    self.text_font = pygame.font.SysFont("monospace", 42, bold=True)
    self.hint_font = pygame.font.SysFont("monospace", 28, bold=True)

  def handle_event(self, event):
    if event.type != pygame.KEYDOWN:
      return None

    if event.key == pygame.K_RETURN:
      record_score(self.score, self.name)
      return ("score_saved", {"score": self.score})

    if event.key == pygame.K_ESCAPE:
      return ("score_skipped", {"score": self.score})

    if event.key == pygame.K_BACKSPACE:
      self.name = self.name[:-1]
      return None

    if event.unicode and event.unicode.isprintable():
      character = event.unicode
      if character == "\r":
        return None
      self.name = (self.name + character)[:16]
    return None

  def update(self, dt):
    return None

  def draw(self, surface):
    surface.fill("black")

    title_surface = self.title_font.render("HIGH SCORE!", True, "white")
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    surface.blit(title_surface, title_rect)

    score_text = self.text_font.render(f"Score: {self.score}", True, "gray")
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
    surface.blit(score_text, score_rect)

    name_surface = self.text_font.render(self.name or "_", True, "white")
    name_rect = name_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    surface.blit(name_surface, name_rect)

    hint_surface = self.hint_font.render("Name yourself and press ENTER or press ESC to skip", True, "darkgray")
    hint_rect = hint_surface.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.75)))
    surface.blit(hint_surface, hint_rect)
