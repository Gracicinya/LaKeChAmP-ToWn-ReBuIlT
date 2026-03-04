"""
Mini-game A: **Guess the Pin**

- Generate secret pin (or pick from list)
- Input box for number entry
- Feedback text: “Higher” / “Lower”
- Show attempt counter
- Win when correct → transition back to storybook with a “bridge lowered” flag

- Hints: “Try the middle of your current range.”, "The pin is a prime number.", "The pin is an even number.", "The pin is an odd number."
"""

import pygame
import random

# ── Initialise ────────────────────────────────────────────────────────────────
pygame.init()

SCREEN_W, SCREEN_H = 900, 640
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Guess the Pin To Unlock the Bridge")
clock = pygame.time.Clock()

def main():
    pass

def run_guess_game():
    return main()

if __name__ == "__main__":
    main()