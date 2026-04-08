"""
puzzle_map.py
=============
Mini-game: Drag-and-drop town map puzzle.
Wraps the logic from town_puzzle.py into a run_puzzle_game() function
that returns True on completion, False on Escape/quit.

The puzzle is a 3x3 grid sliced from community_map.jpg.
"""

import pygame
import sys
import random
import os

# ── Layout & colour constants (mirror town_puzzle.py) ────────────────────────
COLS, ROWS  = 3, 3
TILE_SIZE   = 160
SCREEN_W    = 960
SCREEN_H    = 640
BOARD_X     = 350
BOARD_Y     = (SCREEN_H - ROWS * TILE_SIZE) // 2
TRAY_X      = 10
TRAY_Y      = 10
TRAY_W      = 320
TRAY_H      = SCREEN_H - 20
TRAY_COLS   = 2
TRAY_PAD    = 12

WHITE       = (255, 255, 255)
MID_GREY    = (160, 165, 170)
DARK_GREY   = ( 70,  75,  80)
BG_COLOUR   = ( 34, 140, 200)
BOARD_BG    = ( 44,  52,  63)
TRAY_BG     = ( 25,  30,  38)
GREEN       = ( 72, 199, 142)
HELD_YELLOW = (255, 210,  80)
LABEL_COL   = (180, 190, 200)

MAP_IMAGE_PATH = "community_map.jpg"

FALLBACK_COLOURS = [
    (100, 140, 190), ( 80, 170, 100), (190, 130,  80),
    (200,  80,  80), (170, 120, 200), (220, 100,  60),
    ( 90, 160, 180), (160, 150, 100), (110, 110, 170),
]


# Load and slice the town map into puzzle tiles, or fall back to coloured placeholder tiles.
def _load_tiles(font_big):
    """Load and slice the map image, or return fallback coloured tiles."""
    # Search for the image next to main.py / this file
    candidates = [
        MAP_IMAGE_PATH,
        os.path.join(os.path.dirname(__file__), MAP_IMAGE_PATH),
        os.path.join(os.path.dirname(__file__), "..", MAP_IMAGE_PATH),
    ]
    full_path = None
    for c in candidates:
        if os.path.exists(c):
            full_path = c
            break

    if full_path is None:
        tiles = []
        for i, col in enumerate(FALLBACK_COLOURS):
            s = pygame.Surface((TILE_SIZE, TILE_SIZE))
            s.fill(col)
            tiles.append(s)
        return tiles, None

    raw       = pygame.image.load(full_path).convert()
    target_w  = TILE_SIZE * COLS
    target_h  = TILE_SIZE * ROWS
    full_img  = pygame.transform.scale(raw, (target_w, target_h))

    tiles = []
    for row in range(ROWS):
        for col in range(COLS):
            t = pygame.Surface((TILE_SIZE, TILE_SIZE))
            t.blit(full_img, (0, 0), pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            tiles.append(t)

    ref = pygame.transform.scale(raw, (target_w, target_h)).convert_alpha()
    ref.set_alpha(60)
    return tiles, ref


# Puzzle piece object stores its target slot, image, and drag state.
class _Piece:
    def __init__(self, index, image):
        self.index  = index
        self.image  = image
        self.placed = False
        self.rect   = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)

    def draw(self, surface, held=False):
        if self.placed:
            return
        surface.blit(self.image, self.rect)
        col = HELD_YELLOW if held else (200, 200, 200)
        w   = 3 if held else 2
        pygame.draw.rect(surface, col, self.rect, width=w, border_radius=4)


class _Slot:
    def __init__(self, index):
        col = index % COLS
        row = index // COLS
        self.index  = index
        self.rect   = pygame.Rect(
            BOARD_X + col * TILE_SIZE,
            BOARD_Y + row * TILE_SIZE,
            TILE_SIZE, TILE_SIZE,
        )
        self.filled = False

    def draw(self, surface, piece=None):
        if self.filled and piece:
            surface.blit(piece.image, self.rect)
        else:
            pygame.draw.rect(surface, MID_GREY, self.rect, width=2, border_radius=4)


def _layout_tray(pieces, shuffled_tray, map_tiles):
    """Position un-placed pieces in the tray."""
    unplaced = [pieces[i] for i in shuffled_tray if not pieces[i].placed]
    tile_w   = (TRAY_W - TRAY_PAD * (TRAY_COLS + 1)) // TRAY_COLS
    for i, piece in enumerate(unplaced):
        tc = i % TRAY_COLS
        tr = i // TRAY_COLS
        x  = TRAY_X + TRAY_PAD + tc * (tile_w + TRAY_PAD)
        y  = TRAY_Y + 70 + tr * (tile_w + TRAY_PAD)
        piece.rect  = pygame.Rect(x, y, tile_w, tile_w)
        piece.image = pygame.transform.scale(map_tiles[piece.index], (tile_w, tile_w))


# Draw the puzzle screen, including the board, tray, and win overlay.
def _draw(screen, fonts, pieces, slots, shuffled_tray, held_piece,
          reference_image, complete, win_timer):
    screen.fill(BG_COLOUR)

    # Tray
    pygame.draw.rect(screen, TRAY_BG,  (TRAY_X, TRAY_Y, TRAY_W, TRAY_H), border_radius=14)
    pygame.draw.rect(screen, MID_GREY, (TRAY_X, TRAY_Y, TRAY_W, TRAY_H), width=2, border_radius=14)
    lbl = fonts["med"].render("PIECES", True, LABEL_COL)
    screen.blit(lbl, (TRAY_X + TRAY_W // 2 - lbl.get_width() // 2, TRAY_Y + 18))
    remaining = sum(1 for p in pieces if not p.placed)
    rem = fonts["small"].render(f"{remaining} of {COLS*ROWS} remaining", True, MID_GREY)
    screen.blit(rem, (TRAY_X + TRAY_W // 2 - rem.get_width() // 2, TRAY_Y + 44))

    # Board panel
    board_rect = pygame.Rect(BOARD_X - 16, BOARD_Y - 40,
                              COLS * TILE_SIZE + 32, ROWS * TILE_SIZE + 56)
    pygame.draw.rect(screen, BOARD_BG,  board_rect, border_radius=14)
    pygame.draw.rect(screen, MID_GREY, board_rect, width=2, border_radius=14)
    t = fonts["med"].render("TOWN MAP", True, LABEL_COL)
    screen.blit(t, (board_rect.centerx - t.get_width() // 2, board_rect.y + 10))

    # Reference image ghost
    if reference_image:
        screen.blit(reference_image, (BOARD_X, BOARD_Y))

    # Slots
    for slot in slots:
        slot.draw(screen, pieces[slot.index] if slot.filled else None)

    # Tray pieces
    for i in shuffled_tray:
        p = pieces[i]
        if not p.placed and p is not held_piece:
            p.draw(screen)

    # Held piece
    if held_piece:
        held_piece.draw(screen, held=True)

    # Hint
    hint = fonts["small"].render("R = restart   ESC = back to story", True, DARK_GREY)
    screen.blit(hint, (SCREEN_W - hint.get_width() - 10, SCREEN_H - 20))

    # Win overlay
    if complete:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        alpha   = min(200, win_timer // 3)
        overlay.fill((10, 15, 25, int(alpha)))
        screen.blit(overlay, (0, 0))
        if win_timer > 300:
            cx, cy = SCREEN_W // 2, SCREEN_H // 2
            w1 = fonts["big"].render("Puzzle Complete!", True, GREEN)
            w2 = fonts["med"].render("You've revealed the map of Lakechamp Town.", True, WHITE)
            w3 = fonts["small"].render("Press ENTER or → to continue", True, LABEL_COL)
            screen.blit(w1, w1.get_rect(center=(cx, cy - 44)))
            screen.blit(w2, w2.get_rect(center=(cx, cy + 8)))
            screen.blit(w3, w3.get_rect(center=(cx, cy + 48)))

    pygame.display.flip()


# Main puzzle mini-game loop: handles input, dragging, dropping, and completion.
def run_puzzle_game(screen=None, clock=None):
    """
    Run the map-puzzle mini-game.
    Returns True on completion, False on Escape/quit.
    """
    standalone = screen is None
    if standalone:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Town Map Puzzle")
        clock  = pygame.time.Clock()

    fonts = {
        "big":   pygame.font.SysFont("Segoe UI", 36, bold=True),
        "med":   pygame.font.SysFont("Segoe UI", 20),
        "small": pygame.font.SysFont("Segoe UI", 14),
    }

    map_tiles, reference_image = _load_tiles(fonts["big"])

    def _reset():
        pieces       = [_Piece(i, map_tiles[i]) for i in range(COLS * ROWS)]
        slots        = [_Slot(i) for i in range(COLS * ROWS)]
        shuffled     = list(range(COLS * ROWS))
        random.shuffle(shuffled)
        _layout_tray(pieces, shuffled, map_tiles)
        return pieces, slots, shuffled

    pieces, slots, shuffled_tray = _reset()
    held_piece  = None
    drag_offset = (0, 0)
    complete    = False
    win_timer   = 0

    running = True
    while running:
        ms = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if standalone:
                    pygame.quit(); sys.exit()
                return False

            elif event.type == pygame.KEYDOWN:
                if complete:
                    if event.key in (pygame.K_RETURN, pygame.K_RIGHT, pygame.K_KP_ENTER):
                        return True
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    pieces, slots, shuffled_tray = _reset()
                    held_piece  = None
                    complete    = False
                    win_timer   = 0

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if complete:
                    return True
                mx, my = event.pos
                for i in shuffled_tray[::-1]:
                    p = pieces[i]
                    if not p.placed and p.rect.collidepoint(mx, my):
                        p.image     = pygame.transform.scale(map_tiles[p.index], (TILE_SIZE, TILE_SIZE))
                        p.rect      = pygame.Rect(p.rect.x, p.rect.y, TILE_SIZE, TILE_SIZE)
                        held_piece  = p
                        drag_offset = (mx - p.rect.x, my - p.rect.y)
                        break

            elif event.type == pygame.MOUSEMOTION:
                if held_piece:
                    mx, my = event.pos
                    held_piece.rect.x = mx - drag_offset[0]
                    held_piece.rect.y = my - drag_offset[1]

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if held_piece and not complete:
                    mx, my = event.pos
                    for slot in slots:
                        if not slot.filled and slot.rect.collidepoint(mx, my):
                            if slot.index == held_piece.index:
                                slot.filled       = True
                                held_piece.placed = True
                                held_piece.rect   = slot.rect.copy()
                                held_piece.image  = pygame.transform.scale(
                                    map_tiles[held_piece.index], (TILE_SIZE, TILE_SIZE))
                            break
                    held_piece = None
                    _layout_tray(pieces, shuffled_tray, map_tiles)
                    if all(s.filled for s in slots):
                        complete  = True
                        win_timer = 0

        if complete:
            win_timer += ms

        _draw(screen, fonts, pieces, slots, shuffled_tray,
            held_piece, reference_image, complete, win_timer)

    return False


if __name__ == "__main__":
    pygame.init()
    run_puzzle_game()
    pygame.quit()
