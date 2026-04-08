"""
guess_pin.py
============
Mini-game: Guess the 4-digit PIN to lower the drawbridge.
Returns True when the player wins, False if they quit (Escape).

Controls:
    0-9       type digits
    Backspace  delete last digit
    Enter      submit guess
    Escape     quit / return to story
"""

import pygame
import random

# ── Palette (warm / weathered) ────────────────────────────────────────────────
C_RUST        = (139,  58,  26)
C_RUST_LIGHT  = (196,  88,  42)
C_RUST_DARK   = ( 74,  26,   8)
C_WOOD        = (107,  66,  38)
C_WOOD_LIGHT  = (160,  98,  58)
C_WOOD_DARK   = ( 59,  34,  18)
C_STONE       = (122, 112,  96)
C_STONE_LIGHT = (176, 168, 152)
C_PARCHMENT   = (232, 217, 184)
C_PARCHMENT_D = (196, 169, 110)
C_INK         = ( 44,  26,  14)
C_MOSS        = ( 74, 103,  65)
C_WATER       = ( 42,  74, 106)
C_SKY         = (100, 140, 175)
C_HIGHER      = (212, 138,  42)
C_LOWER       = ( 74, 138, 196)

SW, SH   = 900, 600
SCENE_H  = 220
PANEL_Y  = SCENE_H
CELL_W   = 60
CELL_H   = 72


def _draw_scene(surf, bridge_angle, chain_pct):
    """Draw the bridge/moat scene. bridge_angle 0=flat, 1=fully raised."""
    surf.fill(C_SKY, (0, 0, SW, SCENE_H))

    # Water
    pygame.draw.rect(surf, C_WATER, (0, SCENE_H - 55, SW, 55))
    for i in range(0, SW, 36):
        pygame.draw.line(surf, (60, 110, 150), (i, SCENE_H - 42), (i + 18, SCENE_H - 42), 2)

    # Cliffs
    pygame.draw.polygon(surf, C_STONE,
        [(0, SCENE_H - 55), (90, SCENE_H - 55 - 60), (90, SCENE_H), (0, SCENE_H)])
    pygame.draw.polygon(surf, C_STONE,
        [(SW, SCENE_H - 55), (SW - 90, SCENE_H - 55 - 60), (SW - 90, SCENE_H), (SW, SCENE_H)])

    # Towers
    for tx in (62, SW - 90):
        pygame.draw.rect(surf, C_STONE, (tx, SCENE_H - 55 - 72, 28, 72))
        pygame.draw.rect(surf, C_STONE_LIGHT, (tx, SCENE_H - 55 - 72, 28, 72), 2)
        for m in range(3):
            mx = tx + 2 + m * 9
            pygame.draw.rect(surf, C_STONE_LIGHT, (mx, SCENE_H - 55 - 72 - 12, 7, 12))

    # Chains
    chain_top_y = SCENE_H - 55 - 72 + 8
    chain_bot_y = int(chain_top_y + 48 * chain_pct)
    for cx in (76, SW - 76):
        for y in range(chain_top_y, chain_bot_y, 10):
            seg_col = C_RUST if (y // 10) % 2 == 0 else C_RUST_DARK
            pygame.draw.rect(surf, seg_col, (cx - 1, y, 3, 8))

    # Bridge (pivots from left tower, rotates up)
    bridge_w = SW - 90 - 90
    bridge_h = 22
    bridge_x = 90
    bridge_y = SCENE_H - 55 - bridge_h

    bridge_surf = pygame.Surface((bridge_w, bridge_h), pygame.SRCALPHA)
    for px in range(0, bridge_w, 22):
        col = C_WOOD if (px // 22) % 2 == 0 else C_WOOD_DARK
        pygame.draw.rect(bridge_surf, col, (px, 0, 22, bridge_h))
    pygame.draw.rect(bridge_surf, C_WOOD_LIGHT, (0, 0, bridge_w, 3))

    angle_deg = bridge_angle * 65
    rotated   = pygame.transform.rotate(bridge_surf, -angle_deg)
    surf.blit(rotated, (bridge_x, bridge_y + bridge_h - rotated.get_height()))

    # Padlock
    if bridge_angle > 0.05:
        cx, cy = SW // 2, SCENE_H // 2 - 10
        pygame.draw.arc(surf, C_RUST, (cx - 11, cy - 14, 22, 18), 0, 3.14159, 3)
        pygame.draw.rect(surf, C_RUST, (cx - 14, cy, 28, 20), border_radius=3)
        pygame.draw.rect(surf, C_RUST_DARK, (cx - 3, cy + 6, 6, 10), border_radius=3)


def _numpad_layout(pad_x, pad_y):
    """Return list of (rect, label) for the numpad keys."""
    rows   = [["7","8","9"], ["4","5","6"], ["1","2","3"], ["DEL","0","ENTER"]]
    keys   = []
    kw, kh = 60, 48
    gap    = 8
    for ri, row in enumerate(rows):
        for ci, label in enumerate(row):
            kx = pad_x + ci * (kw + gap)
            ky = pad_y + ri * (kh + gap)
            keys.append((pygame.Rect(kx, ky, kw, kh), label))
    return keys


def _draw_panel(surf, fonts, current, hint_text, hint_color, history, attempts, won, pad_x, pad_y):
    pygame.draw.rect(surf, C_WOOD, (0, PANEL_Y, SW, SH - PANEL_Y))
    pygame.draw.rect(surf, C_RUST, (0, PANEL_Y, SW, 4))
    pygame.draw.rect(surf, C_RUST_DARK, (0, SH - 4, SW, 4))

    # Title
    title = fonts["title"].render("ENTER THE PIN", True, C_PARCHMENT_D)
    surf.blit(title, (SW // 2 - title.get_width() // 2, PANEL_Y + 12))

    # Digit cells
    total_w = 4 * CELL_W + 3 * 10
    start_x = SW // 2 - total_w // 2
    cell_y  = PANEL_Y + 48

    for i in range(4):
        cx         = start_x + i * (CELL_W + 10)
        active     = (i == len(current) and not won)
        border_col = C_PARCHMENT_D if active else C_RUST
        pygame.draw.rect(surf, C_INK, (cx, cell_y, CELL_W, CELL_H), border_radius=4)
        pygame.draw.rect(surf, border_col, (cx, cell_y, CELL_W, CELL_H), 2, border_radius=4)
        if i < len(current):
            ch = fonts["digit"].render(current[i], True, C_PARCHMENT)
            surf.blit(ch, (cx + CELL_W // 2 - ch.get_width() // 2,
                           cell_y + CELL_H // 2 - ch.get_height() // 2))
        elif active and (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.rect(surf, C_PARCHMENT_D,
                             (cx + CELL_W // 2 - 10, cell_y + CELL_H - 12, 20, 2))

    # Hint
    hint = fonts["hint"].render(hint_text, True, hint_color)
    surf.blit(hint, (SW // 2 - hint.get_width() // 2, cell_y + CELL_H + 10))

    # Numpad
    mouse_pos = pygame.mouse.get_pos()
    for rect, label in _numpad_layout(pad_x, pad_y):
        hover = rect.collidepoint(mouse_pos)
        if label == "ENTER":
            bg = C_RUST_LIGHT if hover else C_RUST
        elif label == "DEL":
            bg = C_RUST if hover else C_RUST_DARK
        else:
            bg = C_STONE_LIGHT if hover else C_STONE
        pygame.draw.rect(surf, bg, rect, border_radius=5)
        pygame.draw.rect(surf, C_STONE_LIGHT, rect, 2, border_radius=5)
        lbl = fonts["key"].render(label, True, C_PARCHMENT)
        surf.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                        rect.centery - lbl.get_height() // 2))

    # History (right of numpad)
    hist_x = pad_x + 3 * (60 + 8) + 20
    hist_y = pad_y
    hl     = fonts["small"].render("HISTORY", True, C_STONE_LIGHT)
    surf.blit(hl, (hist_x, hist_y))
    for j, (guess, direction) in enumerate(history[-7:]):
        col    = C_HIGHER if direction == "higher" else (C_LOWER if direction == "lower" else C_MOSS)
        symbol = "▲" if direction == "higher" else ("▼" if direction == "lower" else "✓")
        row    = fonts["small"].render(f"{guess}  {symbol} {direction.title()}", True, col)
        surf.blit(row, (hist_x, hist_y + 22 + j * 22))

    # Attempt count
    att = fonts["small"].render(f"Attempts: {attempts}", True, C_STONE_LIGHT)
    surf.blit(att, (SW // 2 - att.get_width() // 2, SH - 20))

    # Continue prompt after win
    if won:
        cont = fonts["small"].render("Press ENTER or → to continue", True, C_PARCHMENT_D)
        surf.blit(cont, (SW // 2 - cont.get_width() // 2, SH - 38))


def run_guess_game(screen=None, clock=None):
    """
    Run the PIN-guessing mini-game.
    Pass an existing screen + clock when called from main.py.
    Returns True on win, False if the player presses Escape.
    """
    standalone = screen is None
    if standalone:
        pygame.init()
        screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("Guess the PIN")
        clock = pygame.time.Clock()

    fonts = {
        "title": pygame.font.SysFont("Georgia",     18, bold=True),
        "digit": pygame.font.SysFont("Courier New", 38, bold=True),
        "key":   pygame.font.SysFont("Courier New", 16, bold=True),
        "hint":  pygame.font.SysFont("Georgia",     15),
        "small": pygame.font.SysFont("Courier New", 13),
    }

    secret       = str(random.randint(0, 9999)).zfill(4)
    current      = ""
    history      = []
    attempts     = 0
    hint_text    = "Enter a 4-digit PIN and press ENTER"
    hint_color   = C_STONE_LIGHT
    won          = False
    bridge_angle = 1.0   # starts raised
    chain_pct    = 1.0

    cell_y  = PANEL_Y + 48
    pad_x   = SW // 2 - (3 * 60 + 2 * 8) // 2
    pad_y   = cell_y + CELL_H + 42

    def submit():
        nonlocal current, attempts, hint_text, hint_color, won
        if len(current) < 4:
            return
        attempts += 1
        gi = int(current)
        ai = int(secret)
        if gi == ai:
            history.append((current, "correct"))
            hint_text  = f"PIN correct — {secret}"
            hint_color = C_MOSS
            won        = True
        elif gi < ai:
            history.append((current, "higher"))
            hint_text  = "Higher"
            hint_color = C_HIGHER
        else:
            history.append((current, "lower"))
            hint_text  = "Lower"
            hint_color = C_LOWER
        current = ""

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if standalone:
                    pygame.quit()
                    import sys; sys.exit()
                return False

            elif event.type == pygame.KEYDOWN:
                if won:
                    if event.key in (pygame.K_RETURN, pygame.K_RIGHT, pygame.K_KP_ENTER):
                        return True
                    continue
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_BACKSPACE:
                    current = current[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    submit()
                elif event.unicode.isdigit() and len(current) < 4:
                    current += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if won:
                    return True
                for rect, label in _numpad_layout(pad_x, pad_y):
                    if rect.collidepoint(event.pos):
                        if label == "DEL":
                            current = current[:-1]
                        elif label == "ENTER":
                            submit()
                        elif len(current) < 4:
                            current += label
                        break

        # Animate bridge
        if won:
            bridge_angle = max(0.0, bridge_angle - dt * 0.0015)
            chain_pct    = max(0.15, chain_pct - dt * 0.001)
        else:
            bridge_angle = min(1.0, bridge_angle + dt * 0.003)
            chain_pct    = min(1.0, chain_pct + dt * 0.003)

        _draw_scene(screen, bridge_angle, chain_pct)
        _draw_panel(screen, fonts, current, hint_text, hint_color,
                    history, attempts, won, pad_x, pad_y)
        pygame.display.flip()

    return False


if __name__ == "__main__":
    pygame.init()
    run_guess_game()
    pygame.quit()
