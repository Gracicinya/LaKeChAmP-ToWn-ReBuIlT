"""
road_crossing.py
================
Mini-game: Guide a resident safely across a broken road.
Left/Right to move, wait for gaps in traffic.
Returns True on crossing, False on Escape/quit.
"""

import pygame
import sys
import os
import random

SW, SH = 900, 600

C_SKY    = (100, 170, 220)
C_ROAD   = ( 50,  50,  55)
C_LINE   = (220, 200,  60)
C_GRASS  = ( 72, 130,  60)
C_PLAYER = (220, 140,  60)
C_CAR1   = (200,  60,  60)
C_CAR2   = ( 60, 120, 200)
C_CAR3   = ( 60, 180,  80)
C_WHITE  = (255, 255, 255)
C_CREAM  = (232, 217, 184)
C_DARK   = ( 30,  35,  40)
C_GREEN  = ( 72, 199, 142)
C_RED    = (220,  70,  70)

LANES = [
    {"y": 200, "dir":  1, "speed": 180, "color": C_CAR1},
    {"y": 280, "dir": -1, "speed": 220, "color": C_CAR2},
    {"y": 360, "dir":  1, "speed": 150, "color": C_CAR3},
    {"y": 440, "dir": -1, "speed": 200, "color": C_CAR1},
]
LANE_H     = 60
PLAYER_W   = 40
PLAYER_H   = 50
PLAYER_X   = SW // 2
START_Y    = SH - 60
GOAL_Y     = 80
CAR_W      = 90
CAR_H      = 44
LIVES      = 3


def _load_truck_images():
    asset_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "road crossing game - pickup truck")
    asset_dir = os.path.normpath(asset_dir)
    images = {"left": [], "right": []}

    if os.path.isdir(asset_dir):
        for filename in sorted(os.listdir(asset_dir)):
            if not filename.lower().endswith(".png"):
                continue
            path = os.path.join(asset_dir, filename)
            try:
                image = pygame.image.load(path).convert_alpha()
            except pygame.error:
                continue
            if "right_facing" in filename.lower():
                images["right"].append(image)
            else:
                images["left"].append(image)

    if not images["right"] and images["left"]:
        images["right"] = [pygame.transform.flip(img, True, False) for img in images["left"]]

    return images


def _make_cars(truck_images):
    cars = []
    for lane in LANES:
        for _ in range(3):
            if lane["dir"] == 1:
                x = random.randint(-SW, 0)
                images = truck_images.get("right", [])
            else:
                x = random.randint(SW, 2 * SW)
                images = truck_images.get("left", [])

            image = None
            if images:
                image = random.choice(images)
                image = pygame.transform.smoothscale(image, (CAR_W, CAR_H))

            cars.append({
                "x":     float(x),
                "y":     lane["y"],
                "dir":   lane["dir"],
                "speed": lane["speed"],
                "color": lane["color"],
                "image": image,
            })
    return cars


def run_crossing_game(screen=None, clock=None):
    # Main loop for the road crossing mini-game.
    standalone = screen is None
    if standalone:
        pygame.init()
        screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("Cross the Road")
        clock  = pygame.time.Clock()

    font_big   = pygame.font.SysFont("Georgia",     28, bold=True)
    font_med   = pygame.font.SysFont("Segoe UI",    18)
    font_small = pygame.font.SysFont("Courier New", 14)

    truck_images = _load_truck_images()

    def _reset():
        return {
            "px":    float(PLAYER_X),
            "py":    float(START_Y),
            "cars":  _make_cars(truck_images),
            "lives": LIVES,
            "won":   False,
            "dead":  False,
            "timer": 0,
        }

    state    = _reset()
    move_cooldown = 0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0   # seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if standalone:
                    pygame.quit(); sys.exit()
                return False
            elif event.type == pygame.KEYDOWN:
                if state["won"]:
                    if event.key in (pygame.K_RETURN, pygame.K_RIGHT):
                        return True
                if state["dead"] and state["lives"] <= 0:
                    if event.key in (pygame.K_RETURN, pygame.K_r):
                        state = _reset()
                        continue
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    state = _reset()

        if not state["won"] and not state["dead"]:
            keys = pygame.key.get_pressed()
            step = 60
            if move_cooldown <= 0:
                moved = False
                if keys[pygame.K_UP]    and state["py"] > GOAL_Y + PLAYER_H:
                    state["py"] -= step; moved = True
                if keys[pygame.K_DOWN]  and state["py"] < START_Y:
                    state["py"] += step; moved = True
                if keys[pygame.K_LEFT]  and state["px"] > PLAYER_W:
                    state["px"] -= step; moved = True
                if keys[pygame.K_RIGHT] and state["px"] < SW - PLAYER_W:
                    state["px"] += step; moved = True
                if moved:
                    move_cooldown = 0.15

            move_cooldown = max(0, move_cooldown - dt)

            # Move cars
            for car in state["cars"]:
                car["x"] += car["dir"] * car["speed"] * dt
                if car["dir"] == 1 and car["x"] > SW + CAR_W:
                    car["x"] = -CAR_W - random.randint(0, 300)
                elif car["dir"] == -1 and car["x"] < -CAR_W:
                    car["x"] = SW + CAR_W + random.randint(0, 300)

            # Collision
            player_rect = pygame.Rect(state["px"] - PLAYER_W // 2,
                                      state["py"] - PLAYER_H // 2,
                                      PLAYER_W, PLAYER_H)
            for car in state["cars"]:
                car_rect = pygame.Rect(car["x"] - CAR_W // 2,
                                       car["y"] - CAR_H // 2,
                                       CAR_W, CAR_H)
                if player_rect.colliderect(car_rect):
                    state["lives"] -= 1
                    state["dead"]   = True
                    state["timer"]  = 0
                    break

            # Win
            if state["py"] <= GOAL_Y + PLAYER_H:
                state["won"] = True

        elif state["dead"]:
            state["timer"] += dt
            if state["timer"] > 1.2 and state["lives"] > 0:
                state["dead"] = False
                state["px"]   = float(PLAYER_X)
                state["py"]   = float(START_Y)

        # ── Draw ──────────────────────────────────────────────────────────────
        # Sky / goal zone
        screen.fill(C_SKY, (0, 0, SW, GOAL_Y + LANE_H))
        # Goal grass
        pygame.draw.rect(screen, C_GRASS, (0, GOAL_Y - 10, SW, LANE_H))
        goal_txt = font_med.render("SAFETY", True, C_WHITE)
        screen.blit(goal_txt, (SW // 2 - goal_txt.get_width() // 2, GOAL_Y + 10))

        # Road
        road_top = LANES[0]["y"] - LANE_H // 2
        road_bot = LANES[-1]["y"] + LANE_H // 2
        pygame.draw.rect(screen, C_ROAD, (0, road_top, SW, road_bot - road_top))
        for lane in LANES:
            for x in range(0, SW, 60):
                pygame.draw.rect(screen, C_LINE, (x, lane["y"] + LANE_H // 2 - 2, 30, 4))

        # Start grass
        pygame.draw.rect(screen, C_GRASS, (0, road_bot, SW, SH - road_bot))
        start_txt = font_med.render("START", True, C_WHITE)
        screen.blit(start_txt, (SW // 2 - start_txt.get_width() // 2, road_bot + 10))

        # Cars
        for car in state["cars"]:
            if car["image"]:
                screen.blit(car["image"], (car["x"] - CAR_W // 2, car["y"] - CAR_H // 2))
            else:
                r = pygame.Rect(car["x"] - CAR_W // 2, car["y"] - CAR_H // 2, CAR_W, CAR_H)
                pygame.draw.rect(screen, car["color"], r, border_radius=6)
                pygame.draw.rect(screen, C_WHITE, r, 1, border_radius=6)

        # Player
        if not (state["dead"] and int(state["timer"] * 8) % 2 == 0):
            pr = pygame.Rect(state["px"] - PLAYER_W // 2,
                             state["py"] - PLAYER_H // 2,
                             PLAYER_W, PLAYER_H)
            pygame.draw.rect(screen, C_PLAYER, pr, border_radius=8)
            pygame.draw.rect(screen, C_WHITE, pr, 2, border_radius=8)

        # HUD
        hud = font_med.render(f"Lives: {'♥ ' * state['lives']}", True, C_RED)
        screen.blit(hud, (10, 10))
        ctrl = font_small.render("Arrow keys to move   R = restart   ESC = back", True, C_DARK)
        screen.blit(ctrl, (SW - ctrl.get_width() - 10, SH - 20))

        # Overlays
        if state["won"]:
            ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
            ov.fill((10, 25, 10, 160))
            screen.blit(ov, (0, 0))
            w1 = font_big.render("Made it across!", True, C_GREEN)
            w2 = font_med.render("Press ENTER or → to continue", True, C_CREAM)
            screen.blit(w1, w1.get_rect(center=(SW // 2, SH // 2 - 20)))
            screen.blit(w2, w2.get_rect(center=(SW // 2, SH // 2 + 24)))

        elif state["dead"] and state["lives"] <= 0:
            ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
            ov.fill((40, 10, 10, 180))
            screen.blit(ov, (0, 0))
            w1 = font_big.render("No lives left!", True, C_RED)
            w2 = font_med.render("Press R to try again   ESC = back", True, C_CREAM)
            screen.blit(w1, w1.get_rect(center=(SW // 2, SH // 2 - 20)))
            screen.blit(w2, w2.get_rect(center=(SW // 2, SH // 2 + 24)))

        pygame.display.flip()

    return False


if __name__ == "__main__":
    pygame.init()
    run_crossing_game()
    pygame.quit()
