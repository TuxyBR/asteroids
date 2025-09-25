import sys
import os
import json
import uuid
import time
import pygame

from constants import *

from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot
from explosion import Explosion
from mqtt_sync import MQTTGameClient

def main():
  pygame.init()

  update_group = pygame.sprite.Group()
  draw_group = pygame.sprite.Group()
  asteroid_group = pygame.sprite.Group()
  shot_group = pygame.sprite.Group()

  Player.containers = (update_group, draw_group)
  Asteroid.containers = (asteroid_group, update_group, draw_group)
  AsteroidField.containers = (update_group)
  Shot.containers = (shot_group, update_group, draw_group)
  Explosion.containers = (update_group, draw_group)

  dt = 0
  score = 0
  fps_limit = 60
  clock = pygame.time.Clock()
  explosions = []
  # simple distinct colors palette
  COLORS = [
    (255, 255, 255),
    (255, 0, 0),
    (0, 255, 0),
    (0, 128, 255),
    (255, 128, 0),
    (255, 0, 255),
    (0, 255, 255),
    (255, 255, 0),
  ]

  screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

  # Multiplayer setup via MQTT (minimal)
  player_id = os.getenv("PLAYER_ID") or uuid.uuid4().hex[:8]
  mqtt_client = MQTTGameClient(player_id, on_event=None)
  mqtt_ok = mqtt_client.connect()

  # Collect existing colors from retained join messages (briefly)
  used_color_idx = set()
  join_events_buffer = []
  start_wait = time.monotonic()
  if mqtt_ok:
    while time.monotonic() - start_wait < 0.6:
      ev = mqtt_client.get_event(timeout=0.1)
      if not ev:
        continue
      if ev.get("type") == "player" and ev.get("action") == "join":
        color = ev.get("color")
        if isinstance(color, list) and len(color) == 3 and tuple(color) in COLORS:
          used_color_idx.add(COLORS.index(tuple(color)))
        join_events_buffer.append(ev)
      elif ev.get("type") == "host":
        pass
      else:
        # stash for later processing in main loop
        join_events_buffer.append(ev)

  # choose a color not used
  def pick_color():
    for i, c in enumerate(COLORS):
      if i not in used_color_idx:
        return c
    return COLORS[0]

  local_color = pick_color()
  if mqtt_ok:
    mqtt_client.publish_join(list(local_color))

  players = {}
  def make_player(pid, color, is_local):
    return Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, color=color, is_local=is_local, player_id=pid)

  local_player = make_player(player_id, local_color, True)
  players[player_id] = local_player
  players_alive = {player_id: True}

  # install shoot handler to sync via MQTT; host will spawn shots locally
  def on_shoot(p: Player):
    if mqtt_ok:
      if mqtt_client.is_host():
        shot = Shot(p.position[0], p.position[1], host_controlled=True)
        shot.velocity = pygame.Vector2(0, 1).rotate(p.rotation) * PLAYER_SHOT_SPEED
        shot_owner[shot.shot_id] = p.player_id
        return True
      else:
        mqtt_client.publish_shoot(p.position[0], p.position[1], p.rotation)
        return True
    return False
  local_player._on_shoot = on_shoot

  asteroid_field = AsteroidField()
  font = pygame.font.SysFont("monospace", 36, bold=True)

  # track world objects by id for syncing (non-host)
  asteroid_by_id = {}
  shot_by_id = {}
  shot_owner = {}

  # process buffered join events (create remote players)
  for ev in join_events_buffer:
    if ev.get("type") == "player" and ev.get("action") == "join":
      pid = ev.get("player_id")
      if pid and pid != player_id and pid not in players:
        color = tuple(ev.get("color") or (255, 255, 255))
        players[pid] = make_player(pid, color, False)
        players_alive[pid] = True

  while True:
    pygame.display.set_caption(f"Asteroids by TuxyBR - Score: {score}")
    score_text = font.render(f"Score: {score}", True, "gray")
    text_rect = score_text.get_rect()
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        return
      if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
        if not local_player.alive:
          # respawn at center with same color
          color = local_player.color
          new_p = make_player(player_id, color, True)
          # restore local shoot handler after respawn
          new_p._on_shoot = on_shoot
          players[player_id] = new_p
          local_player = new_p
          players_alive[player_id] = True
          if mqtt_ok:
            mqtt_client.publish_player_respawn(player_id, new_p.position.x, new_p.position.y, new_p.rotation)

    screen.fill("black")
    update_group.update(dt)

    # MQTT event handling
    if mqtt_ok:
      mqtt_client.maybe_claim_host()
      # host runs asteroid spawns only if at least one player alive
      asteroid_field.enabled = mqtt_client.is_host() and any(players_alive.values())
      while True:
        ev = mqtt_client.get_event(timeout=0.0)
        if not ev:
          break
        et = ev.get("type")
        if et == "player":
          action = ev.get("action")
          pid = ev.get("player_id")
          if pid == player_id:
            continue
          if action == "join":
            if pid not in players:
              color = tuple(ev.get("color") or (255, 255, 255))
              players[pid] = make_player(pid, color, False)
              players_alive[pid] = True
          elif action == "state":
            pl = players.get(pid)
            if pl:
              pl.position.update(float(ev.get("x", pl.position.x)), float(ev.get("y", pl.position.y)))
              pl.rotation = float(ev.get("rot", pl.rotation))
          elif action == "shoot":
            # host spawns shots on shoot events
            if mqtt_client.is_host():
              x, y = float(ev.get("x", 0)), float(ev.get("y", 0))
              rot = float(ev.get("rot", 0))
              s = Shot(x, y, host_controlled=True)
              s.velocity = pygame.Vector2(0, 1).rotate(rot) * PLAYER_SHOT_SPEED
              shot_owner[s.shot_id] = pid
        elif et == "world_state":
          # non-host: sync world
          if not mqtt_client.is_host():
            # asteroids
            incoming = ev.get("asteroids", [])
            seen_ids = set()
            for a in incoming:
              aid = int(a.get("id"))
              seen_ids.add(aid)
              ax, ay = float(a.get("x", 0)), float(a.get("y", 0))
              avx, avy = float(a.get("vx", 0)), float(a.get("vy", 0))
              ar = float(a.get("radius", ASTEROID_MIN_RADIUS))
              if aid not in asteroid_by_id:
                ast = Asteroid(ax, ay, ar, asteroid_id=aid, host_controlled=False)
                asteroid_by_id[aid] = ast
              ast = asteroid_by_id[aid]
              ast.position.update(ax, ay)
              ast.velocity.update(avx, avy)
            # remove missing
            for aid in list(asteroid_by_id.keys()):
              if aid not in seen_ids:
                asteroid_by_id[aid].kill()
                del asteroid_by_id[aid]

            # shots
            incoming_s = ev.get("shots", [])
            seen_s = set()
            for s in incoming_s:
              sid = int(s.get("id"))
              seen_s.add(sid)
              sx, sy = float(s.get("x", 0)), float(s.get("y", 0))
              svx, svy = float(s.get("vx", 0)), float(s.get("vy", 0))
              if sid not in shot_by_id:
                sh = Shot(sx, sy, shot_id=sid, host_controlled=False)
                shot_by_id[sid] = sh
              sh = shot_by_id[sid]
              sh.position.update(sx, sy)
              sh.velocity.update(svx, svy)
            for sid in list(shot_by_id.keys()):
              if sid not in seen_s:
                shot_by_id[sid].kill()
                del shot_by_id[sid]
        elif et == "explosion":
          explosions.append(Explosion(pygame.Vector2(float(ev.get("x", 0)), float(ev.get("y", 0)))))
        elif et == "score":
          if ev.get("player_id") == player_id:
            score += int(ev.get("delta", 0))
        elif et == "player_dead":
          pid = ev.get("player_id")
          if pid in players:
            players_alive[pid] = False
            # ensure the sprite is removed locally
            try:
              players[pid].die()
            except Exception:
              pass
        elif et == "player_respawn":
          pid = ev.get("player_id")
          if pid:
            players_alive[pid] = True
            color = getattr(players.get(pid), 'color', (255,255,255))
            # replace player sprite with a fresh one
            is_local = (pid == player_id)
            new_p = make_player(pid, color, is_local)
            new_p.position.update(float(ev.get("x", SCREEN_WIDTH/2)), float(ev.get("y", SCREEN_HEIGHT/2)))
            new_p.rotation = float(ev.get("rot", 0))
            players[pid] = new_p
            if is_local:
              # restore local shoot handler
              new_p._on_shoot = on_shoot
              local_player = new_p

    # helper: clear the world if all known players are dead
    def all_players_dead():
      return players_alive and all(not alive for alive in players_alive.values())

    def clear_world():
      for a in list(asteroid_group):
        a.kill()
      for s in list(shot_group):
        s.kill()
      explosions.clear()
      asteroid_field.enabled = False

    for asteroid in asteroid_group:
      # Local player collision: mark dead and continue running
      if local_player.alive and asteroid.colision(local_player):
        local_player.die()
        players_alive[player_id] = False
        if mqtt_ok:
          mqtt_client.publish_player_dead(player_id)
      for shot in list(shot_group):
        if asteroid.colision(shot):
          gained = asteroid.split()
          # host announces explosions and scores
          if mqtt_ok and mqtt_client.is_host():
            mqtt_client.publish_explosion(asteroid.position.x, asteroid.position.y)
            owner = shot_owner.get(getattr(shot, "shot_id", None), player_id)
            mqtt_client.publish_score(owner, gained)
            if owner == player_id:
              score += gained
          else:
            # local mode
            score += gained
          explosions.append(Explosion(asteroid.position))
          sid = getattr(shot, "shot_id", None)
          if sid in shot_owner:
            del shot_owner[sid]
          shot.kill()

    # If everyone is dead, clear the world
    if all_players_dead():
      clear_world()

    effect = []
    for explosion in explosions:
        if not explosion.is_dead():
            effect.append(explosion)
    explosions[:] = effect

    for drawable in draw_group:
      drawable.draw(screen)
    screen.blit(score_text, (30, SCREEN_HEIGHT - text_rect.height - 15))

    # host: simulate asteroids + publish world state periodically
    if mqtt_ok and mqtt_client.is_host():
      # publish world (asteroids + shots)
      ast_list = [
        {"id": a.asteroid_id, "x": a.position.x, "y": a.position.y, "vx": a.velocity.x, "vy": a.velocity.y, "radius": a.radius}
        for a in asteroid_group
      ]
      shot_list = [
        {"id": s.shot_id, "x": s.position.x, "y": s.position.y, "vx": s.velocity.x, "vy": s.velocity.y}
        for s in shot_group
      ]
      mqtt_client.publish_world_state({"asteroids": ast_list, "shots": shot_list})

    # publish local state for others/host (capped at 120 Hz in MQTT client)
    if mqtt_ok and local_player.alive:
      mqtt_client.publish_player_state(local_player.position.x, local_player.position.y, local_player.rotation)

    # respawn is handled via KEYDOWN event above

    dt = clock.tick(fps_limit) / 1000
    pygame.display.flip()


if __name__ == "__main__":
  main()
