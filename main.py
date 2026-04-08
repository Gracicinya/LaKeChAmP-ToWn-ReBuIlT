"""
main.py  –  The Remaking of Lakechamp Town
===========================================
Entry point.  Manages the game loop, storybook navigation, and
launches mini-games at the right story moments.

Controls
--------
    LEFT / RIGHT arrow  navigate story pages
    ENTER               launch the mini-game on the current page (if any)
    ESCAPE              quit
"""

# ══════════════════════════════════════════════════════════════════════════════
#  Imports
# ══════════════════════════════════════════════════════════════════════════════
import pygame
import sys
import os

# Add the project root to sys.path so imports work regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, STORY_FONT_SIZE, GAME_TITLE
from mini_games import guess_pin, puzzle_map, road_crossing, slot_placement
from storybook import Storybook, draw_story_page


# ══════════════════════════════════════════════════════════════════════════════
#  GameState  –  persists across scenes
#  Tracks story progress and which mini-games are completed.
# ══════════════════════════════════════════════════════════════════════════════
class GameState:
    def __init__(self):
        self.completed_games = []   # list of mini-game names completed
        self.bridge_lowered  = False
        self.map_restored    = False
        self.residents_home  = False


# ══════════════════════════════════════════════════════════════════════════════
#  Game  –  Main game class
#  Encapsulates the main loop, input handling, rendering, and mini-game transitions.
# ══════════════════════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.screen = None
        self.clock = None
        self.state = GameState()
        self.storybook = None
        self.story_font = None
        self.running = True
        self.in_mini_game = False
        self.mini_games = {
            "guess_pin": (guess_pin.run_guess_game, "bridge_lowered"),
            "puzzle_map": (puzzle_map.run_puzzle_game, "map_restored"),
            "slot_placement": (slot_placement.run_placement_game, "residents_home"),
            "road_crossing": (road_crossing.run_crossing_game, None),
        }

    def init(self):
        """Initialize Pygame, create the window, and build story resources."""
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption(GAME_TITLE)
            self.clock = pygame.time.Clock()

            self.storybook = Storybook()
            self.story_font = pygame.font.Font(None, STORY_FONT_SIZE)
        except Exception as e:
            print(f"Failed to initialize game: {e}", file=sys.stderr)
            sys.exit(1)

    def launch_mini_game(self, mini_game_name):
        """Launch the named mini-game and update story state after success."""
        if mini_game_name not in self.mini_games:
            print(f"Unknown mini-game: {mini_game_name}", file=sys.stderr)
            return False

        self.in_mini_game = True
        func, flag = self.mini_games[mini_game_name]
        result = func(screen=self.screen, clock=self.clock)
        self.in_mini_game = False

        if result:
            if flag:
                setattr(self.state, flag, True)
            if mini_game_name not in self.state.completed_games:
                self.state.completed_games.append(mini_game_name)

        return result

    def handle_events(self):
        """Handle Pygame events."""
        # Process window and keyboard input, including story navigation and mini-game launch.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif not self.in_mini_game:
                    if event.key == pygame.K_RIGHT:
                        self.storybook.next_page()
                    elif event.key == pygame.K_LEFT:
                        self.storybook.prev_page()
                    elif event.key == pygame.K_RETURN:
                        mini_game = self.storybook.get_mini_game()
                        if mini_game:
                            won = self.launch_mini_game(mini_game)
                            if won:
                                self.storybook.next_page()
                            else:
                                self.storybook.reset_current_page()

    def draw(self, dt):
        """Draw the current scene."""
        current_page = self.storybook.get_current_page()
        draw_story_page(self.screen, current_page, self.story_font,
                        SCREEN_WIDTH, SCREEN_HEIGHT, self.state, self.storybook, dt=dt)
        pygame.display.flip()

    def run(self):
        """Main game loop."""
        # Loop until the window is closed or the player quits.
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.draw(dt)


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    game = Game()
    game.init()
    game.run()
    pygame.quit()
    sys.exit()
