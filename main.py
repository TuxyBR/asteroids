import pygame

from constants import LARGURA_TELA, ALTURA_TELA
from telas.tela_fim import TelaGameOver
from telas.tela_jogo import TelaJogo
from telas.tela_menu import TelaMenu


def troca_tela(transition):
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

  surface = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
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
        next_screen = troca_tela(transition)
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
      next_screen = troca_tela(transition)
      if next_screen is None:
        return
      current_screen = next_screen
      continue

    current_screen.draw(surface)
    pygame.display.flip()


if __name__ == "__main__":
  main()
