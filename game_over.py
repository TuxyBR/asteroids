import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class TelaGameOver:

  def __init__(self, final_score):
    self.final_score = final_score

    self.title_font = pygame.font.SysFont("monospace", 72, bold=True)
    self.menu_font = pygame.font.SysFont("monospace", 42, bold=True)
    self.hud_font = pygame.font.SysFont("monospace", 36, bold=True)

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
