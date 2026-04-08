"""
storybook.py
============
Story pages, Storybook class, and the draw_story_page() renderer.

Each page dict:
    text       - story text (\n for line breaks)
    bg_color   - RGB background tint
    mini_game  - None  OR  one of: "guess_pin", "puzzle_map", "slot_placement", "road_crossing"

draw_story_page() accepts state, storybook, and dt so it can show
context-sensitive prompts and drive frame-rate-independent animation.
"""

import pygame
import math
import os
import random

_STORY_BG_IMAGE = None

# ==============================================================================
#  Shared palette
# ==============================================================================
C_TEXT        = (255, 255, 255)
C_HINT_KEY    = (255, 255, 100)
C_HINT_NAV    = (180, 200, 180)
C_TITLE       = (232, 217, 184)
C_ACCENT      = (196, 169, 110)

C_RUST        = (139,  58,  26)
C_RUST_LIGHT  = (196,  88,  42)
C_RUST_DARK   = ( 74,  26,   8)
C_WOOD        = (107,  66,  38)
C_WOOD_LIGHT  = (160,  98,  58)
C_WOOD_DARK   = ( 59,  34,  18)
C_STONE       = (122, 112,  96)
C_STONE_LIGHT = (176, 168, 152)
C_WATER       = ( 42,  74, 106)



# ==============================================================================
#  Gradient / drawing helpers
# ==============================================================================

def _gradient_rect(surf, top_col, bot_col, rect):
    x, y, w, h = rect
    for row in range(h):
        t = row / max(h - 1, 1)
        r = int(top_col[0] + (bot_col[0] - top_col[0]) * t)
        g = int(top_col[1] + (bot_col[1] - top_col[1]) * t)
        b = int(top_col[2] + (bot_col[2] - top_col[2]) * t)
        pygame.draw.line(surf, (r, g, b), (x, y + row), (x + w, y + row))


def _draw_stars(surf, width, height, seed=42):
    rng = random.Random(seed)
    for _ in range(120):
        sx   = rng.randint(0, width)
        sy   = rng.randint(0, int(height * 0.65))
        size = rng.choice([1, 1, 1, 2])
        alpha = rng.randint(140, 255)
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, alpha), (size, size), size)
        surf.blit(s, (sx, sy))


def _shimmer(surf, x, y, w, t_ms, idx):
    alpha = int(60 + 50 * math.sin(t_ms * 0.002 + idx * 1.3))
    s = pygame.Surface((w, 3), pygame.SRCALPHA)
    s.fill((200, 230, 255, alpha))
    surf.blit(s, (x, y))


# ==============================================================================
#  Particle system  (confetti on celebration page)
# ==============================================================================

class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "col", "size")

    def __init__(self, width, height):
        self.x        = random.uniform(0, width)
        self.y        = random.uniform(height * 0.15, height * 0.75)
        self.vx       = random.uniform(-30, 30)
        self.vy       = random.uniform(-80, -20)
        self.max_life = random.randint(1200, 2800)
        self.life     = self.max_life
        self.col      = random.choice([
            (255, 220, 60), (255, 140, 60), (100, 220, 130),
            (80, 180, 255), (255, 100, 180), (220, 255, 100),
        ])
        self.size = random.randint(3, 7)

    def update(self, dt):
        self.x    += self.vx * dt * 0.001
        self.y    += self.vy * dt * 0.001
        self.vy   += 40 * dt * 0.001
        self.life -= dt

    def alive(self):
        return self.life > 0

    def draw(self, surf):
        alpha = int(255 * max(0.0, self.life / self.max_life))
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.col, alpha), (self.size, self.size), self.size)
        surf.blit(s, (int(self.x) - self.size, int(self.y) - self.size))


_particles: list = []


def _update_particles(dt, width, height):
    global _particles
    for p in _particles:
        p.update(dt)
    _particles = [p for p in _particles if p.alive()]
    while len(_particles) < 80:
        _particles.append(_Particle(width, height))


# ==============================================================================
#  Scene backdrops
# ==============================================================================

# ---------- 0: Title – calm lake at dusk --------------------------------------
def _backdrop_title(surf, w, h, t):
    water_y = int(h * 0.60)
    _gradient_rect(surf, (40, 60, 110), (180, 100, 50), (0, 0, w, water_y))
    # Moon
    pygame.draw.circle(surf, (255, 245, 200), (int(w * 0.75), int(h * 0.18)), 26)
    pygame.draw.circle(surf, (230, 210, 140), (int(w * 0.75), int(h * 0.18)), 20)
    _draw_stars(surf, w, int(h * 0.55), seed=7)
    # Water
    _gradient_rect(surf, (35, 60, 100), (22, 40, 70), (0, water_y, w, h - water_y))
    for i in range(0, w, 55):
        _shimmer(surf, i, water_y + 18, 35, t, i)
        _shimmer(surf, i + 20, water_y + 32, 25, t, i + 5)
    # Shoreline
    pygame.draw.rect(surf, (30, 22, 14), (0, water_y - 4, w, 8))
    # Town silhouette
    sil = [(0.12, 0.52, 0.04, 0.08), (0.19, 0.47, 0.03, 0.13), (0.24, 0.50, 0.05, 0.10), (0.31, 0.45, 0.04, 0.15), (0.37, 0.51, 0.06, 0.09), (0.44, 0.48, 0.03, 0.12), (0.49, 0.43, 0.04, 0.17), (0.55, 0.50, 0.05, 0.10), (0.62, 0.46, 0.03, 0.14), (0.67, 0.52, 0.06, 0.08), (0.74, 0.47, 0.04, 0.13), (0.80, 0.50, 0.03, 0.10)]
    for rx, ry, rw, rh in sil:
        pygame.draw.rect(surf, (20, 15, 10), (int(w * rx), int(h * ry), int(w * rw), int(h * rh)))
    # Lit windows
    for rx, ry, rw, rh in sil[::2]:
        rng = random.Random(int(rx * 100))
        for _ in range(2):
            wx = int(w * rx) + rng.randint(2, max(3, int(w * rw) - 4))
            wy = int(h * ry) + rng.randint(2, max(3, int(h * rh) - 4))
            pygame.draw.rect(surf, (255, 200, 80), (wx, wy, 3, 3))


# ---------- 1: Ruins – broken town at dusk ------------------------------------
def _backdrop_ruins(surf, w, h, t):
    ground_y = int(h * 0.62)
    _gradient_rect(surf, (60, 35, 30), (130, 65, 35), (0, 0, w, ground_y))
    # Smoke wisps
    for i, (sx, spd) in enumerate([(w*0.20, 0.8), (w*0.45, 1.1), (w*0.70, 0.7)]):
        for seg in range(6):
            sy  = ground_y - 30 - seg * 18
            ox  = int(8 * math.sin(t * 0.001 * spd + i + seg * 0.5))
            alpha = max(0, 90 - seg * 14)
            ss = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(ss, (80, 70, 60, alpha), (8, 8), 8)
            surf.blit(ss, (int(sx) + ox - 8, sy))
    _gradient_rect(surf, (40, 30, 22), (28, 20, 14), (0, ground_y, w, h - ground_y))
    # Rubble
    for rx, rs in [(0.10, 3), (0.28, 5), (0.50, 4), (0.68, 6), (0.85, 3)]:
        rng = random.Random(int(rx * 100))
        for _ in range(rs):
            bx = int(w * rx) + rng.randint(-20, 20)
            by = ground_y + rng.randint(-6, 12)
            bww = rng.randint(8, 22)
            bhh = rng.randint(6, 14)
            col = rng.choice([C_STONE, C_STONE_LIGHT, C_RUST_DARK, C_WOOD_DARK])
            pygame.draw.rect(surf, col, (bx, by, bww, bhh))
    # Broken buildings
    for bx, by, bww, bhh, jagged in [
        (int(w*0.12), int(h*0.35), 55, int(h*0.27), True),
        (int(w*0.30), int(h*0.28), 70, int(h*0.34), False),
        (int(w*0.52), int(h*0.32), 60, int(h*0.30), True),
        (int(w*0.72), int(h*0.30), 50, int(h*0.32), False),
        (int(w*0.86), int(h*0.38), 45, int(h*0.24), True),
    ]:
        pygame.draw.rect(surf, C_STONE, (bx, by, bww, bhh))
        pygame.draw.rect(surf, C_STONE_LIGHT, (bx, by, bww, bhh), 2)
        if jagged:
            pts = [(bx, by), (bx + bww//3, by - 15), (bx + bww//2, by - 5), (bx + 2*bww//3, by - 20), (bx + bww, by)]
            pygame.draw.polygon(surf, C_STONE_LIGHT, pts)
        for wx in range(bx + 6, bx + bww - 6, 16):
            pygame.draw.rect(surf, (20, 15, 10), (wx, by + 10, 8, 12))


# ---------- 2: Scattered – empty roads at dusk --------------------------------
def _backdrop_scattered(surf, w, h, t):
    ground_y = int(h * 0.58)
    _gradient_rect(surf, (45, 38, 28), (90, 70, 45), (0, 0, w, ground_y))
    _gradient_rect(surf, (35, 28, 18), (22, 16, 10), (0, ground_y, w, h - ground_y))
    # Converging road
    pygame.draw.polygon(surf, (50, 45, 40),
        [(w//2 - 30, ground_y - 5), (w//2 + 30, ground_y - 5), (w, h), (0, h)])
    for i in range(5):
        pct = (i + 1) / 6
        rx  = int(w//2 - 30*pct + (w//2)*pct - 15*pct)
        ry  = int(ground_y + (h - ground_y) * pct)
        pygame.draw.rect(surf, (120, 110, 80), (rx, ry, int(6 + 20*pct), int(4 + 8*pct)))
    # Debris
    rng = random.Random(99)
    for _ in range(18):
        lx = rng.randint(0, w)
        ly = ground_y + rng.randint(0, h - ground_y - 5)
        pygame.draw.ellipse(surf, rng.choice([(80,60,30),(60,80,40),(100,70,30)]), (lx, ly, rng.randint(6, 14), rng.randint(4, 8)))


# ---------- 3: Engineers arriving scene ------------------------------
def _backdrop_engineers(surf, w, h, t):
    ground_y = int(h * 0.60)
    _gradient_rect(surf, (100, 160, 220), (220, 180, 100), (0, 0, w, ground_y))
    # Road
    pygame.draw.polygon(surf, (70, 62, 52), [(0, ground_y + 20), (0, h), (w//2, h), (w//2, ground_y + 20)])
    pygame.draw.line(surf, (70, 60, 50), (int(w*0.47), ground_y - 10), (int(w*0.47), ground_y - 44), 2)
    pygame.draw.rect(surf, (100, 80, 40), (int(w*0.44), ground_y - 48, 6, 4))


# ---------- 4: Blueprint / map table ------------------------------------------
def _backdrop_blueprint(surf, w, h, t):
    surf.fill((30, 42, 58))
    for gx in range(0, w, 40):
        pygame.draw.line(surf, (50, 70, 100), (gx, 0), (gx, h), 1)
    for gy in range(0, h, 40):
        pygame.draw.line(surf, (50, 70, 100), (0, gy), (w, gy), 1)
    # Table
    table_rect = (int(w*0.10), int(h*0.30), int(w*0.80), int(h*0.50))
    pygame.draw.rect(surf, (90, 66, 42), table_rect, border_radius=8)
    pygame.draw.rect(surf, C_WOOD_LIGHT, table_rect, 3, border_radius=8)
    # Blueprint paper
    bx0, by0, bw2, bh2 = (int(w*0.16), int(h*0.36), int(w*0.68), int(h*0.38))
    pygame.draw.rect(surf, (42, 72, 120), (bx0, by0, bw2, bh2), border_radius=4)
    pygame.draw.rect(surf, (100, 150, 220), (bx0, by0, bw2, bh2), 2, border_radius=4)
    for gx in range(bx0 + 20, bx0 + bw2 - 10, 30):
        pygame.draw.line(surf, (80, 130, 200), (gx, by0 + 10), (gx, by0 + bh2 - 10), 1)
    for gy in range(by0 + 20, by0 + bh2 - 10, 25):
        pygame.draw.line(surf, (80, 130, 200), (bx0 + 10, gy), (bx0 + bw2 - 10, gy), 1)
    # Building outlines
    for bx3, by3, bw3, bh3 in [(bx0+30,by0+30,40,35),(bx0+90,by0+20,30,50), (bx0+140,by0+40,50,28),(bx0+210,by0+25,35,45)]:
        pygame.draw.rect(surf, (120, 180, 240), (bx3, by3, bw3, bh3), 2)
    # Pencil
    pygame.draw.rect(surf, (230, 200, 60), (int(w*0.25), int(h*0.70), 80, 8), border_radius=2)
    pygame.draw.polygon(surf, (200, 160, 80),
        [(int(w*0.25), int(h*0.70)), (int(w*0.25), int(h*0.70)+8), (int(w*0.25)-10, int(h*0.70)+4)])


# ---------- 5: Puzzle map – parchment pieces -------------------------
def _backdrop_puzzle(surf, w, h, t):
    _gradient_rect(surf, (80, 66, 44), (44, 34, 22), (0, 0, w, h))
    pieces = [
        (0.10, 0.20, 80, 60, 14), (0.30, 0.12, 60, 50, -8),
        (0.55, 0.18, 70, 55, 20), (0.75, 0.25, 55, 65, -15),
        (0.15, 0.55, 65, 50,  9), (0.65, 0.60, 75, 58, -12),
        (0.40, 0.68, 60, 45, 18), (0.85, 0.55, 58, 52, -6),
    ]
    # Bob and rotate pieces, with grid lines and borders to make them look like old parchment
    for i, (px_f, py_f, pw, ph, base_ang) in enumerate(pieces):
        px  = int(w * px_f)
        py  = int(h * py_f)
        ang = math.radians(base_ang + math.sin(t * 0.0008 + i) * 4)
        ps  = pygame.Surface((pw, ph), pygame.SRCALPHA)
        ps.fill((200, 180, 130, 200))
        for gx in range(0, pw, 15):
            pygame.draw.line(ps, (150, 130, 90, 120), (gx, 0), (gx, ph), 1)
        for gy in range(0, ph, 12):
            pygame.draw.line(ps, (150, 130, 90, 120), (0, gy), (pw, gy), 1)
        pygame.draw.rect(ps, (140, 110, 70, 200), (0, 0, pw, ph), 2)
        rotated = pygame.transform.rotate(ps, math.degrees(ang))
        surf.blit(rotated, (px - rotated.get_width()//2, py - rotated.get_height()//2))


# ---------- 6: Bridge locked ----------------------------------------
def _backdrop_bridge_locked(surf, w, h, t):
    water_y = int(h * 0.65)
    _gradient_rect(surf, (35, 38, 55), (70, 55, 35), (0, 0, w, water_y))
    # Storm clouds
    for i, (cx, cy, cr) in enumerate([(w*0.20, h*0.15, 70), (w*0.50, h*0.10, 90), (w*0.75, h*0.18, 65), (w*0.35, h*0.22, 55)]):
        drift = math.sin(t * 0.0005 + i) * 6
        cs = pygame.Surface((int(cr*2.5), int(cr*1.4)), pygame.SRCALPHA)
        for ox, oy, r2 in [(0,0,cr),(cr//2,-cr//4,int(cr*0.7)),(cr,0,int(cr*0.8))]:
            pygame.draw.circle(cs, (55, 52, 65, 200), (ox+cr//2, oy+cr//2), r2)
        surf.blit(cs, (int(cx+drift) - int(cr*1.25), int(cy) - int(cr*0.7)))
    # Rain
    rng = random.Random(int(t / 60))
    for _ in range(40):
        rx = rng.randint(0, w)
        ry = rng.randint(0, water_y)
        pygame.draw.line(surf, (100, 130, 180), (rx, ry), (rx - 2, ry + 14), 1)
    # Water
    _gradient_rect(surf, (28, 45, 75), (18, 30, 55), (0, water_y, w, h - water_y))
    for i in range(0, w, 35):
        wh = int(4 + 3 * math.sin(t * 0.004 + i * 0.05))
        pygame.draw.arc(surf, (50, 90, 140), (i, water_y + 5, 35, wh * 2), 0, math.pi, 2)
    # Pulsing padlock
    lcx, lcy = w // 2, water_y // 2
    pygame.draw.arc(surf, C_RUST, (lcx - 13, lcy - 16, 26, 20), 0, math.pi, 3)
    pygame.draw.rect(surf, C_RUST, (lcx - 16, lcy, 32, 22), border_radius=4)
    pulse = int(30 + 20 * math.sin(t * 0.005))
    ls = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(ls, (200, 80, 40, pulse), (30, 30), 30)
    surf.blit(ls, (lcx - 30, lcy - 30))


# ---------- 7: Guess-PIN – bridge locked + faint keypad -----------------------
def _backdrop_guess_pin(surf, w, h, t):
    _backdrop_bridge_locked(surf, w, h, t)
    pad_w, pad_h = 200, 240
    pad_x = w // 2 - pad_w // 2
    pad_y = int(h * 0.25)
    ps = pygame.Surface((pad_w, pad_h), pygame.SRCALPHA)
    ps.fill((0, 0, 0, 55))
    for ri in range(4):
        for ci in range(3):
            pygame.draw.rect(ps, (80, 70, 60, 80), (8 + ci*64, 8 + ri*58, 54, 48), border_radius=4)
    surf.blit(ps, (pad_x, pad_y))


# ---------- 8: Bridge lowering (dt-driven) -------------------------
def _backdrop_bridge_lowering(surf, w, h, t):
    water_y = int(h * 0.67)
    _gradient_rect(surf, (80, 120, 180), (230, 150, 70), (0, 0, w, water_y))
    # Sun
    sun_x, sun_y = int(w * 0.72), int(water_y * 0.35)
    for r in range(45, 0, -5):
        ss = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(ss, (255, 220, 80, max(0, 25 - r)), (r, r), r)
        surf.blit(ss, (sun_x - r, sun_y - r))
    pygame.draw.circle(surf, (255, 230, 100), (sun_x, sun_y), 30)
    pygame.draw.circle(surf, (255, 250, 200), (sun_x, sun_y), 20)
    # Water
    _gradient_rect(surf, (42, 74, 106), (28, 52, 80), (0, water_y, w, h - water_y))
    for i in range(0, w, 42):
        pygame.draw.arc(surf, (60, 110, 150), (i, water_y + 6, 42, 12), 0, math.pi, 2)
    for i in range(0, w, 58):
        _shimmer(surf, i, water_y + 22, 30, t, i)
    # Cliffs
    cliff_h = 88
    pygame.draw.polygon(surf, C_STONE, [(0, water_y), (120, water_y - cliff_h), (120, h), (0, h)])
    pygame.draw.polygon(surf, C_STONE, [(w, water_y), (w-120, water_y - cliff_h), (w-120, h), (w, h)])
    # Towers
    tower_w, tower_h = 38, 100
    tower_lx = 88
    tower_rx  = w - 88 - tower_w
    tower_y   = water_y - cliff_h - tower_h
    for tx in (tower_lx, tower_rx):
        pygame.draw.rect(surf, C_STONE, (tx, tower_y, tower_w, tower_h + cliff_h))
        pygame.draw.rect(surf, C_STONE_LIGHT, (tx, tower_y, tower_w, tower_h + cliff_h), 2)
        for m in range(4):
            pygame.draw.rect(surf, C_STONE_LIGHT, (tx + 2 + m*9, tower_y - 14, 7, 14))
        slit_cx = tx + tower_w // 2
        pygame.draw.rect(surf, (30, 25, 20), (slit_cx - 2, tower_y + 20, 4, 16), border_radius=2)
    # Distant town silhouette
    for bx_f, bh2 in [(0.30,50),(0.34,80),(0.39,40),(0.45,65),(0.50,55),(0.56,45),(0.62,70)]:
        pygame.draw.rect(surf, (60, 50, 40), (int(w*bx_f), water_y - cliff_h - bh2, 28, bh2))


# ---------- 9: Road crossing --------------------------------------------------
def _backdrop_road_crossing(surf, w, h, t):
    ground_y = int(h * 0.35)
    _gradient_rect(surf, (120, 170, 230), (200, 220, 250), (0, 0, w, ground_y))
    # Clouds
    for i, (cx_f, cy_f, cw, ch) in enumerate(
            [(0.15, 0.10, 90, 35), (0.45, 0.06, 110, 40), (0.75, 0.12, 80, 30)]):
        drift = math.sin(t * 0.0003 + i) * 8
        cs = pygame.Surface((cw, ch), pygame.SRCALPHA)
        for ox, oy, r in [(0,ch//2,ch//2),(cw//3,0,int(ch*0.6)),(2*cw//3,ch//4,int(ch*0.55)),(cw,ch//2,ch//2)]:
            pygame.draw.circle(cs, (255, 255, 255, 220), (ox, oy), r)
        surf.blit(cs, (int(w*cx_f) + int(drift), int(h*cy_f)))
    # Pavement
    pygame.draw.rect(surf, (160, 155, 140), (0, ground_y, w, 20))
    # Road
    road_y = ground_y + 20
    road_h = int(h * 0.45)
    _gradient_rect(surf, (55, 52, 48), (40, 38, 35), (0, road_y, w, road_h))
    lane_h = road_h // 3
    for lane in range(1, 3):
        ly = road_y + lane * lane_h
        for dx in range(0, w, 50):
            dash_phase = (t * 0.1 + dx) % 50
            if dash_phase < 30:
                pygame.draw.rect(surf, (220, 200, 60), (dx, ly - 2, 30, 4))
    # Cars (animated)
    for speed_f, cy, col, direction in [
        (0.04, road_y + 18,  (180, 50, 50),   1),
        (0.07, road_y + 68,  (50, 80, 180),  -1),
        (0.05, road_y + 118, (60, 160, 80),   1),
        (0.06, road_y + 168, (180, 130, 50), -1),
    ]:
        cx = (int(t * speed_f * 60) % (w + 80)) - 80 if direction == 1 \
            else w - (int(t * speed_f * 60) % (w + 80)) + 40
        pygame.draw.rect(surf, col, (cx, cy, 60, 22), border_radius=4)
        pygame.draw.rect(surf, tuple(max(0,c-30) for c in col), (cx + 10, cy - 12, 36, 14), border_radius=3)
        pygame.draw.rect(surf, (180, 220, 255), (cx + 13, cy - 11, 12, 11))
        pygame.draw.rect(surf, (180, 220, 255), (cx + 28, cy - 11, 12, 11))
        for wx in (cx + 8, cx + 44):
            pygame.draw.circle(surf, (30, 30, 30), (wx, cy + 22), 7) 
            pygame.draw.circle(surf, (100, 100, 100), (wx, cy + 22), 4)
    # Bottom pavement & grass
    pygame.draw.rect(surf, (160, 155, 140), (0, road_y + road_h, w, 22))
    _gradient_rect(surf, (72, 110, 58), (50, 80, 38), (0, road_y + road_h + 22, w, h - road_y - road_h - 22))
    # Pedestrian waiting
    pw_x = int(w * 0.10)
    pw_y = road_y + road_h + 5
    pygame.draw.circle(surf, (200, 160, 110), (pw_x, pw_y - 14), 8)
    pygame.draw.rect(surf, (80, 100, 160), (pw_x - 6, pw_y - 6, 12, 18))


# ---------- 10: Residents almost home -----------------------------------------
def _backdrop_residents(surf, w, h, t):
    ground_y = int(h * 0.55)
    _gradient_rect(surf, (160, 200, 230), (220, 240, 255), (0, 0, w, ground_y))
    pygame.draw.circle(surf, (255, 240, 160), (int(w*0.80), int(h*0.15)), 22)
    _gradient_rect(surf, (80, 110, 65), (55, 80, 44), (0, ground_y, w, h - ground_y))
    pygame.draw.rect(surf, (90, 85, 75), (0, ground_y + 10, w, 30))
    # Houses
    configs = [
        (int(w*0.08), ground_y-90,  70, 90, (180,100,70), (220,60,50)),
        (int(w*0.25), ground_y-80,  65, 80, (160,140,110),(180,80,60)),
        (int(w*0.45), ground_y-100, 75,100, (140,120,90), (200,70,55)),
        (int(w*0.65), ground_y-85,  68, 85, (170,110,80), (190,65,50)),
        (int(w*0.83), ground_y-75,  62, 75, (155,130,100),(210,75,58)),
    ]
    for hx, hy, hbw, hbh, wall_col, roof_col in configs:
        pygame.draw.rect(surf, wall_col, (hx, hy + int(hbh*0.3), hbw, int(hbh*0.7)))
        pygame.draw.rect(surf, tuple(min(255,c+20) for c in wall_col), (hx, hy + int(hbh*0.3), hbw, int(hbh*0.7)), 2)
        pygame.draw.polygon(surf, roof_col,
            [(hx-4, hy+int(hbh*0.3)+2), (hx+hbw//2, hy), (hx+hbw+4, hy+int(hbh*0.3)+2)])
        dw, dh = 12, 20
        pygame.draw.rect(surf, (60, 40, 20), (hx+hbw//2-dw//2, hy+hbh-dh, dw, dh), border_radius=2)
        for wx_off in (8, hbw - 20):
            alpha = int(200 + 40 * math.sin(t * 0.003 + hx * 0.01))
            ws = pygame.Surface((14, 12), pygame.SRCALPHA)
            ws.fill((255, 220, 100, alpha))
            surf.blit(ws, (hx + wx_off, hy + int(hbh*0.4)))
    # Walking family
    walk_x = int((t * 0.02) % (w * 0.5) + w * 0.1)
    walk_y = ground_y + 5
    for ox, oy, r in [(-20, 0, 7), (-8, 3, 6), (4, 2, 5)]:
        pygame.draw.circle(surf, (60, 45, 35), (walk_x + ox, walk_y + oy - 22), r)
        pygame.draw.rect(surf, (60, 45, 35), (walk_x+ox-r+2, walk_y+oy-15, r*2-4, 15))


# ---------- 11: Slot placement – residents + faint slots ----------------------
def _backdrop_slot_placement(surf, w, h, t):
    _backdrop_residents(surf, w, h, t)
    ps = pygame.Surface((w, h), pygame.SRCALPHA)
    for i, fx in enumerate([0.15, 0.38, 0.62, 0.85]):
        alpha = int(40 + 20 * math.sin(t * 0.002 + i))
        pygame.draw.rect(ps, (255, 255, 255, alpha), (int(w*fx) - 30, int(h*0.20), 60, 80), 2, border_radius=6)
    surf.blit(ps, (0, 0))


# ---------- 12: Celebration ---------------------------------------------------
def _backdrop_celebration(surf, w, h, t, dt, state):
    ground_y = int(h * 0.58)
    _gradient_rect(surf, (80, 140, 220), (180, 230, 255), (0, 0, w, ground_y))
    # Sun
    sun_x, sun_y = w // 2, int(h * 0.12)
    for r in range(60, 0, -6):
        ss = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(ss, (255, 240, 100, max(0, 18 - r//3)), (r, r), r)
        surf.blit(ss, (sun_x - r, sun_y - r))
    pygame.draw.circle(surf, (255, 245, 150), (sun_x, sun_y), 32)
    _gradient_rect(surf, (80, 130, 60), (55, 95, 40), (0, ground_y, w, h - ground_y))
    pygame.draw.rect(surf, (80, 76, 70), (0, ground_y + 15, w, 28))
    for dx in range(0, w, 50):
        pygame.draw.rect(surf, (210, 195, 55), (dx, ground_y + 27, 28, 4))
    # Full town
    configs = [
        (int(w*0.05),  ground_y-100, 72, 100, (175,100,65), (210,55,45)),
        (int(w*0.20),  ground_y- 85, 65,  85, (155,135,105),(175,70,55)),
        (int(w*0.36),  ground_y-110, 78, 110, (135,115,85), (195,60,50)),
        (int(w*0.54),  ground_y- 90, 70,  90, (165,105,75), (185,62,48)),
        (int(w*0.72),  ground_y-100, 74, 100, (150,125,95), (200,68,52)),
        (int(w*0.87),  ground_y- 80, 62,  80, (160,115,80), (205,72,56)),
    ]
    for hx, hy, hbw, hbh, wall_col, roof_col in configs:
        pygame.draw.rect(surf, wall_col, (hx, hy+int(hbh*0.3), hbw, int(hbh*0.7)))
        pygame.draw.rect(surf, tuple(min(255,c+25) for c in wall_col), (hx, hy+int(hbh*0.3), hbw, int(hbh*0.7)), 2)
        pygame.draw.polygon(surf, roof_col, [(hx-5,hy+int(hbh*0.3)+2),(hx+hbw//2,hy),(hx+hbw+5,hy+int(hbh*0.3)+2)])
        dw, dh = 13, 22
        pygame.draw.rect(surf, (55, 35, 18), (hx+hbw//2-dw//2, hy+hbh-dh, dw, dh), border_radius=2)
        for wx_off in (6, hbw - 20):
            ws = pygame.Surface((14, 12), pygame.SRCALPHA)
            ws.fill((255, 220, 100, 220))
            surf.blit(ws, (hx + wx_off, hy + int(hbh*0.4)))
        # Flags
        fx = hx + hbw // 2
        fy = hy - 20
        pygame.draw.line(surf, (120, 90, 50), (fx, fy), (fx, fy - 22), 2)
        wave = int(4 * math.sin(t * 0.004 + hx * 0.02))
        pygame.draw.polygon(surf, (220, 60, 60),
            [(fx, fy-22), (fx+14+wave, fy-16), (fx, fy-10)])
    # Confetti
    _update_particles(dt, w, h)
    for p in _particles:
        p.draw(surf)


# ---------- 13: Town Hall dedication ------------------------------------------
def _backdrop_town_hall(surf, w, h, t):
    ground_y = int(h * 0.60)
    _gradient_rect(surf, (100, 155, 215), (195, 225, 250), (0, 0, w, ground_y))
    _gradient_rect(surf, (72, 110, 58), (50, 80, 38), (0, ground_y, w, h - ground_y))


# ---------- 14: Lake / river --------------------------------------------------
def _backdrop_lake(surf, w, h, t):
    water_y = int(h * 0.45)
    _gradient_rect(surf, (90, 150, 210), (180, 220, 250), (0, 0, w, water_y))
    # Clouds
    for i, (cx_f, cr) in enumerate([(0.12, 55), (0.40, 70), (0.68, 50), (0.88, 60)]):
        drift = math.sin(t * 0.0003 + i * 0.8) * 10
        cs = pygame.Surface((int(cr*2.5), int(cr*1.2)), pygame.SRCALPHA)
        for ox, oy, r in [(0,cr//2,cr//2),(cr//2,0,int(cr*0.65)),(cr,cr//4,int(cr*0.7)),(int(cr*1.5),cr//2,cr//2)]:
            pygame.draw.circle(cs, (255, 255, 255, 230), (ox, oy), r)
        surf.blit(cs, (int(w*cx_f)+int(drift)-int(cr*1.25), int(h*0.04)))
    # Lake
    _gradient_rect(surf, (55, 120, 190), (35, 85, 145), (0, water_y, w, h - water_y))
    for i in range(0, w, 48):
        pygame.draw.arc(surf, (70, 140, 210), (i, water_y+8, 48, 14), 0, math.pi, 2)
    for i in range(0, w, 65):
        _shimmer(surf, i, water_y+28, 38, t, i)
    # Banks
    _gradient_rect(surf, (72, 118, 55), (50, 88, 36), (0, 0, w, 40))
    _gradient_rect(surf, (72, 118, 55), (50, 88, 36), (0, h-50, w, 50))


# ---------- 15: Credits – night sky over town ---------------------------------
def _backdrop_credits(surf, w, h, t):
    _gradient_rect(surf, (25, 35, 55), (10, 18, 32), (0, 0, w, h))
    _draw_stars(surf, w, h, seed=77)
    # Moon
    pygame.draw.circle(surf, (240, 235, 200), (w//2, int(h*0.22)), 38)
    pygame.draw.circle(surf, (255, 252, 230), (w//2, int(h*0.22)), 28)
    for r in range(60, 0, -6):
        ms = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(ms, (240, 235, 200, max(0, 15-r//4)), (r, r), r)
        surf.blit(ms, (w//2-r, int(h*0.22)-r))


def _load_story_bg(width, height):
    global _STORY_BG_IMAGE
    if _STORY_BG_IMAGE is None:
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            "assets", "storybook mainbg - silhouette skyline illustration", "78791.jpg"
        ))
        if os.path.exists(path):
            try:
                _STORY_BG_IMAGE = pygame.image.load(path).convert()
            except pygame.error:
                _STORY_BG_IMAGE = None
        else:
            _STORY_BG_IMAGE = None

    if _STORY_BG_IMAGE is not None:
        return pygame.transform.smoothscale(_STORY_BG_IMAGE, (width, height))
    return None


# ==============================================================================
#  Story pages
# ==============================================================================
STORY_PAGES = [
    # 0 - Title / instructions
    {
        "title":     "The Remaking of Lakechamp Town",
        "text": "Use the LEFT and RIGHT arrow keys to turn the pages.\n"
                "Press ENTER on challenge pages to begin a mini-game.\n\n"
                "The town remembers what it once was.\n"
                "Now it needs your help to become whole again.",                           
        "bg_color":  (40, 55, 80),
        "mini_game": None,
    },
    # 1 - Establish the world
    {
        "title":     None,
        "text": "Lakechamp was once a place of warm evenings and open doors.\n"
                "Children raced through the square; neighbours shared stories\n"
                "over fences and front porches.\n\n"
                "Then the disaster came—sudden, merciless—and the laughter\n"
                "vanished, leaving only quiet streets and shattered homes.",
        "bg_color":  (60, 40, 40),
        "mini_game": None,
    },
    # 2 - The displacement
    {
        "title":     None,
        "text": "Families fled in every direction, carrying only what they could.\n"
                "The town that once felt unbreakable fell silent.\n\n"
                "Yet even scattered, the people of Lakechamp held on to one\n"
                "belief: their home was worth returning to.",                                                                      
    },
    # 3 - Help arrives
    {
        "title":     None,
        "text": "Weeks later, a familiar team returned—engineers, planners,\n"
                "and builders who had shaped Lakechamp long ago.\n\n"
                "\"We built this town once,\" said the lead engineer,\n"
                "brushing dust from a fallen beam.\n"
                "\"And with your help, we’ll bring it back again.\"",
        "bg_color":  (35, 55, 45),
        "mini_game": None,
    },
    # 4 - Need a map first
    {
        "title":     None,
        "text": "Before rebuilding can begin, the team needs a full map of\n"
                "Lakechamp’s streets and landmarks.\n\n"
                "But the original blueprints were torn apart in the chaos.\n"
                "Only scattered fragments remain.\n"
                "Can you restore what was lost?",
        "bg_color":  (50, 65, 80),
        "mini_game": None,
    },
    # 5 - MINI-GAME: puzzle_map
    {
        "title":     "Challenge: Restore the Town Map",
        "text": "Drag and drop the map pieces into the correct positions.\n"
                "Pieces snap into place when you find the right spot.\n\n"
                "Reassemble all nine fragments to reveal Lakechamp Town.",
        "bg_color":  (45, 55, 40),
        "mini_game": "puzzle_map",
    },
    # 6 - Bridge is the next obstacle
    {
        "title":     None,
        "text": "With the map restored, supply routes finally make sense.\n\n"
                "But the old drawbridge—Lakechamp’s lifeline—won’t budge.\n"
                "A rusted PIN pad clings to the gatehouse wall, its screen\n"
                "flickering weakly.\n\n"
                "Someone locked it before the disaster… but who?",                                                     
        "bg_color":  (55, 40, 30),
        "mini_game": None,
    },
    # 7 - MINI-GAME: guess_pin
    {
        "title":     "Challenge: Unlock the Bridge",
        "text": "Guess the 4-digit PIN to lower the drawbridge.\n"
                "After each attempt, you’ll learn whether the correct\n"
                "number is Higher or Lower.\n\n"
                "Crack the code and reopen Lakechamp’s supply line.",
        "bg_color":  (55, 40, 25),
        "mini_game": "guess_pin",
    },
    # 8 - Supplies flow; bridge lowered (animated)
    {
        "title":     None,
        "text": "The bridge groans, then lowers with a triumphant clang.\n"
                "Trucks roll across, carrying timber, tools, medicine,\n"
                "and the first fresh food the town has seen in months.\n\n"
                "Now the residents begin to return.\n"
                "Four families stand at the edge of town, hopeful and afraid.",
        "bg_color":  (35, 60, 50),
        "mini_game": None,
    },
    # 9 - MINI-GAME: road_crossing
    {
        "title":     "Challenge: Cross the Road",
        "text": "Guide the first resident safely across the busy road.\n\n"
                "Use the ARROW KEYS to move.\n"
                "Watch for gaps in traffic—three lives, use them well.",
        "bg_color":  (40, 50, 65),
        "mini_game": "road_crossing",
    },
    # 10 - Almost home
    {
        "title":     None,
        "text": "One by one, the residents brave the road and step onto\n"
                "Lakechamp’s soil again.\n\n"
                "But the rebuilt streets feel unfamiliar.\n"
                "Homes stand where rubble once lay, and memories blur.\n\n"
                "Help each family find the doorway that belongs to them.",
        "bg_color":  (45, 55, 35),
        "mini_game": None,
    },
    # 11 - MINI-GAME: slot_placement
    {
        "title":     "Challenge: Guide the Residents Home",
        "text":      "Drag each resident to their matching home.\n\n"
                    "Look at the name above each slot to find\n"
                    "where each family belongs.",
        "bg_color":  (40, 60, 45),
        "mini_game": "slot_placement",
    },
    # 12 - Main ending / celebration
    {
        "title":     "Lakechamp Town - Restored",
        "text": "Laughter returns to the streets as families settle in.\n"
                "The bridge stands strong. The restored map hangs proudly\n"
                "in the town hall.\n\n"
                "Lakechamp was not only rebuilt—it was remembered.",
        "bg_color":  (35, 55, 45),
        "mini_game": None,
    },
    # 13 - Epilogue: Town Hall
    {
        "title":     "Epilogue: The Town Hall",
        "text": "In the weeks that follow, the community gathers beneath\n"
                "the newly rebuilt rafters of the town hall.\n\n"
                "They frame the restored map and hang it high—a promise\n"
                "that what breaks can be rebuilt when hands work together.",
        "bg_color":  (45, 40, 60),
        "mini_game": None,
    },
    # 14 - Epilogue: The lake
    {
        "title":     "Epilogue: The Lake",
        "text": "Children return to the lake that gave the town its name.\n\n"
                "They sail paper boats across the calm water, just as\n"
                "their parents once did.\n"
                "The open bridge watches over them—a symbol of hope kept.",   
        "bg_color":  (30, 55, 70),
        "mini_game": None,
    },
    # 15 - Credits / final page
    {
        "title":     "Thank You",
        "text": "Lakechamp stands tall once more.\n\n"
                "Every puzzle solved. Every family home.\n"
                "Every road crossed.\n\n"
                "You helped bring a town back to life.",
        "bg_color":  (20, 22, 38),
        "mini_game": None,
    },
]

# ==============================================================================
#  Storybook
# ==============================================================================
class Storybook:
    def __init__(self):
        self.current_page = 0
        self.total_pages  = len(STORY_PAGES)

    def get_current_page(self):
        if 0 <= self.current_page < self.total_pages:
            return STORY_PAGES[self.current_page]
        return None

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            return True
        return False

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            return True
        return False

    def is_last_page(self):
        return self.current_page >= self.total_pages - 1

    def get_mini_game(self):
        page = self.get_current_page()
        return page["mini_game"] if page else None

    def reset_current_page(self):
        # No state is stored per page, so resetting keeps the player on the same page.
        self.current_page = max(0, min(self.current_page, self.total_pages - 1))
        return self.get_current_page()

    def page_number(self):
        return self.current_page

    def total(self):
        return self.total_pages


# ==============================================================================
#  draw_story_page
# ==============================================================================

def draw_story_page(screen, page, font, width, height, state=None, storybook=None, dt=16):
    """
    Render a single story page using the storybook background image.
    """
    if not page:
        screen.fill((20, 20, 30))
        return

    t = pygame.time.get_ticks()

    # Show the storybook background image for every page when available.
    bg_image = _load_story_bg(width, height)
    if bg_image is not None:
        screen.blit(bg_image, (0, 0))
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        screen.blit(overlay, (0, 0))
    else:
        screen.fill(page["bg_color"])

    # No illustrated backdrops are drawn; the JPG is the main page background.

    # -- Vignette --
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    for _, rect in [
        ("top",    (0, 0, width, 45)),
        ("bottom", (0, height-45, width, 45)),
        ("left",   (0, 0, 55, height)),
        ("right",  (width-55, 0, 55, height)),
    ]:
        pygame.draw.rect(vignette, (0, 0, 0, 65), rect)
    screen.blit(vignette, (0, 0))

    # -- Title --
    title_font = pygame.font.Font(None, 38)
    if page.get("title"):
        title_surf = title_font.render(page["title"], True, C_TITLE)
        screen.blit(title_surf, (width//2 - title_surf.get_width()//2, 42))
        text_start_y = 112
    else:
        text_start_y = height // 2 - 80

    # -- Text box --
    text_lines = page["text"].split("\n")
    line_h     = 36
    box_h      = len(text_lines) * line_h + 32
    box_x      = 60
    box_y      = text_start_y - 16
    box_w      = width - 120

    has_bg_image = bg_image is not None
    box_alpha    = 190 if has_bg_image else 100
    border_col   = C_WOOD_LIGHT if has_bg_image else (80, 80, 80)

    box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box_surf.fill((0, 0, 0, box_alpha))
    screen.blit(box_surf, (box_x, box_y))
    pygame.draw.rect(screen, border_col, (box_x, box_y, box_w, box_h), 1, border_radius=6)

    y_offset = text_start_y
    for line in text_lines:
        rendered = font.render(line, True, C_TEXT)
        screen.blit(rendered, (box_x + 16, y_offset))
        y_offset += line_h

    # -- Mini-game prompt --
    if page.get("mini_game"):
        mini_name    = page["mini_game"]
        already      = state and mini_name in state.completed_games
        prompt_text  = ("Completed!"
                        if already else "Press ENTER to start the challenge")
        prompt_color = (120, 200, 120) if already else C_HINT_KEY

        prompt_font = pygame.font.Font(None, 26)
        prompt      = prompt_font.render(prompt_text, True, prompt_color)
        py          = height - 60
        px          = width//2 - prompt.get_width()//2
        bg_s        = pygame.Surface((prompt.get_width()+24, prompt.get_height()+10), pygame.SRCALPHA)
        bg_s.fill((0, 0, 0, 130))
        screen.blit(bg_s, (px-12, py-5))
        screen.blit(prompt, (px, py))

    # -- Navigation arrows --
    nav_font = pygame.font.Font(None, 22)
    if storybook and storybook.current_page > 0:
        left = nav_font.render("  prev", True, C_HINT_NAV)
        screen.blit(left, (20, height-28))
    if storybook and not storybook.is_last_page():
        right = nav_font.render("next  ", True, C_HINT_NAV)
        screen.blit(right, (width - right.get_width()-20, height-28))

    # -- Page counter --
    if storybook:
        pg_txt = nav_font.render(
            f"{storybook.current_page+1} / {storybook.total_pages}",
            True, (110, 110, 110))
        screen.blit(pg_txt, (width//2 - pg_txt.get_width()//2, height-28))

    # -- ESC hint --
    esc = nav_font.render("ESC = quit", True, (80, 80, 80))
    screen.blit(esc, (width - esc.get_width()-10, 10))
