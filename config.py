"""
SHADOW CHESS - Configuration & Theme Constants
Premium Dark & Gold Chess Game
"""

import os

# Window & Display
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60
WINDOW_TITLE = "SHADOW CHESS"

# Board Layout
BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8  # 80 pixels
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 80

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PIECES_DIR = os.path.join(ASSETS_DIR, "pieces")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
DATA_DIR = os.path.join(BASE_DIR, "data")

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
STATISTICS_FILE = os.path.join(DATA_DIR, "statistics.json")

# Color Palettes
# -------------------------------------------------------------
# Base UI Colors (Charcoal & Metallic Gold)
COLOR_BG_DARK = (15, 16, 20)          # Deep obsidian black
COLOR_PANEL_BG = (23, 25, 32)         # Charcoal panel background
COLOR_PANEL_SURFACE = (31, 34, 44)    # Elevated cards/containers
COLOR_PANEL_BORDER = (48, 52, 68)     # Subtle card border

# Gold Metallic Accent Palette
COLOR_GOLD_PRIMARY = (212, 175, 55)   # Rich metallic gold
COLOR_GOLD_LIGHT = (245, 215, 110)    # Highlight gold
COLOR_GOLD_MUTED = (145, 120, 40)     # Muted antique gold
COLOR_GOLD_DARK = (90, 75, 25)        # Deep shadow gold

# Text Colors
COLOR_TEXT_WHITE = (240, 242, 248)
COLOR_TEXT_MUTED = (155, 162, 180)
COLOR_TEXT_GOLD = (235, 195, 75)
COLOR_TEXT_DARK = (20, 20, 25)

# Status & Feedback Colors
COLOR_CHECK = (235, 60, 60, 160)       # Glowing red for king in check
COLOR_LAST_MOVE = (212, 175, 55, 75)   # Amber/gold highlight for last move
COLOR_SELECTED = (245, 215, 110, 130)  # Bright gold for selected piece
COLOR_LEGAL_DOT = (212, 175, 55, 170)  # Gold dot for empty legal target
COLOR_LEGAL_CAPTURE = (235, 80, 80, 190)# Red/gold ring for capture target
COLOR_WIN = (65, 210, 120)             # Success green
COLOR_LOSS = (235, 70, 70)             # Defeat red
COLOR_DRAW = (160, 170, 190)           # Neutral silver

# Board Themes
BOARD_THEMES = {
    "Midnight Gold": {
        "name": "Midnight Gold",
        "light_square": (72, 77, 92),
        "dark_square": (38, 41, 51),
        "border_color": (212, 175, 55),
        "highlight_color": (212, 175, 55),
        "desc": "Deep charcoal slate with metallic gold trim"
    },
    "Obsidian & Silver": {
        "name": "Obsidian & Silver",
        "light_square": (62, 66, 78),
        "dark_square": (28, 30, 36),
        "border_color": (180, 190, 210),
        "highlight_color": (160, 185, 230),
        "desc": "Monochrome contrast with platinum accents"
    },
    "Emerald Shadow": {
        "name": "Emerald Shadow",
        "light_square": (60, 95, 75),
        "dark_square": (30, 52, 40),
        "border_color": (90, 205, 140),
        "highlight_color": (80, 220, 150),
        "desc": "Rich forest emerald with luminescent green"
    },
    "Royal Wood": {
        "name": "Royal Wood",
        "light_square": (155, 120, 85),
        "dark_square": (88, 58, 36),
        "border_color": (218, 165, 32),
        "highlight_color": (230, 180, 60),
        "desc": "Warm dark mahogany with antique gold"
    }
}

DEFAULT_BOARD_THEME = "Midnight Gold"

# Piece Themes
PIECE_THEMES = [
    "Shadow Gold",
    "Neon Cyber",
    "Classic Slate"
]
DEFAULT_PIECE_THEME = "Shadow Gold"

# AI Difficulties
DIFFICULTY_EASY = "Easy"
DIFFICULTY_MEDIUM = "Medium"
DIFFICULTY_HARD = "Hard"

DIFFICULTIES = [DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD]

DIFFICULTY_SETTINGS = {
    DIFFICULTY_EASY: {
        "depth": 2,
        "randomness": 0.35,  # 35% chance to introduce slight tactical inaccuracy
        "name": "Apprentice (Easy)",
        "desc": "Good for beginners and casual play."
    },
    DIFFICULTY_MEDIUM: {
        "depth": 3,
        "randomness": 0.05,
        "name": "Knight (Medium)",
        "desc": "Solid tactical vision and positional play."
    },
    DIFFICULTY_HARD: {
        "depth": 4,
        "randomness": 0.0,
        "name": "Grandmaster (Hard)",
        "desc": "Deep search with advanced pruning & piece-square tables."
    }
}
