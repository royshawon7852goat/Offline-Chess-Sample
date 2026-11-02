"""
SHADOW CHESS - Piece Renderer & Cache
Loads, scales, and caches piece surfaces for board rendering with procedural fallbacks.
"""

import os
import pygame
from typing import Dict, Tuple
from config import PIECES_DIR, SQUARE_SIZE

# Piece type character mapping
PIECE_CHARS = {
    1: "p",  # Pawn
    2: "n",  # Knight
    3: "b",  # Bishop
    4: "r",  # Rook
    5: "q",  # Queen
    6: "k"   # King
}


class PieceRenderer:
    """Manages high-DPI chess piece surfaces with caching and procedural fallbacks."""

    def __init__(self):
        self._cache: Dict[Tuple[str, str, int, str], pygame.Surface] = {}
        self.current_theme = "Shadow Gold"

    def set_theme(self, theme_name: str):
        if self.current_theme != theme_name:
            self.current_theme = theme_name
            self._cache.clear()

    def get_piece_surface(self, piece_type: int, color: bool, size: int = SQUARE_SIZE, theme: str = None) -> pygame.Surface:
        """
        Retrieves a smoothly scaled piece surface.
        piece_type: 1..6 (chess.PAWN..chess.KING)
        color: True for White, False for Black
        size: Target pixel width and height (square)
        """
        active_theme = theme or self.current_theme
        color_str = "w" if color else "b"
        piece_char = PIECE_CHARS.get(piece_type, "p")
        key = (piece_char, color_str, size, active_theme)

        if key in self._cache:
            return self._cache[key]

        # Attempt to load from theme folder
        theme_slug = active_theme.lower().replace(" ", "_")
        paths_to_try = [
            os.path.join(PIECES_DIR, theme_slug, f"{color_str}_{piece_char}.png"),
            os.path.join(PIECES_DIR, f"{color_str}_{piece_char}.png"),
        ]

        loaded_surf = None
        for path in paths_to_try:
            if os.path.exists(path):
                try:
                    raw_img = pygame.image.load(path)
                    if pygame.display.get_surface() is not None:
                        img = raw_img.convert_alpha()
                    else:
                        img = raw_img
                    loaded_surf = pygame.transform.smoothscale(img, (size, size))
                    break
                except Exception as e:
                    print(f"[PieceRenderer] Warning: Failed loading image {path}: {e}")

        # If loading failed, produce procedural vector fallback
        if loaded_surf is None:
            loaded_surf = self._draw_procedural_fallback(piece_char, color, size)

        self._cache[key] = loaded_surf
        return loaded_surf

    def _draw_procedural_fallback(self, piece_char: str, color: bool, size: int) -> pygame.Surface:
        """Draws a clean, stylized geometric fallback piece."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        main_color = (240, 240, 245) if color else (25, 27, 34)
        gold_color = (212, 175, 55)

        # Base circle
        pygame.draw.circle(surf, gold_color, (cx, cy), size // 2 - 4, width=3)
        pygame.draw.circle(surf, main_color, (cx, cy), size // 2 - 8)

        # Letter glyph in center
        try:
            font = pygame.font.SysFont("segoe ui,arial", int(size * 0.45), bold=True)
            text_surf = font.render(piece_char.upper(), True, gold_color)
            text_rect = text_surf.get_rect(center=(cx, cy))
            surf.blit(text_surf, text_rect)
        except Exception:
            pass

        return surf
