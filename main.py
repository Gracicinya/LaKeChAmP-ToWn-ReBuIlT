"""
    - Text styles:- Heading, body, small UI text
    - Colors:- Primary, secondary, background, text, error

- Overlays:
    - Pause menu
    - Tutorial modal
    - Hint modal
    - Win/lose screen template

Create a `GameState` object that persists across scenes:

- `current_page`
- `completed_games`
- `bridge_lowered`
- `map_restored`
- `residents_home`

**Passive interactions**

- Smoke: looping particle puffs or drifting translucent circles
- Residents: simple idle sprites that wander on story pages

"""
# ══════════════════════════════════════════════════════════════════════════════
#  Import
# ══════════════════════════════════════════════════════════════════════════════
import pygame
import sys
import random
import time
import os
import math
from storybook import Storybook, draw_story_page
from mini_games import guess_pin, puzzle_map, slot_placement, road_crossing

# ══════════════════════════════════════════════════════════════════════════════
#  Global Variables
# ══════════════════════════════════════════════════════════════════════════════

# Game state variables
in_mini_game = False


# ══════════════════════════════════════════════════════════════════════════════
#  Initialize
# ══════════════════════════════════════════════════════════════════════════════

# Initialize Pygame
# Create the game window and clock
# Define game variables
# Background image

# Define colors, fonts, and other constants
# Define the GameState class to manage game state across scenes

def GameState():
    def __init__(self):
        self.current_page = 0
        self.completed_games = []
        self.bridge_lowered = False
        self.map_restored = False
        self.residents_home = False

def init():
    global screen, FPS, end, clock, state, background_image, resident1_image, resident2_image, resident3_image, resident4_image, residents_speed, storybook, story_font, screen_width, screen_height
    pygame.init()

    screen_width, screen_height = 900, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("The Remaking of Lakechamp Town")
    FPS = 60
    clock = pygame.time.Clock()

    # Initialize the storybook
    storybook = Storybook()
    story_font = pygame.font.Font(None, 26)

    # Initialize mini-game state
    in_mini_game = False

    # Load background image and other assets here
    background_image = pygame.Surface((screen_width, screen_height))  # Placeholder for background image
    background_image.fill((200, 200, 255))  # Light blue background

    residents_speed = 2
    
    """CHANGE THIS LATER
     - For now, I'm using colored rectangles as placeholders for the resident images.
     - Later, I can replace these with actual images of the residents.
     - I plan on making them more lively by having them move around predetermined paths that align with map layout.
     """
    # Placeholders for resident images
    resident1_image = pygame.Surface((50, 50))  # Placeholder for resident 1 image
    resident1_image.fill((255, 0, 0))  # Red square for resident 1
    resident2_image = pygame.Surface((50, 50))  # Placeholder for resident 2 image
    resident2_image.fill((0, 255, 0))  # Green square for resident 2
    resident3_image = pygame.Surface((50, 50))  # Placeholder for resident 3 image
    resident3_image.fill((0, 0, 255))  # Blue square for resident 3
    resident4_image = pygame.Surface((50, 50))  # Placeholder for resident 4 image
    resident4_image.fill((255, 255, 0))  # Yellow square for resident 4
    """I will update the above placeholders and load actual images for the residents when available."""
# ══════════════════════════════════════════════════════════════════════════════
#  Update
# ══════════════════════════════════════════════════════════════════════════════

# Event handling: Check for user input
# Game logic updates
def Update():
    global screen, FPS, end, clock, background_image, residents_speed, in_mini_game

# Event handling: Check for user input (keyboard(arrow keys, enter to select, escape to pause), mouse(right click, left click))
# Event handling: Update state based on user input (next page, launch mini game, tutorial, hints, select menu options, pause game)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                storybook.next_page()
            elif event.key == pygame.K_LEFT:
                storybook.prev_page()
            elif event.key == pygame.K_RETURN and not in_mini_game:
                # Check if current page has a mini-game to launch
                mini_game = storybook.get_mini_game()
                if mini_game == "puzzle_map":
                    in_mini_game = True
                    # Launch the puzzle game
                    if puzzle_map.run_puzzle_game():
                        # Puzzle completed successfully
                        storybook.next_page()  # Move to next story page
                    in_mini_game = False
                elif mini_game == "guess_pin":
                    in_mini_game = True
                    # Launch the guessing game
                    if guess_pin.run_guess_game():
                        # Puzzle completed successfully
                        storybook.next_page()  # Move to next story page
                    in_mini_game = False
                elif mini_game == "slot_placement":
                    in_mini_game = True
                    # Launch the slot placement game
                    if slot_placement.run_placement_game():
                        # Puzzle completed successfully
                        storybook.next_page()  # Move to next story page
                    in_mini_game = False
                elif mini_game == "road_crossing":
                    in_mini_game = True
                    # Launch the road crossing game
                    if road_crossing.run_crossing_game():
                        # Puzzle completed successfully
                        storybook.next_page()  # Move to next story page
                    in_mini_game = False

# Game logic updates (e.g., move residents, check for interactions, update game state, smoke animation)
# implement per‑frame updates: move residents, animate smoke, check for win/lose conditions.
# if a mini‑game is active, call its update function or hand control to it.
# update state.completed_games and other flags as the player progresses.

# ══════════════════════════════════════════════════════════════════════════════
#  Draw
# ══════════════════════════════════════════════════════════════════════════════

def Draw():
    # Draw the background and story content
    current_page = storybook.get_current_page()
    
    # Draw the story page (background, text, navigation hints)
    draw_story_page(screen, current_page, story_font, screen_width, screen_height)
    
    # Draw residents
    screen.blit(resident1_image, (100, 100))  # Draw resident 1 at (100, 100)
    screen.blit(resident2_image, (200, 100))  # Draw resident 2 at (200, 100)
    screen.blit(resident3_image, (300, 100))  # Draw resident 3 at (300, 100)
    screen.blit(resident4_image, (400, 100))  # Draw resident 4 at (400, 100)

    pygame.display.flip()
    clock.tick(FPS)

    # Render the current page's content based on state.current_page


# ══════════════════════════════════════════════════════════════════════════════
#  Main game loop
# ══════════════════════════════════════════════════════════════════════════════

def MainLoop():
    global end

    end = False
    while not end:
        Update()
        Draw()

# ══════════════════════════════════════════════════════════════════════════════
#  Run the game
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init()
    MainLoop()

# ══════════════════════════════════════════════════════════════════════════════
#  Quit
# ══════════════════════════════════════════════════════════════════════════════

    pygame.quit()
    sys.exit()