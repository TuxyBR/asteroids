import pygame

from entities.player_input import PlayerInputState
from screens.game_screen import GameScreen
from services.multiplayer import MultiplayerHostSession


class MultiplayerHostGameScreen(GameScreen):

  def __init__(self, config):
    self.config = config
    self.session = None
    self._session_closed = True
    super().__init__()
    self.uses_local_keyboard = False
    self.allow_respawns = True
    self.session = MultiplayerHostSession(config, self)
    self.session.start()
    self._session_closed = False

    self.local_player_id = self.player.player_id
    self.session_font = pygame.font.SysFont("monospace", 24, bold=True)

  def _ensure_session_stopped(self):
    if self._session_closed or self.session is None:
      return
    self.session.stop()
    self._session_closed = True

  def handle_event(self, event):
    transition = super().handle_event(event)
    if transition is not None and transition[0] == "return_to_menu":
      if self.session is not None:
        self.session.broadcast_game_over(self.score)
      self._ensure_session_stopped()
    return transition

  def update(self, dt):
    self.session.process_pending()
    local_input = PlayerInputState.from_keyboard()
    self.set_player_input(self.local_player_id, local_input)

    transition = super().update(dt)

    self.session.broadcast_state()

    if transition is not None and transition[0] == "game_over":
      score_payload = transition[1] or {}
      score = score_payload.get("score", 0)
      self.session.broadcast_game_over(score)
      self._ensure_session_stopped()

    return transition

  def draw(self, surface):
    super().draw(surface)

    overlay_lines = [
      f"Session {self.config.session_id}",
      f"Players: {self.session.remote_player_count() + 1}",
    ]

    respawn_status = self.get_respawn_status()
    for player_id, message in respawn_status:
      overlay_lines.append(f"{player_id[:6]}: {message}")

    width = surface.get_width()
    for index, text in enumerate(overlay_lines):
      label = self.session_font.render(text, True, "gray")
      surface.blit(label, (width - label.get_width() - 20, 20 + index * 26))

  def __del__(self):
    if hasattr(self, "session"):
      self._ensure_session_stopped()
