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
import pygame