import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from services.score_manager import load_scores


class TelaGameOver:

  def __init__(self, final_score):
    self.final_score = final_score

    self.title_font = pygame.font.SysFont("monospace", 72, bold=True)
    self.menu_font = pygame.font.SysFont("monospace", 42, bold=True)
    self.hud_font = pygame.font.SysFont("monospace", 36, bold=True)
    self.small_font = pygame.font.SysFont("monospace", 28, bold=True)

    self.top_scores = load_scores()[:3]

  def handle_event(self, event):
    if event.type != pygame.KEYDOWN:
      return None

    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
      return ("return_to_menu", None)

    return None

  def update(self, dt):
    pygame.display.set_caption("Asteroids by TuxyBR - Game Over")
    return None

  def draw(self, surface):
    surface.fill("black")

    title_text = self.title_font.render("GAME OVER", True, "white")
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    surface.blit(title_text, title_rect)

    score_surface = self.menu_font.render(f"Final Score: {self.final_score}", True, "gray")
    score_rect = score_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    surface.blit(score_surface, score_rect)

    prompt_surface = self.hud_font.render("Press Enter or Spacebar to return", True, "darkgray")
    prompt_rect = prompt_surface.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.8)))
    surface.blit(prompt_surface, prompt_rect)

    block_x = int(SCREEN_WIDTH * 0.75)
    header = self.hud_font.render("TOP 3", True, "white")
    header_rect = header.get_rect(center=(block_x, SCREEN_HEIGHT // 3))
    surface.blit(header, header_rect)

    spacing = 50
    for index, record in enumerate(self.top_scores, start=1):
      text = f"{index}. {record.name} - {record.score}"
      row = self.small_font.render(text, True, "gray")
      row_rect = row.get_rect(center=(block_x, SCREEN_HEIGHT // 3 + index * spacing))
      surface.blit(row, row_rect)
