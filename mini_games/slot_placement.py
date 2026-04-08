"""
slot_placement.py
=================
Mini-game: Drag residents back to their correct home slots.
A simple drag-and-drop "everyone goes home" puzzle.
Returns True on completion, False on Escape/quit.
"""

import pygame
import sys
import os
import random

SW, SH = 900, 600

# Colours
BG      = ( 60,  90,  60)
WHITE   = (255, 255, 255)
CREAM   = (232, 217, 184)
GREY    = (160, 165, 170)
GREEN   = ( 72, 199, 142)
YELLOW  = (255, 210,  80)
DARK    = ( 30,  35,  30)

RESIDENT_DATA = [
    {"name": "Ada",   "color": (200,  80,  80), "home": 0},
    {"name": "Ben",   "color": ( 80, 160, 200), "home": 1},
    {"name": "Cora",  "color": (200, 140,  60), "home": 2},
    {"name": "Dex",   "color": (140,  80, 200), "home": 3},
]

SLOT_SIZE  = 90
PIECE_SIZE = 70
PIECES_Y   = SH // 2 + 100


def _load_background_image():
    asset_path = os.path.normpath(os.path.join(
        os.path.dirname(__file__),
        "..", "assets", "slot placement game - apartment building", "728.jpg"
    ))
    if os.path.exists(asset_path):
        try:
            image = pygame.image.load(asset_path).convert()
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, (SW, SH))
    return None


def _slot_positions():
    cols = 2
    rows = 2
    marginX = 130 # how much horizontal space is between slots
    marginY = 80 # how much vertical space is between slots
    X_OFFSET = 230 # how much to shift the whole grid left/right (positive = right) to better fit the background image
    Y_OFFSET = 115
    grid_width = cols * SLOT_SIZE + (cols - 1) * marginX
    grid_height = rows * SLOT_SIZE + (rows - 1) * marginY
    start_x = SW // 2 - grid_width // 2 + X_OFFSET
    start_y = SH // 2 - grid_height // 2 - Y_OFFSET
    positions = []
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * (SLOT_SIZE + marginX)
            y = start_y + row * (SLOT_SIZE + marginY)
            positions.append((x, y))
    return positions

def _piece_start_positions(order):
    total = len(order) * PIECE_SIZE + (len(order) - 1) * 30
    sx    = SW // 2 - total // 2
    return [(sx + i * (PIECE_SIZE + 30), PIECES_Y) for i in range(len(order))]


def run_placement_game(screen=None, clock=None):
    standalone = screen is None
    if standalone:
        pygame.init()
        screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("Residents Go Home")
        clock  = pygame.time.Clock()

    font_big   = pygame.font.SysFont("Georgia",     26, bold=True)
    font_med   = pygame.font.SysFont("Segoe UI",    18)
    font_small = pygame.font.SysFont("Courier New", 14)
    background = _load_background_image()

    def _reset():
        order = list(range(len(RESIDENT_DATA)))
        random.shuffle(order)
        starts = _piece_start_positions(order)
        pieces = []
        for pos_i, res_i in enumerate(order):
            d = RESIDENT_DATA[res_i]
            pieces.append({
                "res_i":  res_i,
                "color":  d["color"],
                "name":   d["name"],
                "home":   d["home"],
                "rect":   pygame.Rect(starts[pos_i][0], starts[pos_i][1], PIECE_SIZE, PIECE_SIZE),
                "placed": False,
            })
        return pieces

    slot_pos  = _slot_positions()
    pieces    = _reset()
    held      = None
    drag_off  = (0, 0)
    complete  = False
    win_timer = 0

    running = True
    while running:
        ms = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if standalone:
                    pygame.quit(); sys.exit()
                return False

            elif event.type == pygame.KEYDOWN:
                if complete and event.key in (pygame.K_RETURN, pygame.K_RIGHT):
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    pieces   = _reset()
                    held     = None
                    complete = False
                    win_timer= 0

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if complete:
                    return True
                mx, my = event.pos
                for p in reversed(pieces):
                    if not p["placed"] and p["rect"].collidepoint(mx, my):
                        held     = p
                        drag_off = (mx - p["rect"].x, my - p["rect"].y)
                        break

            elif event.type == pygame.MOUSEMOTION and held:
                mx, my = event.pos
                held["rect"].x = mx - drag_off[0]
                held["rect"].y = my - drag_off[1]

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and held:
                mx, my = event.pos
                for slot_i, (sx, sy) in enumerate(slot_pos):
                    slot_rect = pygame.Rect(sx, sy, SLOT_SIZE, SLOT_SIZE)
                    if slot_rect.collidepoint(mx, my):
                        # Check if slot is already occupied
                        occupied = any(p["placed"] and p["home"] == slot_i for p in pieces)
                        if not occupied and held["home"] == slot_i:
                            held["placed"] = True
                            held["rect"]   = pygame.Rect(
                                sx + (SLOT_SIZE - PIECE_SIZE) // 2,
                                sy + (SLOT_SIZE - PIECE_SIZE) // 2,
                                PIECE_SIZE, PIECE_SIZE)
                        break
                held = None
                if all(p["placed"] for p in pieces):
                    complete  = True
                    win_timer = 0

        if complete:
            win_timer += ms

        # ── Draw ──────────────────────────────────────────────────────────────
        if background is not None:
            screen.blit(background, (0, 0))
            fade = pygame.Surface((SW, SH), pygame.SRCALPHA)
            fade.fill((10, 20, 10, 120))
            screen.blit(fade, (0, 0))
        else:
            screen.fill(BG)

        # Title
        title = font_big.render("Guide the Residents Home", True, CREAM)
        screen.blit(title, (SW // 2 - title.get_width() // 2, 30))
        sub = font_med.render("Drag each resident to their matching home slot.", True, GREY)
        screen.blit(sub, (SW // 2 - sub.get_width() // 2, 68))

        # Slots
        for slot_i, (sx, sy) in enumerate(slot_pos):
            d   = RESIDENT_DATA[slot_i]
            col = tuple(max(0, c - 80) for c in d["color"])
            pygame.draw.rect(screen, col,  (sx, sy, SLOT_SIZE, SLOT_SIZE), border_radius=8)
            pygame.draw.rect(screen, GREY, (sx, sy, SLOT_SIZE, SLOT_SIZE), 2, border_radius=8)
            lbl = font_small.render(d["name"], True, GREY)
            screen.blit(lbl, (sx + SLOT_SIZE // 2 - lbl.get_width() // 2, sy + SLOT_SIZE + 4))

        # Pieces (placed first, then unplaced, then held on top)
        for p in pieces:
            if p is held:
                continue
            col = p["color"]
            pygame.draw.rect(screen, col, p["rect"], border_radius=6)
            bdr = GREEN if p["placed"] else WHITE
            pygame.draw.rect(screen, bdr, p["rect"], 2, border_radius=6)
            n = font_small.render(p["name"], True, WHITE)
            screen.blit(n, (p["rect"].centerx - n.get_width() // 2,
                            p["rect"].centery - n.get_height() // 2))

        if held:
            pygame.draw.rect(screen, held["color"], held["rect"], border_radius=6)
            pygame.draw.rect(screen, YELLOW, held["rect"], 3, border_radius=6)
            n = font_small.render(held["name"], True, WHITE)
            screen.blit(n, (held["rect"].centerx - n.get_width() // 2,
                            held["rect"].centery - n.get_height() // 2))

        # Hint
        hint = font_small.render("R = restart   ESC = back", True, DARK)
        screen.blit(hint, (SW - hint.get_width() - 10, SH - 20))

        # Win overlay
        if complete:
            ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
            ov.fill((10, 25, 10, min(180, win_timer // 3)))
            screen.blit(ov, (0, 0))
            if win_timer > 300:
                w1 = font_big.render("Everyone is home!", True, GREEN)
                w2 = font_med.render("Press ENTER or → to continue", True, CREAM)
                screen.blit(w1, w1.get_rect(center=(SW // 2, SH // 2 - 20)))
                screen.blit(w2, w2.get_rect(center=(SW // 2, SH // 2 + 24)))

        pygame.display.flip()

    return False


if __name__ == "__main__":
    pygame.init()
    run_placement_game()
    pygame.quit()
