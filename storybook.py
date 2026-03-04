"""
Main story gets told here. 
Should be able to read the story from page 1 to the end with arrows, even if mini-games are placeholders.

Goal: deliver the narrative pages smoothly, and launch mini-games at the right moments.
Make the rebuild feel like “stages of recovery.”

- Page:
    - page background colors/images
    - A consistent palette (3–5 main colors + 1 accent)
    - story text box
- UI:
    - **Left/Right arrows** for navigation (storybook and at the end of mini-games)
    - **Restart** button (global)
    - **Hint** button (global)
    - **Tutorial** button (global)
"""


import pygame
# ══════════════════════════════════════════════════════════════════════════════
#  Story Pages
# ══════════════════════════════════════════════════════════════════════════════

STORY_PAGES = [
    {
        "text": "Navigate through the story using the left and right arrow keys. ",
        "bg_color": (100, 100, 150),
        "mini_game": None
    },
    {
        "text": "The streets of Lakechamp were once filled with laughter, "
        "\nBut after disaster struck, only broken buildings and empty homes remained. ",
        "bg_color": (100, 100, 150),
        "mini_game": None
    },
    {
        "text": "The residents were displaced, the town left in disarray, and the future uncertain. "
        "\nNow the residents are trying to get back on their feet. ",
        "bg_color": (100, 100, 150),
        "mini_game": None
    },
    {
        "text": "Thankfully the team of engineers, builders, and city planners that built"
        "\n the town have returned to help with the restoration efforts.",
        "bg_color": (100, 100, 150),
        "mini_game": None
    },
    {
        "text": "With the bridge fixed, supplies can flow in."
        "\nBut before the engineers can proceed, they need a map of the town.",
        "bg_color": (100, 100, 150),
        "mini_game": None
    },
    {
        "text": "Complete the puzzle that reveals the map of the town. "
        "\nDrag and drop map pieces into the correct positions. "
        "\nPieces will snap into place when positioned correctly. "
        "\nAll map pieces must be placed correctly to win.",
        "bg_color": (150, 120, 80),
        "mini_game": "puzzle_map"
    },
    {
        "text": "The bridge that connects the town to the outside world is broken."
        "\n\nThe engineers and the residents need you to restore it.",
        "bg_color": (100, 100, 150),
        "mini_game": None
    },
    {
        "text": "How to fix the bridge: "
        "\n\nYou need to guess the secret pin code that unlocks the control panel."
        "\n\nBegin by pressing the ENTER key to start the mini-game."
        "\nYou need to complete the challenge to continue the story.",
        "bg_color": (120, 80, 60),
        "mini_game": "guess_pin"
    },

    {
        "text": "The engineers need to navigate the town safely.\n\n Help them avoid the cars and obstacles",
        "bg_color": (100, 130, 100),
        "mini_game": "road_crossing"
    },
    {
        "text": "The town has been restored!\n\nNext, we need to bring the residents back home.",
        "bg_color": (80, 120, 150),
        "mini_game": "slot_placement"
    },
    {
        "text": "Great work! The residents are returning home.\n\nThe town is coming back to life!",
        "bg_color": (150, 150, 100),
        "mini_game": None
    },
    {
        "text": "Congratulations! Lakechamp Town has been rebuilt.\n\nThank you for your hard work in the restoration!",
        "bg_color": (100, 150, 100),
        "mini_game": None
    }
]


class Storybook:
    """Manages story pages and navigation."""
    
    def __init__(self):
        self.current_page = 0
        self.total_pages = len(STORY_PAGES)
    
    def get_current_page(self):
        """Returns the current page data."""
        if self.current_page < self.total_pages:
            return STORY_PAGES[self.current_page]
        return None
    
    def next_page(self):
        """Move to the next page if available."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            return True
        return False
    
    def prev_page(self):
        """Move to the previous page if available."""
        if self.current_page > 0:
            self.current_page -= 1
            return True
        return False
    
    def is_last_page(self):
        """Check if we're on the last page."""
        return self.current_page >= self.total_pages - 1
    
    def get_mini_game(self):
        """Returns the mini game to launch for this page, if any."""
        page = self.get_current_page()
        if page:
            return page["mini_game"]
        return None


def draw_story_page(screen, page, font, width, height):
    """Draws a story page to the screen."""
    if not page:
        return
    
    # Draw background
    bg_color = page["bg_color"]
    screen.fill(bg_color)
    
    # Draw text box
    text = page["text"]
    text_lines = text.split("\n")
    y_offset = height // 2 - 50
    
    for line in text_lines:
        rendered_text = font.render(line, True, (255, 255, 255))
        screen.blit(rendered_text, (50, y_offset))
        y_offset += 40
    
    # Draw mini-game hint if this page has one
    if page.get("mini_game"):
        mini_game_hint = font.render("Press ENTER to start mini-game", True, (255, 255, 100))
        screen.blit(mini_game_hint, (width // 2 - mini_game_hint.get_width() // 2, height - 30))