"""
SHADOW CHESS - Settings Manager
Handles loading, validation, and saving of application preferences to JSON.
"""

import json
import os
from config import (
    DATA_DIR,
    SETTINGS_FILE,
    DEFAULT_BOARD_THEME,
    DEFAULT_PIECE_THEME,
    DIFFICULTY_MEDIUM,
    BOARD_THEMES,
    PIECE_THEMES,
    DIFFICULTIES
)

DEFAULT_SETTINGS = {
    "sound_enabled": True,
    "sound_volume": 0.8,
    "board_theme": DEFAULT_BOARD_THEME,
    "piece_theme": DEFAULT_PIECE_THEME,
    "animations_enabled": True,
    "ai_difficulty": DIFFICULTY_MEDIUM,
    "player_color": "White",
    "show_legal_moves": True,
    "show_last_move": True
}


class SettingsManager:
    """Manages persistent configuration settings with graceful fallback."""

    def __init__(self, filepath=SETTINGS_FILE):
        self.filepath = filepath
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        """Loads settings from JSON file, creating default if absent or corrupted."""
        if not os.path.exists(self.filepath):
            self.save()
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.settings.update(data)
                self._validate()
        except Exception as e:
            print(f"[SettingsManager] Warning: Error loading settings ({e}). Restoring defaults.")
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()

    def _validate(self):
        """Ensures all values conform to allowed constraints."""
        if not isinstance(self.settings.get("sound_enabled"), bool):
            self.settings["sound_enabled"] = True
        
        vol = self.settings.get("sound_volume", 0.8)
        if not isinstance(vol, (int, float)) or not (0.0 <= vol <= 1.0):
            self.settings["sound_volume"] = 0.8

        if self.settings.get("board_theme") not in BOARD_THEMES:
            self.settings["board_theme"] = DEFAULT_BOARD_THEME

        if self.settings.get("piece_theme") not in PIECE_THEMES:
            self.settings["piece_theme"] = DEFAULT_PIECE_THEME

        if not isinstance(self.settings.get("animations_enabled"), bool):
            self.settings["animations_enabled"] = True

        if self.settings.get("ai_difficulty") not in DIFFICULTIES:
            self.settings["ai_difficulty"] = DIFFICULTY_MEDIUM

        if self.settings.get("player_color") not in ["White", "Black"]:
            self.settings["player_color"] = "White"

        if not isinstance(self.settings.get("show_legal_moves"), bool):
            self.settings["show_legal_moves"] = True

        if not isinstance(self.settings.get("show_last_move"), bool):
            self.settings["show_last_move"] = True

    def save(self):
        """Saves current settings to disk atomically."""
        try:
            dirname = os.path.dirname(self.filepath)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            temp_file = self.filepath + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
            # Atomic replace
            if os.path.exists(self.filepath):
                os.replace(temp_file, self.filepath)
            else:
                os.rename(temp_file, self.filepath)
        except Exception as e:
            print(f"[SettingsManager] Error saving settings: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self._validate()
        self.save()

    def toggle(self, key):
        if key in self.settings and isinstance(self.settings[key], bool):
            self.set(key, not self.settings[key])
            return self.settings[key]
        return None

    def reset_to_defaults(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.save()
