import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from telas.game_over import TelaGameOver
from telas.game_screen import TelaJogo
from telas.menu_screen import TelaMenu


def resolve_transition(transition):
  action, payload = transition

  if action == "quit":
    return None
  if action == "start_game":
    return TelaJogo()
  if action == "game_over":
    final_score = 0 if payload is None else payload.get("score", 0)
    return TelaGameOver(final_score)
  if action == "return_to_menu":
    return TelaMenu()

  raise ValueError(f"Unknown transition action: {action}")


def main():
  pygame.init()

  surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  clock = pygame.time.Clock()
  fps_limit = 60

  current_screen = TelaMenu()

  while True:
    screen_changed = False

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        return

      transition = current_screen.handle_event(event)
      if transition is not None:
        next_screen = resolve_transition(transition)
        if next_screen is None:
          return
        current_screen = next_screen
        screen_changed = True
        break

    dt = clock.tick(fps_limit) / 1000

    if screen_changed:
      continue

    transition = current_screen.update(dt)
    if transition is not None:
      next_screen = resolve_transition(transition)
      if next_screen is None:
        return
      current_screen = next_screen
      continue

    current_screen.draw(surface)
    pygame.display.flip()


if __name__ == "__main__":
  main()
