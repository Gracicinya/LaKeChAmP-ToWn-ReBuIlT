"""
Town Map Puzzle Game
====================
A drag-and-drop puzzle game where you assemble a map of the town.
The puzzle pieces are sliced from the image of the town map.

HOW TO PLAY:
  - Click and drag a puzzle piece from the left tray
  - Drop it onto the matching spot on the board
  - If correct, it snaps into place
  - Place all pieces correctly to win!

CONTROLS:
  R = restart / reshuffle

REQUIREMENTS:
  pip install pygame
"""

import pygame
import sys
import random
import os

# ══════════════════════════════════════════════════════════════════════════════
#  Map image
# ══════════════════════════════════════════════════════════════════════════════
MAP_IMAGE_PATH = "community_map.jpg"
# ══════════════════════════════════════════════════════════════════════════════

# ── Initialise ────────────────────────────────────────────────────────────────
pygame.init()

SCREEN_W, SCREEN_H = 960, 640
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Town Map Puzzle")
clock = pygame.time.Clock()

# ── Layout constants ──────────────────────────────────────────────────────────
COLS, ROWS   = 3, 3
TILE_SIZE    = 160     # each puzzle piece is TILE_SIZE x TILE_SIZE pixels
BOARD_X      = 350     # left edge of the puzzle board area
BOARD_Y      = (SCREEN_H - ROWS * TILE_SIZE) // 2
TRAY_X       = 10
TRAY_Y       = 10
TRAY_W       = 320
TRAY_H       = SCREEN_H - 20
TRAY_COLS    = 2
TRAY_PAD     = 12

# ── Colours ───────────────────────────────────────────────────────────────────
WHITE       = (255, 255, 255)
MID_GREY    = (160, 165, 170)
DARK_GREY   = ( 70,  75,  80)
BG_COLOUR   = ( 34,  140,  200)
BOARD_BG    = ( 44,  52,  63)
TRAY_BG     = ( 25,  30,  38)
GREEN       = ( 72, 199, 142)
HELD_YELLOW = (255, 210,  80)
LABEL_COL   = (180, 190, 200)

# ── Fonts ─────────────────────────────────────────────────────────────────────
font_big   = pygame.font.SysFont("Segoe UI", 36, bold=True)
font_med   = pygame.font.SysFont("Segoe UI", 20)
font_small = pygame.font.SysFont("Segoe UI", 14)


# ── Load & slice the map image into pygame surfaces ───────────────────────────
def load_map_tiles(image_path, tile_size, cols, rows):
    """
    Load an image using pure pygame, resize it to fit the grid exactly,
    then slice it into (cols x rows) tile surfaces.
    Returns a list of pygame.Surface objects ordered left→right, top→bottom.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path  = os.path.join(script_dir, image_path)

    if not os.path.exists(full_path):
        print(f"[WARNING] Map image not found: {full_path}")
        print("          Using coloured placeholder tiles instead.")
        return None

    # Load and scale the full image to exactly fit the grid
    raw_img   = pygame.image.load(full_path).convert()
    target_w  = tile_size * cols
    target_h  = tile_size * rows
    full_img  = pygame.transform.scale(raw_img, (target_w, target_h))

    # Slice into tiles by blitting each region onto a new surface
    tiles = []
    for row in range(rows):
        for col in range(cols):
            tile_surf = pygame.Surface((tile_size, tile_size))
            # Source rect: the region of the full image for this tile
            src_rect  = pygame.Rect(col * tile_size, row * tile_size, tile_size, tile_size)
            tile_surf.blit(full_img, (0, 0), src_rect)
            tiles.append(tile_surf)

    return tiles   # list of COLS×ROWS pygame surfaces


# ── Fallback: coloured placeholder tiles (when no image is available) ─────────
FALLBACK_COLOURS = [
    (100, 140, 190), ( 80, 170, 100), (190, 130,  80),
    (200,  80,  80), (170, 120, 200), (220, 100,  60),
    ( 90, 160, 180), (160, 150, 100), (110, 110, 170),
]
FALLBACK_ICONS = ["🏛","🌳","🏫","🏥","🛒","🚒","📚","🏘","🚉"]

def make_fallback_tile(index, tile_size):
    """Create a simple coloured tile surface as a fallback."""
    colour = FALLBACK_COLOURS[index % len(FALLBACK_COLOURS)]
    icon   = FALLBACK_ICONS[index % len(FALLBACK_ICONS)]
    surf   = pygame.Surface((tile_size, tile_size))
    surf.fill(colour)
    # draw icon
    icon_surf = font_big.render(icon, True, WHITE)
    surf.blit(icon_surf, icon_surf.get_rect(center=(tile_size//2, tile_size//2 - 10)))
    return surf


# ── Load tiles ────────────────────────────────────────────────────────────────
map_tiles = load_map_tiles(MAP_IMAGE_PATH, TILE_SIZE, COLS, ROWS)

if map_tiles is None:
    # Use coloured fallback tiles
    map_tiles = [make_fallback_tile(i, TILE_SIZE) for i in range(COLS * ROWS)]

# ── Reference image ───────────────────────────────────────────────────────────
script_dir      = os.path.dirname(os.path.abspath(__file__))
full_path       = os.path.join(script_dir, MAP_IMAGE_PATH)
reference_image = pygame.image.load(full_path).convert_alpha()
ref_w           = COLS * TILE_SIZE
ref_h           = ROWS * TILE_SIZE
reference_image = pygame.transform.scale(reference_image, (ref_w, ref_h))
reference_image.set_alpha(60)   # 0 = invisible, 255 = fully opaque, 60 = low opacity

# ── Puzzle Piece ──────────────────────────────────────────────────────────────
class Piece:
    """One puzzle piece, carrying the image slice for its correct grid position."""

    def __init__(self, index):
        self.index  = index                     # which slot this piece belongs to
        self.image  = map_tiles[index]          # pygame.Surface (the slice)
        self.placed = False                     # True once placed into place
        self.rect   = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)

    def draw(self, surface, held=False):
        if self.placed:
            return
        # Draw the image slice
        surface.blit(self.image, self.rect)
        # Border
        border_col = HELD_YELLOW if held else (200, 200, 200)
        border_w   = 3 if held else 2
        pygame.draw.rect(surface, border_col, self.rect, width=border_w, border_radius=4)



# ── Board Slot ────────────────────────────────────────────────────────────────
class Slot:
    """One empty slot on the puzzle board waiting for its matching piece."""

    def __init__(self, index):
        col = index % COLS
        row = index // COLS
        self.index  = index
        self.rect   = pygame.Rect(
            BOARD_X + col * TILE_SIZE,
            BOARD_Y + row * TILE_SIZE,
            TILE_SIZE, TILE_SIZE
        )
        self.filled = False

    def draw(self, surface, piece=None):
        if self.filled and piece:
            # Show the correctly placed image
            surface.blit(piece.image, self.rect)
        else:
                    # Empty slot: border only, reference image shows through
                    pygame.draw.rect(surface, MID_GREY, self.rect, width=2, border_radius=4)

# ── Build game objects ────────────────────────────────────────────────────────
slots  = [Slot(i)  for i in range(COLS * ROWS)]
pieces = [Piece(i) for i in range(COLS * ROWS)]

shuffled_tray = list(range(len(pieces)))
random.shuffle(shuffled_tray)


def layout_tray():
    """Re-position all un-placed pieces neatly inside the tray panel."""
    unplaced = [pieces[i] for i in shuffled_tray if not pieces[i].placed]
    tile_w   = (TRAY_W - TRAY_PAD * (TRAY_COLS + 1)) // TRAY_COLS
    for i, piece in enumerate(unplaced):
        tray_col = i % TRAY_COLS
        tray_row = i // TRAY_COLS
        x  = TRAY_X + TRAY_PAD + tray_col * (tile_w + TRAY_PAD)
        y  = TRAY_Y + 70 + tray_row  * (tile_w + TRAY_PAD)
        piece.rect = pygame.Rect(x, y, tile_w, tile_w)
        # Scale the piece image to match tray tile size
        piece.image = pygame.transform.scale(map_tiles[piece.index], (tile_w, tile_w))


layout_tray()


# ── Drag state ────────────────────────────────────────────────────────────────
held_piece  = None
drag_offset = (0, 0)

# ── Win state ─────────────────────────────────────────────────────────────────
complete  = False
win_timer = 0


# Draw
def draw():
    screen.fill(BG_COLOUR)

    # ── Tray panel ────────────────────────────────────────────────────────
    pygame.draw.rect(screen, TRAY_BG, (TRAY_X, TRAY_Y, TRAY_W, TRAY_H), border_radius=14)
    pygame.draw.rect(screen, MID_GREY, (TRAY_X, TRAY_Y, TRAY_W, TRAY_H), width=2, border_radius=14)

    tray_label = font_med.render("PIECES", True, LABEL_COL)
    screen.blit(tray_label, (TRAY_X + TRAY_W//2 - tray_label.get_width()//2, TRAY_Y + 18))

    remaining = sum(1 for piece in pieces if not piece.placed)
    rem_label = font_small.render(f"{remaining} of {COLS*ROWS} remaining", True, MID_GREY)
    screen.blit(rem_label, (TRAY_X + TRAY_W//2 - rem_label.get_width()//2, TRAY_Y + 44))

    # ── Board panel ───────────────────────────────────────────────────────
    board_rect = pygame.Rect(
        BOARD_X - 16, BOARD_Y - 40,
        COLS * TILE_SIZE + 32, ROWS * TILE_SIZE + 56
    )
    pygame.draw.rect(screen, BOARD_BG, board_rect, border_radius=14)
    pygame.draw.rect(screen, MID_GREY, board_rect, width=2, border_radius=14)

    title = font_med.render("TOWN MAP", True, LABEL_COL)
    screen.blit(title, (board_rect.centerx - title.get_width()//2, board_rect.y + 10))

    # ── Reference image (low opacity, under pieces) ───────────────────────────
    screen.blit(reference_image, (BOARD_X, BOARD_Y))

    # ── Slots ─────────────────────────────────────────────────────────────
    for slot in slots:
        piece_for_slot = pieces[slot.index] if slot.filled else None
        slot.draw(screen, piece_for_slot)

    # ── Tray pieces ───────────────────────────────────────────────────────
    for i in shuffled_tray:
        piece = pieces[i]
        if not piece.placed and piece is not held_piece:
            piece.draw(screen)

    # ── Held piece (on top of everything) ─────────────────────────────────
    if held_piece:
        held_piece.draw(screen, held=True)

    # ── Controls hint ─────────────────────────────────────────────────────
    hint = font_small.render("R = restart", True, DARK_GREY)
    screen.blit(hint, (SCREEN_W - hint.get_width() - 10, SCREEN_H - 20))

    # ── Win overlay ───────────────────────────────────────────────────────
    if complete:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        alpha   = min(200, win_timer // 3)
        overlay.fill((10, 15, 25, int(alpha)))
        screen.blit(overlay, (0, 0))

        if win_timer > 300:
            center_x, center_y = SCREEN_W // 2, SCREEN_H // 2
            win_title = font_big.render("🎉  Puzzle Complete!  🎉", True, GREEN)
            win_subtitle = font_med.render("You've revealed the ideal town map.", True, WHITE)
            win_restart = font_small.render("Press  R  to play again", True, LABEL_COL)
            screen.blit(win_title, win_title.get_rect(center=(center_x, center_y - 44)))
            screen.blit(win_subtitle, win_subtitle.get_rect(center=(center_x, center_y +  8)))
            screen.blit(win_restart, win_restart.get_rect(center=(center_x, center_y + 48)))

    pygame.display.flip()

# ── Main game loop ────────────────────────────────────────────────────────────
def main():
    global held_piece, drag_offset, complete, win_timer

    while True:
        # Reset state at the start of each game
        random.shuffle(shuffled_tray)
        for piece in pieces:
            piece.placed = False
            piece.image  = map_tiles[piece.index]
        for slot in slots:
            slot.filled = False
        held_piece = None
        complete  = False
        win_timer = 0
        layout_tray()

        running = True
        while running:
            ms_elapsed = clock.tick(60)

            # ── Events ────────────────────────────────────────────────────────────
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        running = False   # breaks inner loop, outer while True restarts

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if complete:
                        continue
                    mouse_x, mouse_y = event.pos
                    for i in shuffled_tray[::-1]:
                        piece = pieces[i]
                        if not piece.placed and piece.rect.collidepoint(mouse_x, mouse_y):
                            # Scale back to full TILE_SIZE when picked up
                            piece.image     = pygame.transform.scale(map_tiles[piece.index], (TILE_SIZE, TILE_SIZE))
                            piece.rect      = pygame.Rect(piece.rect.x, piece.rect.y, TILE_SIZE, TILE_SIZE)
                            held_piece  = piece
                            drag_offset = (mouse_x - piece.rect.x, mouse_y - piece.rect.y)
                            break

                elif event.type == pygame.MOUSEMOTION:
                    if held_piece:
                        mouse_x, mouse_y = event.pos
                        held_piece.rect.x = mouse_x - drag_offset[0]
                        held_piece.rect.y = mouse_y - drag_offset[1]

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if held_piece and not complete:
                        mouse_x, mouse_y  = event.pos
                        for slot in slots:
                            if not slot.filled and slot.rect.collidepoint(mouse_x, mouse_y):
                                if slot.index == held_piece.index:
                                    # Correct!
                                    slot.filled       = True
                                    held_piece.placed = True
                                    held_piece.rect   = slot.rect.copy()
                                    held_piece.image  = pygame.transform.scale(
                                        map_tiles[held_piece.index], (TILE_SIZE, TILE_SIZE))
                                break   # only check one slot
                        held_piece = None
                        layout_tray()   # update tray after piece placed

                        if all(s.filled for s in slots):
                            complete       = True
                            win_timer = 0

            if complete:
                win_timer += ms_elapsed

            # ── Draw ──────────────────────────────────────────────────────────────
            draw()



if __name__ == "__main__":
    main()
