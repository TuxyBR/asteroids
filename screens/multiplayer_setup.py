import string
import uuid

import pygame

from constants import MULTIPLAYER_DEFAULT_BROKER, MULTIPLAYER_DEFAULT_PORT
from services.multiplayer import MultiplayerConfig


PRINTABLE = set(string.printable) - {"\x0b", "\x0c", "\r"}


class _BaseMultiplayerSetupScreen:

  cancel_transition = ("show_multiplayer_menu", None)

  def __init__(self, title, field_specs):
    self.title = title
    self.fields = []
    for spec in field_specs:
      name, label, default, char_filter = spec
      self.fields.append({
        "name": name,
        "label": label,
        "value": default,
        "filter": char_filter,
      })

    self.selected_index = 0
    self.error_message = None

    self.title_font = pygame.font.SysFont("monospace", 54, bold=True)
    self.field_font = pygame.font.SysFont("monospace", 32, bold=True)
    self.info_font = pygame.font.SysFont("monospace", 24, bold=True)

  def handle_event(self, event):
    if event.type != pygame.KEYDOWN:
      return None

    if event.key in (pygame.K_UP):
      self.selected_index = (self.selected_index - 1) % len(self.fields)
      return None

    if event.key in (pygame.K_DOWN):
      self.selected_index = (self.selected_index + 1) % len(self.fields)
      return None

    if event.key == pygame.K_TAB:
      self.selected_index = (self.selected_index + 1) % len(self.fields)
      return None

    if event.key == pygame.K_ESCAPE:
      return self.cancel_transition

    field = self.fields[self.selected_index]

    if event.key == pygame.K_BACKSPACE:
      field["value"] = field["value"][:-1]
      return None

    if event.key == pygame.K_RETURN:
      return self._attempt_submit()

    char = event.unicode
    if not char or char not in PRINTABLE:
      return None

    char_filter = field.get("filter")
    if char_filter and not char_filter(char):
      return None

    field["value"] += char
    return None

  def _attempt_submit(self):
    values = {field["name"]: field["value"].strip() for field in self.fields}
    try:
      config, payload = self._build_payload(values)
    except ValueError as exc:
      self.error_message = str(exc)
      return None

    self.error_message = None
    data = {"config": config}
    data.update(payload or {})
    return (self.submit_action, data)

  def _build_payload(self, values):
    raise NotImplementedError

  def update(self, dt):
    pygame.display.set_caption(f"Asteroids - {self.title}")
    return None

  def draw(self, surface):
    surface.fill("black")

    title_surface = self.title_font.render(self.title, True, "white")
    title_rect = title_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 5))
    surface.blit(title_surface, title_rect)

    base_y = surface.get_height() // 2 - 60
    spacing = 56

    for index, field in enumerate(self.fields):
      is_selected = index == self.selected_index
      prefix = "> " if is_selected else "  "
      label = field["label"]
      value = field["value"] if field["value"] else "<empty>"
      text = f"{prefix}{label}: {value}"
      color = "white" if is_selected else "gray"
      field_surface = self.field_font.render(text, True, color)
      rect = field_surface.get_rect(center=(surface.get_width() // 2, base_y + index * spacing))
      surface.blit(field_surface, rect)

    info_text = "Use arrow keys to move, type to edit, ENTER to continue, ESC to go back"
    info_surface = self.info_font.render(info_text, True, "dimgray")
    info_rect = info_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() - 80))
    surface.blit(info_surface, info_rect)

    if self.error_message:
      error_surface = self.info_font.render(self.error_message, True, "red")
      error_rect = error_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() - 40))
      surface.blit(error_surface, error_rect)


def _port_filter(char: str) -> bool:
  return char.isdigit()


def _session_filter(char: str) -> bool:
  return char.isalnum() or char in {"-", "_"}


class MultiplayerHostSetupScreen(_BaseMultiplayerSetupScreen):

  submit_action = "start_host_game"

  def __init__(self):
    session_default = uuid.uuid4().hex[:8]
    fields = [
      ("broker", "Broker Host", MULTIPLAYER_DEFAULT_BROKER, None),
      ("port", "Broker Port", str(MULTIPLAYER_DEFAULT_PORT), _port_filter),
      ("session_id", "Session Code", session_default, _session_filter),
    ]
    super().__init__("Host Setup", fields)

  def _build_payload(self, values):
    broker = values["broker"] or MULTIPLAYER_DEFAULT_BROKER
    port_text = values["port"] or str(MULTIPLAYER_DEFAULT_PORT)

    if not port_text.isdigit():
      raise ValueError("Port must be a number")
    port = int(port_text)

    session_id = values["session_id"] or uuid.uuid4().hex[:8]

    config = MultiplayerConfig(broker=broker, port=port, session_id=session_id)
    return config, {}


class MultiplayerJoinSetupScreen(_BaseMultiplayerSetupScreen):

  submit_action = "start_client_game"

  def __init__(self):
    fields = [
      ("broker", "Broker Host", MULTIPLAYER_DEFAULT_BROKER, None),
      ("port", "Broker Port", str(MULTIPLAYER_DEFAULT_PORT), _port_filter),
      ("session_id", "Session Code", "", _session_filter),
    ]
    super().__init__("Join Game", fields)

  def _build_payload(self, values):
    broker = values["broker"] or MULTIPLAYER_DEFAULT_BROKER
    port_text = values["port"] or str(MULTIPLAYER_DEFAULT_PORT)
    session_id = values["session_id"].strip()

    if not port_text.isdigit():
      raise ValueError("Port must be a number")
    if not session_id:
      raise ValueError("Session code is required")

    port = int(port_text)
    config = MultiplayerConfig(broker=broker, port=port, session_id=session_id)
    return config, {}
