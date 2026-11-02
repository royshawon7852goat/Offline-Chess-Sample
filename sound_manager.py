"""
SHADOW CHESS - Sound Manager
Manages audio playback, volume controls, mute states, and graceful hardware fallbacks.
"""

import os
import pygame
from config import SOUNDS_DIR


class SoundManager:
    """Manages sound effects with volume controls and error-safe execution."""

    def __init__(self, settings_manager=None):
        self.settings = settings_manager
        self.sounds = {}
        self.initialized = False
        self._init_mixer()
        self._load_sounds()

    def _init_mixer(self):
        """Initializes the Pygame audio mixer safely."""
        try:
            # Pre-init mixer with low latency
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.initialized = True
        except Exception as e:
            print(f"[SoundManager] Warning: Audio mixer could not be initialized ({e}). Audio disabled.")
            self.initialized = False

    def _load_sounds(self):
        """Pre-loads all sound effects into memory."""
        if not self.initialized:
            return

        sound_names = [
            "move",
            "capture",
            "check",
            "checkmate",
            "click",
            "game_start",
            "draw",
            "illegal"
        ]

        for name in sound_names:
            filename = f"{name}.wav"
            filepath = os.path.join(SOUNDS_DIR, filename)
            if os.path.exists(filepath):
                try:
                    sound = pygame.mixer.Sound(filepath)
                    self.sounds[name] = sound
                except Exception as e:
                    print(f"[SoundManager] Could not load sound {filename}: {e}")
            else:
                print(f"[SoundManager] Notice: Sound file {filename} not found.")

        self.update_volume()

    def update_volume(self):
        """Updates sound volumes based on current settings."""
        if not self.initialized or not self.settings:
            return

        enabled = self.settings.get("sound_enabled", True)
        volume = self.settings.get("sound_volume", 0.8) if enabled else 0.0

        for sound in self.sounds.values():
            try:
                sound.set_volume(volume)
            except Exception:
                pass

    def play(self, sound_name: str):
        """Plays the requested sound effect if audio is enabled."""
        if not self.initialized:
            return

        if self.settings and not self.settings.get("sound_enabled", True):
            return

        sound = self.sounds.get(sound_name)
        if sound:
            try:
                sound.play()
            except Exception as e:
                print(f"[SoundManager] Error playing {sound_name}: {e}")
