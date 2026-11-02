"""
SHADOW CHESS - Main Application Entrypoint
Premium Offline Desktop Chess Game in Python
"""

import sys
import os
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS, PIECES_DIR
from settings import SettingsManager
from statistics import StatisticsManager
from sound_manager import SoundManager
from ui import ChessUI


def main():
    """Initializes and runs the Shadow Chess desktop application."""
    # Initialize Pygame core
    pygame.init()

    # Create Display Window
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    # Set Window Icon if piece texture exists
    try:
        icon_path = os.path.join(PIECES_DIR, "w_k.png")
        if os.path.exists(icon_path):
            icon_surf = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surf)
    except Exception as e:
        print(f"[Main] Notice: Could not set window icon: {e}")

    # Initialize Core Managers
    settings_manager = SettingsManager()
    stats_manager = StatisticsManager()
    sound_manager = SoundManager(settings_manager)

    # Initialize UI Engine
    ui = ChessUI(screen, settings_manager, stats_manager, sound_manager)

    clock = pygame.time.Clock()
    running = True

    # Main Application Loop (60 FPS)
    while running:
        # Event Processing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                ui.handle_event(event)

        # Graphical Render
        ui.draw()
        pygame.display.flip()

        # Framerate enforcement
        clock.tick(FPS)

    # Clean Exit
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
