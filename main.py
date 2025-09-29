import pygame

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from screens.game_over_screen import GameOverScreen
from screens.game_screen import GameScreen
from screens.menu_screen import MenuScreen
from screens.multiplayer_client_game_screen import MultiplayerClientGameScreen
from screens.multiplayer_host_game_screen import MultiplayerHostGameScreen
from screens.multiplayer_menu_screen import MultiplayerMenuScreen
from screens.multiplayer_setup import MultiplayerHostSetupScreen, MultiplayerJoinSetupScreen
from screens.scoreboard_screen import ScoreboardScreen
from screens.score_entry_screen import ScoreEntryScreen
from services.score_manager import should_record


def switch_screen(transition):
  action, payload = transition

  if action == "quit":
    return None
  if action == "start_game":
    return GameScreen()
  if action == "game_over":
    final_score = 0 if payload is None else payload.get("score", 0)
    if final_score > 0 and should_record(final_score):
      return ScoreEntryScreen(final_score)
    return GameOverScreen(final_score)
  if action in ("score_saved", "score_skipped"):
    final_score = 0 if payload is None else payload.get("score", 0)
    return GameOverScreen(final_score)
  if action == "return_to_menu":
    return MenuScreen()
  if action == "show_scores":
    return ScoreboardScreen()
  if action == "show_multiplayer_menu":
    return MultiplayerMenuScreen()
  if action == "setup_host_game":
    return MultiplayerHostSetupScreen()
  if action == "setup_join_game":
    return MultiplayerJoinSetupScreen()
  if action == "start_host_game":
    config = None if payload is None else payload.get("config")
    if config is None:
      raise ValueError("Missing multiplayer config for host game")
    return MultiplayerHostGameScreen(config)
  if action == "start_client_game":
    config = None if payload is None else payload.get("config")
    if config is None:
      raise ValueError("Missing multiplayer config for client game")
    return MultiplayerClientGameScreen(config)

  raise ValueError(f"Unknown transition action: {action}")


def main():
  pygame.init()

  surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
  clock = pygame.time.Clock()
  fps_limit = 60

  current_screen = MenuScreen()

  while True:
    screen_changed = False

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        return

      transition = current_screen.handle_event(event)
      if transition is not None:
        next_screen = switch_screen(transition)
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
      next_screen = switch_screen(transition)
      if next_screen is None:
        return
      current_screen = next_screen
      continue

    current_screen.draw(surface)
    pygame.display.flip()


if __name__ == "__main__":
  main()
