"""
SHADOW CHESS - User Interface & Graphical Engine
Renders high-end dark & metallic gold menus, boards, side-panels, animations, and modals.
"""

import math
import time
import pygame
import chess
from typing import Optional, Tuple, List, Dict, Callable
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    BOARD_SIZE, SQUARE_SIZE,
    BOARD_OFFSET_X, BOARD_OFFSET_Y,
    COLOR_BG_DARK, COLOR_PANEL_BG, COLOR_PANEL_SURFACE, COLOR_PANEL_BORDER,
    COLOR_GOLD_PRIMARY, COLOR_GOLD_LIGHT, COLOR_GOLD_MUTED, COLOR_GOLD_DARK,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_GOLD, COLOR_TEXT_DARK,
    COLOR_CHECK, COLOR_LAST_MOVE, COLOR_SELECTED, COLOR_LEGAL_DOT, COLOR_LEGAL_CAPTURE,
    BOARD_THEMES, PIECE_THEMES, DIFFICULTIES
)
from piece_renderer import PieceRenderer, PIECE_CHARS
from game_logic import (
    ChessGame,
    STATUS_IN_PROGRESS, STATUS_CHECKMATE, STATUS_STALEMATE,
    STATUS_DRAW_INSUFFICIENT, STATUS_DRAW_FIFTY_MOVES, STATUS_DRAW_REPETITION,
    STATUS_RESIGNED, STATUS_DRAW_AGREED
)


# =====================================================================
# UI WIDGETS
# =====================================================================

class Button:
    """A sleek rounded button with metallic gold accents, hover, and click states."""

    def __init__(self, rect: Tuple[int, int, int, int], text: str, font: pygame.font.Font,
                 callback: Optional[Callable] = None, variant="primary", icon=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.variant = variant  # 'primary', 'secondary', 'danger', 'gold', 'outline'
        self.icon = icon
        self.is_hovered = False
        self.is_pressed = False
        self.enabled = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.rect.collidepoint(event.pos):
                self.is_pressed = False
                if self.callback:
                    self.callback()
                return True
            self.is_pressed = False
        return False

    def draw(self, surface: pygame.Surface):
        # Color mapping based on variant and hover state
        if not self.enabled:
            bg_color = (35, 37, 45)
            border_color = (60, 65, 75)
            text_color = (100, 105, 120)
        elif self.variant == "gold":
            if self.is_pressed:
                bg_color = COLOR_GOLD_MUTED
                border_color = COLOR_GOLD_DARK
            elif self.is_hovered:
                bg_color = COLOR_GOLD_LIGHT
                border_color = COLOR_GOLD_PRIMARY
            else:
                bg_color = COLOR_GOLD_PRIMARY
                border_color = COLOR_GOLD_LIGHT
            text_color = COLOR_TEXT_DARK
        elif self.variant == "danger":
            if self.is_hovered:
                bg_color = (180, 45, 45)
                border_color = (235, 80, 80)
            else:
                bg_color = (120, 30, 30)
                border_color = (160, 40, 40)
            text_color = COLOR_TEXT_WHITE
        elif self.variant == "secondary":
            if self.is_hovered:
                bg_color = (48, 52, 65)
                border_color = COLOR_GOLD_PRIMARY
            else:
                bg_color = COLOR_PANEL_SURFACE
                border_color = COLOR_PANEL_BORDER
            text_color = COLOR_TEXT_WHITE
        else:  # 'primary'
            if self.is_hovered:
                bg_color = (42, 45, 58)
                border_color = COLOR_GOLD_LIGHT
                text_color = COLOR_TEXT_GOLD
            else:
                bg_color = (28, 30, 39)
                border_color = COLOR_GOLD_PRIMARY
                text_color = COLOR_TEXT_WHITE

        # Render rounded rectangle with drop shadow
        draw_rect = self.rect.copy()
        if self.is_pressed:
            draw_rect.y += 2

        # Outer subtle shadow
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(surface, (10, 10, 12), shadow_rect, border_radius=8)

        # Main button body
        pygame.draw.rect(surface, bg_color, draw_rect, border_radius=8)
        # Border
        border_width = 2 if self.is_hovered else 1
        pygame.draw.rect(surface, border_color, draw_rect, width=border_width, border_radius=8)

        # Render text
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)


class MoveAnimation:
    """Manages smooth piece interpolation between squares."""

    def __init__(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], piece_surf: pygame.Surface, duration=0.14):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece_surf = piece_surf
        self.duration = duration
        self.start_time = time.time()
        self.is_done = False

    def update(self) -> Tuple[int, int]:
        now = time.time()
        progress = (now - self.start_time) / self.duration
        if progress >= 1.0:
            self.is_done = True
            return self.to_pos

        # Ease-out cubic curve
        t = 1.0 - math.pow(1.0 - progress, 3)
        curr_x = self.from_pos[0] + (self.to_pos[0] - self.from_pos[0]) * t
        curr_y = self.from_pos[1] + (self.to_pos[1] - self.from_pos[1]) * t
        return int(curr_x), int(curr_y)


# =====================================================================
# MAIN USER INTERFACE SYSTEM
# =====================================================================

class ChessUI:
    """Handles graphics rendering, event processing, screens, and modals."""

    def __init__(self, screen: pygame.Surface, settings_manager, stats_manager, sound_manager):
        self.screen = screen
        self.settings = settings_manager
        self.stats = stats_manager
        self.sounds = sound_manager
        self.piece_renderer = PieceRenderer()
        self.piece_renderer.set_theme(self.settings.get("piece_theme", "Shadow Gold"))

        # Initialize Fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("segoe ui,helvetica,arial", 38, bold=True)
        self.font_heading = pygame.font.SysFont("segoe ui,helvetica,arial", 22, bold=True)
        self.font_body = pygame.font.SysFont("segoe ui,helvetica,arial", 16)
        self.font_bold = pygame.font.SysFont("segoe ui,helvetica,arial", 16, bold=True)
        self.font_small = pygame.font.SysFont("segoe ui,helvetica,arial", 13)
        self.font_coords = pygame.font.SysFont("segoe ui,arial", 12, bold=True)
        self.font_moves = pygame.font.SysFont("consolas,courier", 15)

        # Screens: 'MENU', 'GAME', 'SETTINGS', 'STATISTICS'
        self.current_screen = "MENU"
        self.game: Optional[ChessGame] = None

        # Drag-and-drop state
        self.dragging_square: Optional[int] = None
        self.drag_mouse_pos: Tuple[int, int] = (0, 0)

        # Piece movement animation
        self.active_animation: Optional[MoveAnimation] = None

        # Move history scroll offset
        self.history_scroll_y = 0

        # UI Modals & Confirmations
        self.show_confirm_reset = False
        self.game_over_dismissed = False

        # Build screen buttons
        self._init_menu_buttons()
        self._init_game_buttons()
        self._init_settings_buttons()
        self._init_stats_buttons()

    # -----------------------------------------------------------------
    # BUTTON INITIALIZATIONS
    # -----------------------------------------------------------------

    def _init_menu_buttons(self):
        cx = WINDOW_WIDTH // 2
        btn_w, btn_h = 320, 50
        start_y = 260
        gap = 65

        self.menu_buttons = [
            Button((cx - btn_w // 2, start_y, btn_w, btn_h), "PLAY VS COMPUTER", self.font_heading,
                   callback=lambda: self.start_new_game("PVE"), variant="gold"),
            Button((cx - btn_w // 2, start_y + gap, btn_w, btn_h), "LOCAL MULTIPLAYER", self.font_heading,
                   callback=lambda: self.start_new_game("PVP"), variant="primary"),
            Button((cx - btn_w // 2, start_y + gap * 2, btn_w, btn_h), "SETTINGS", self.font_heading,
                   callback=lambda: self.switch_screen("SETTINGS"), variant="secondary"),
            Button((cx - btn_w // 2, start_y + gap * 3, btn_w, btn_h), "STATISTICS", self.font_heading,
                   callback=lambda: self.switch_screen("STATISTICS"), variant="secondary"),
            Button((cx - btn_w // 2, start_y + gap * 4, btn_w, btn_h), "EXIT GAME", self.font_heading,
                   callback=self.quit_app, variant="danger")
        ]

    def _init_game_buttons(self):
        px = 730
        py = 720
        bw, bh = 95, 38
        gap = 105

        self.game_buttons = [
            Button((px, py, bw, bh), "Undo", self.font_bold, callback=self.on_undo_click, variant="secondary"),
            Button((px + gap, py, bw, bh), "Restart", self.font_bold, callback=self.on_restart_click, variant="secondary"),
            Button((px + gap * 2, py, bw, bh), "Draw", self.font_bold, callback=self.on_draw_click, variant="secondary"),
            Button((px + gap * 3, py, bw, bh), "Resign", self.font_bold, callback=self.on_resign_click, variant="danger"),
            Button((BOARD_OFFSET_X, 22, 130, 36), "← Main Menu", self.font_bold, callback=self.on_exit_to_menu, variant="secondary")
        ]

    def _init_settings_buttons(self):
        self.settings_back_btn = Button((BOARD_OFFSET_X, 30, 130, 40), "← Back", self.font_bold,
                                        callback=lambda: self.switch_screen("MENU"), variant="secondary")

    def _init_stats_buttons(self):
        self.stats_back_btn = Button((BOARD_OFFSET_X, 30, 130, 40), "← Back", self.font_bold,
                                     callback=lambda: self.switch_screen("MENU"), variant="secondary")
        self.stats_reset_btn = Button((WINDOW_WIDTH - 220, 30, 160, 40), "Reset Statistics", self.font_bold,
                                      callback=self.on_reset_stats_click, variant="danger")

    # -----------------------------------------------------------------
    # NAVIGATION & GAME FLOW
    # -----------------------------------------------------------------

    def switch_screen(self, screen_name: str):
        self.sounds.play("click")
        self.current_screen = screen_name
        self.show_confirm_reset = False

    def quit_app(self):
        self.sounds.play("click")
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def start_new_game(self, mode: str):
        self.sounds.play("game_start")
        player_color = self.settings.get("player_color", "White")
        ai_diff = self.settings.get("ai_difficulty", "Medium")
        
        self.game = ChessGame(mode=mode, player_color=player_color, ai_difficulty=ai_diff)
        self.current_screen = "GAME"
        self.game_over_dismissed = False
        self.history_scroll_y = 0
        self.active_animation = None
        self.dragging_square = None

        # If PvE and player chose Black, trigger initial AI move
        if mode == "PVE" and player_color == "Black":
            self.trigger_ai_move()

    def on_exit_to_menu(self):
        self.sounds.play("click")
        self.current_screen = "MENU"

    def on_undo_click(self):
        if not self.game or self.game.is_ai_thinking:
            return
        if self.game.undo_move():
            self.sounds.play("click")
            self.game_over_dismissed = False

    def on_restart_click(self):
        if not self.game or self.game.is_ai_thinking:
            return
        self.sounds.play("game_start")
        self.game.reset()
        self.game_over_dismissed = False
        self.history_scroll_y = 0
        if self.game.mode == "PVE" and self.game.player_color == "Black":
            self.trigger_ai_move()

    def on_resign_click(self):
        if not self.game or self.game.is_game_over() or self.game.is_ai_thinking:
            return
        self.sounds.play("click")
        current_resigner = self.game.turn_name
        self.game.resign(current_resigner)
        self._record_game_end()

    def on_draw_click(self):
        if not self.game or self.game.is_game_over() or self.game.is_ai_thinking:
            return
        self.sounds.play("click")
        accepted = self.game.offer_draw(self.game.turn_name)
        if accepted:
            self.sounds.play("draw")
            self._record_game_end()
        else:
            self.sounds.play("illegal")

    def on_reset_stats_click(self):
        self.sounds.play("click")
        self.stats.reset()

    # -----------------------------------------------------------------
    # EVENT HANDLING
    # -----------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        if self.current_screen == "MENU":
            for btn in self.menu_buttons:
                btn.handle_event(event)

        elif self.current_screen == "GAME":
            self._handle_game_event(event)

        elif self.current_screen == "SETTINGS":
            self._handle_settings_event(event)

        elif self.current_screen == "STATISTICS":
            self._handle_stats_event(event)

    def _handle_game_event(self, event: pygame.event.Event):
        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.game and self.game.pending_promotion:
                    self.game.cancel_promotion()
                else:
                    self.on_exit_to_menu()
                return
            elif event.key == pygame.K_u:
                self.on_undo_click()
                return
            elif event.key == pygame.K_r:
                self.on_restart_click()
                return

        # Game buttons
        for btn in self.game_buttons:
            if btn.handle_event(event):
                return

        if not self.game:
            return

        # Handle Promotion Dialog
        if self.game.pending_promotion:
            if self._handle_promotion_event(event):
                return

        # Handle Game Over Modal clicks
        if self.game.is_game_over() and not self.game_over_dismissed:
            if self._handle_game_over_modal_event(event):
                return

        # Mouse Wheel for Move History Scrolling
        if event.type == pygame.MOUSEWHEEL:
            history_rect = pygame.Rect(720, 180, 440, 360)
            if history_rect.collidepoint(pygame.mouse.get_pos()):
                self.history_scroll_y -= event.y * 24
                self.history_scroll_y = max(0, self.history_scroll_y)

        # Chessboard Mouse Interactions (Click-to-Move and Drag-and-Drop)
        if self.game.is_game_over() or self.game.is_ai_thinking or not self.game.is_player_turn():
            return

        board_rect = pygame.Rect(BOARD_OFFSET_X, BOARD_OFFSET_Y, BOARD_SIZE, BOARD_SIZE)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if board_rect.collidepoint(event.pos):
                sq = self._pos_to_square(event.pos)
                if sq is not None:
                    # If clicking an already selected square's legal target -> execute move
                    if self.game.selected_square is not None and sq in self.game.legal_targets:
                        self._attempt_player_move(self.game.selected_square, sq)
                    else:
                        # Attempt to select piece for click-to-move or start dragging
                        if self.game.select_square(sq):
                            self.dragging_square = sq
                            self.drag_mouse_pos = event.pos

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_square is not None:
                self.drag_mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_square is not None:
                release_sq = self._pos_to_square(event.pos)
                if release_sq is not None and release_sq in self.game.legal_targets:
                    # Drag and drop move executed!
                    self._attempt_player_move(self.dragging_square, release_sq)
                self.dragging_square = None

    def _handle_promotion_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check 4 promotion choices
            dialog_w, dialog_h = 360, 140
            dx = (WINDOW_WIDTH - dialog_w) // 2
            dy = (WINDOW_HEIGHT - dialog_h) // 2
            piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]

            for i, p_type in enumerate(piece_types):
                btn_rect = pygame.Rect(dx + 25 + i * 80, dy + 50, 68, 68)
                if btn_rect.collidepoint(event.pos):
                    from_sq, to_sq = self.game.pending_promotion
                    if self.game.complete_promotion(p_type):
                        self._on_move_completed(from_sq, to_sq)
                    return True
        return False

    def _handle_game_over_modal_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mw, mh = 420, 260
            mx = (WINDOW_WIDTH - mw) // 2
            my = (WINDOW_HEIGHT - mh) // 2

            # Play Again button
            play_again_rect = pygame.Rect(mx + 30, my + 180, 160, 45)
            if play_again_rect.collidepoint(event.pos):
                self.on_restart_click()
                return True

            # Main Menu button
            menu_rect = pygame.Rect(mx + 230, my + 180, 160, 45)
            if menu_rect.collidepoint(event.pos):
                self.on_exit_to_menu()
                return True

            # Dismiss / Review Board button (small 'x' or click outside)
            close_rect = pygame.Rect(mx + mw - 35, my + 15, 25, 25)
            if close_rect.collidepoint(event.pos):
                self.sounds.play("click")
                self.game_over_dismissed = True
                return True
        return False

    def _handle_settings_event(self, event: pygame.event.Event):
        self.settings_back_btn.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # 1. Sound toggle
            sound_rect = pygame.Rect(450, 140, 160, 36)
            if sound_rect.collidepoint(pos):
                self.settings.toggle("sound_enabled")
                self.sounds.update_volume()
                self.sounds.play("click")

            # 2. Animations toggle
            anim_rect = pygame.Rect(450, 200, 160, 36)
            if anim_rect.collidepoint(pos):
                self.settings.toggle("animations_enabled")
                self.sounds.play("click")

            # 3. Show legal moves toggle
            legal_rect = pygame.Rect(450, 260, 160, 36)
            if legal_rect.collidepoint(pos):
                self.settings.toggle("show_legal_moves")
                self.sounds.play("click")

            # 4. Board themes
            for i, theme_name in enumerate(BOARD_THEMES.keys()):
                theme_rect = pygame.Rect(450 + (i % 2) * 230, 320 + (i // 2) * 50, 210, 38)
                if theme_rect.collidepoint(pos):
                    self.settings.set("board_theme", theme_name)
                    self.sounds.play("click")

            # 5. Piece themes
            for i, p_theme in enumerate(PIECE_THEMES):
                p_rect = pygame.Rect(450 + i * 180, 460, 165, 38)
                if p_rect.collidepoint(pos):
                    self.settings.set("piece_theme", p_theme)
                    self.piece_renderer.set_theme(p_theme)
                    self.sounds.play("click")

            # 6. AI Difficulty
            for i, diff in enumerate(DIFFICULTIES):
                diff_rect = pygame.Rect(450 + i * 150, 540, 135, 38)
                if diff_rect.collidepoint(pos):
                    self.settings.set("ai_difficulty", diff)
                    self.sounds.play("click")

            # 7. Player Color
            for i, col in enumerate(["White", "Black"]):
                col_rect = pygame.Rect(450 + i * 150, 620, 135, 38)
                if col_rect.collidepoint(pos):
                    self.settings.set("player_color", col)
                    self.sounds.play("click")

    def _handle_stats_event(self, event: pygame.event.Event):
        self.stats_back_btn.handle_event(event)
        self.stats_reset_btn.handle_event(event)

    # -----------------------------------------------------------------
    # MOVE EXECUTION & AI INTEGRATION
    # -----------------------------------------------------------------

    def _attempt_player_move(self, from_sq: int, to_sq: int):
        """Attempts to execute a human player move."""
        # If pawn promotion is required, game logic triggers pending_promotion dialog
        if self.game.is_promotion(from_sq, to_sq):
            self.game.make_move(from_sq, to_sq)  # Sets pending_promotion
            return

        is_capture = self.game.board.is_capture(chess.Move(from_sq, to_sq))
        if self.game.make_move(from_sq, to_sq):
            self._on_move_completed(from_sq, to_sq, is_capture)

    def _on_move_completed(self, from_sq: int, to_sq: int, was_capture: bool = False):
        """Handles post-move animations, sound triggers, and AI turn scheduling."""
        # Start piece animation if enabled
        if self.settings.get("animations_enabled", True):
            from_pos = self._square_to_pos(from_sq)
            to_pos = self._square_to_pos(to_sq)
            piece = self.game.board.piece_at(to_sq)
            if piece:
                piece_surf = self.piece_renderer.get_piece_surface(piece.piece_type, piece.color, SQUARE_SIZE)
                self.active_animation = MoveAnimation(from_pos, to_pos, piece_surf)

        # Sound effects
        if self.game.status == STATUS_CHECKMATE:
            self.sounds.play("checkmate")
            self._record_game_end()
        elif self.game.is_game_over():
            self.sounds.play("draw")
            self._record_game_end()
        elif self.game.board.is_check():
            self.sounds.play("check")
        elif was_capture:
            self.sounds.play("capture")
        else:
            self.sounds.play("move")

        # In PvE mode, trigger AI response if game continues and it's AI's turn
        if self.game.mode == "PVE" and not self.game.is_game_over() and not self.game.is_player_turn():
            self.trigger_ai_move()

    def trigger_ai_move(self):
        """Dispatches AI move search asynchronously in a background thread."""
        if not self.game or self.game.is_ai_thinking or self.game.is_game_over():
            return

        self.game.is_ai_thinking = True
        from chess_ai import ChessAIWorker
        worker = ChessAIWorker()

        def on_ai_complete(best_move: Optional[chess.Move]):
            # Callback executed when AI completes
            if not best_move or not self.game:
                if self.game:
                    self.game.is_ai_thinking = False
                return

            from_sq = best_move.from_square
            to_sq = best_move.to_square
            is_capture = self.game.board.is_capture(best_move)
            promotion = best_move.promotion

            self.game.is_ai_thinking = False
            if self.game.make_move(from_sq, to_sq, promotion_piece=promotion):
                self._on_move_completed(from_sq, to_sq, is_capture)

        worker.start_search(self.game.board.fen(), self.game.ai_difficulty, on_ai_complete)

    def _record_game_end(self):
        """Records completed match results to statistics."""
        if not self.game or not self.game.is_game_over():
            return

        if self.game.mode == "PVE":
            # Determine outcome from player's perspective
            player_is_white = (self.game.player_color == "White")
            if self.game.winner == "White":
                res = "win" if player_is_white else "loss"
            elif self.game.winner == "Black":
                res = "loss" if player_is_white else "win"
            else:
                res = "draw"
            self.stats.record_pve_game(res, self.game.ai_difficulty)
        else:
            # PvP
            self.stats.record_pvp_game(self.game.winner or "Draw")

    # -----------------------------------------------------------------
    # COORDINATE CONVERSIONS
    # -----------------------------------------------------------------

    def _square_to_pos(self, square: int) -> Tuple[int, int]:
        """Maps chess.Square (0..63) to top-left pixel coordinates (x, y)."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        # If player is Black in PvE, flip board orientation
        flip = (self.game and self.game.mode == "PVE" and self.game.player_color == "Black")
        f = (7 - file) if flip else file
        r = rank if flip else (7 - rank)
        x = BOARD_OFFSET_X + f * SQUARE_SIZE
        y = BOARD_OFFSET_Y + r * SQUARE_SIZE
        return x, y

    def _pos_to_square(self, pos: Tuple[int, int]) -> Optional[int]:
        """Maps pixel coordinate (x, y) to chess.Square (0..63), or None."""
        x, y = pos
        if not (BOARD_OFFSET_X <= x < BOARD_OFFSET_X + BOARD_SIZE and BOARD_OFFSET_Y <= y < BOARD_OFFSET_Y + BOARD_SIZE):
            return None
        f = (x - BOARD_OFFSET_X) // SQUARE_SIZE
        r = (y - BOARD_OFFSET_Y) // SQUARE_SIZE
        flip = (self.game and self.game.mode == "PVE" and self.game.player_color == "Black")
        file = (7 - f) if flip else f
        rank = r if flip else (7 - r)
        return chess.square(file, rank)

    # -----------------------------------------------------------------
    # RENDERING LOOP
    # -----------------------------------------------------------------

    def draw(self):
        """Primary screen render dispatcher."""
        self.screen.fill(COLOR_BG_DARK)

        if self.current_screen == "MENU":
            self._draw_main_menu()
        elif self.current_screen == "GAME":
            self._draw_game_screen()
        elif self.current_screen == "SETTINGS":
            self._draw_settings_screen()
        elif self.current_screen == "STATISTICS":
            self._draw_statistics_screen()

    # -----------------------------------------------------------------
    # MAIN MENU SCREEN
    # -----------------------------------------------------------------

    def _draw_main_menu(self):
        cx = WINDOW_WIDTH // 2

        # Title Card with Gold Glow
        title_surf = self.font_title.render("SHADOW CHESS", True, COLOR_GOLD_LIGHT)
        title_rect = title_surf.get_rect(center=(cx, 130))

        # Title Glow halo
        glow_surf = self.font_title.render("SHADOW CHESS", True, COLOR_GOLD_PRIMARY)
        self.screen.blit(glow_surf, title_rect.move(1, 1))
        self.screen.blit(title_surf, title_rect)

        # Elegant Subtitle
        sub_surf = self.font_body.render("THE MASTER'S BOARD • PREMIUM OFFLINE CHESS", True, COLOR_TEXT_MUTED)
        sub_rect = sub_surf.get_rect(center=(cx, 175))
        self.screen.blit(sub_surf, sub_rect)

        # Gold decorative divider line
        line_w = 400
        pygame.draw.line(self.screen, COLOR_GOLD_PRIMARY, (cx - line_w // 2, 205), (cx + line_w // 2, 205), width=2)
        pygame.draw.circle(self.screen, COLOR_GOLD_LIGHT, (cx, 205), 4)

        # Draw Buttons
        for btn in self.menu_buttons:
            btn.draw(self.screen)

        # Footer
        footer_surf = self.font_small.render("Shadow Chess v1.0 • Pure Offline Desktop Edition", True, (80, 85, 100))
        footer_rect = footer_surf.get_rect(center=(cx, WINDOW_HEIGHT - 35))
        self.screen.blit(footer_surf, footer_rect)

    # -----------------------------------------------------------------
    # GAME SCREEN
    # -----------------------------------------------------------------

    def _draw_game_screen(self):
        if not self.game:
            return

        # Top Bar
        self._draw_top_bar()

        # Chessboard
        self._draw_board()

        # Side Panel (Right)
        self._draw_side_panel()

        # Modals
        if self.game.pending_promotion:
            self._draw_promotion_modal()

        if self.game.is_game_over() and not self.game_over_dismissed:
            self._draw_game_over_modal()

    def _draw_top_bar(self):
        # Back to Main Menu button
        self.game_buttons[4].draw(self.screen)

        # Mode and Difficulty Badge
        mode_str = f"PLAYER VS AI • {self.game.ai_difficulty.upper()}" if self.game.mode == "PVE" else "LOCAL MULTIPLAYER"
        badge_surf = self.font_bold.render(mode_str, True, COLOR_GOLD_PRIMARY)
        self.screen.blit(badge_surf, (200, 28))

        # Current Turn Indicator Pill
        turn_text = f"{self.game.turn_name}'s Turn"
        if self.game.is_ai_thinking:
            turn_text = f"AI Thinking... ({self.game.turn_name})"

        pill_rect = pygame.Rect(WINDOW_WIDTH - 300, 20, 240, 40)
        pygame.draw.rect(self.screen, COLOR_PANEL_SURFACE, pill_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_GOLD_PRIMARY if not self.game.is_ai_thinking else (80, 160, 240),
                         pill_rect, width=2, border_radius=20)

        # Turn color dot
        dot_color = (245, 245, 250) if self.game.board.turn == chess.WHITE else (25, 25, 30)
        dot_x, dot_y = pill_rect.x + 24, pill_rect.centery
        pygame.draw.circle(self.screen, (212, 175, 55), (dot_x, dot_y), 9)
        pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y), 7)

        # Turn text
        txt_surf = self.font_bold.render(turn_text, True, COLOR_TEXT_WHITE)
        self.screen.blit(txt_surf, (dot_x + 18, pill_rect.centery - txt_surf.get_height() // 2))

    def _draw_board(self):
        theme_name = self.settings.get("board_theme", "Midnight Gold")
        theme = BOARD_THEMES.get(theme_name, BOARD_THEMES["Midnight Gold"])

        # Outer Board Frame
        frame_rect = pygame.Rect(BOARD_OFFSET_X - 6, BOARD_OFFSET_Y - 6, BOARD_SIZE + 12, BOARD_SIZE + 12)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, frame_rect, border_radius=6)
        pygame.draw.rect(self.screen, theme["border_color"], frame_rect, width=2, border_radius=6)

        flip = (self.game.mode == "PVE" and self.game.player_color == "Black")

        # 1. Draw Squares
        for file in range(8):
            for rank in range(8):
                sq = chess.square(file, rank)
                f = (7 - file) if flip else file
                r = rank if flip else (7 - rank)
                x = BOARD_OFFSET_X + f * SQUARE_SIZE
                y = BOARD_OFFSET_Y + r * SQUARE_SIZE
                sq_rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)

                # Base square color
                is_light = (file + rank) % 2 != 0
                color = theme["light_square"] if is_light else theme["dark_square"]
                pygame.draw.rect(self.screen, color, sq_rect)

                # Coordinate labels on edges
                if f == 0:  # Rank label on left edge
                    lbl = str(rank + 1)
                    lbl_surf = self.font_coords.render(lbl, True, theme["border_color"])
                    self.screen.blit(lbl_surf, (x + 4, y + 4))
                if r == 7:  # File label on bottom edge
                    lbl = chr(ord('a') + file)
                    lbl_surf = self.font_coords.render(lbl, True, theme["border_color"])
                    self.screen.blit(lbl_surf, (x + SQUARE_SIZE - 12, y + SQUARE_SIZE - 16))

        # 2. Highlights Layer (Last Move, Check, Selected)
        # Last Move Highlight
        if self.settings.get("show_last_move", True) and self.game.last_move:
            from_sq, to_sq = self.game.last_move
            for sq in [from_sq, to_sq]:
                x, y = self._square_to_pos(sq)
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill(COLOR_LAST_MOVE)
                self.screen.blit(s, (x, y))

        # King in Check Glow
        king_check_sq = self.game.get_king_square_in_check()
        if king_check_sq is not None:
            kx, ky = self._square_to_pos(king_check_sq)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(COLOR_CHECK)
            self.screen.blit(s, (kx, ky))
            # Glowing border
            pygame.draw.rect(self.screen, (240, 50, 50), (kx, ky, SQUARE_SIZE, SQUARE_SIZE), width=3)

        # Selected Square Highlight
        if self.game.selected_square is not None:
            sx, sy = self._square_to_pos(self.game.selected_square)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(COLOR_SELECTED)
            self.screen.blit(s, (sx, sy))
            pygame.draw.rect(self.screen, COLOR_GOLD_LIGHT, (sx, sy, SQUARE_SIZE, SQUARE_SIZE), width=3)

        # 3. Draw Pieces (excluding dragged or currently animating piece)
        anim_moving_sq = None
        if self.active_animation and not self.active_animation.is_done:
            anim_moving_sq = self.game.last_move[1] if self.game.last_move else None

        for sq in range(64):
            if sq == self.dragging_square or sq == anim_moving_sq:
                continue

            piece = self.game.board.piece_at(sq)
            if piece:
                px, py = self._square_to_pos(sq)
                p_surf = self.piece_renderer.get_piece_surface(piece.piece_type, piece.color, SQUARE_SIZE)
                self.screen.blit(p_surf, (px, py))

        # 4. Legal Move Markers
        if self.settings.get("show_legal_moves", True) and self.game.selected_square is not None:
            for target_sq in self.game.legal_targets:
                tx, ty = self._square_to_pos(target_sq)
                target_piece = self.game.board.piece_at(target_sq)

                if target_piece:
                    # Enemy piece capture ring
                    cx, cy = tx + SQUARE_SIZE // 2, ty + SQUARE_SIZE // 2
                    pygame.draw.circle(self.screen, (235, 75, 75), (cx, cy), SQUARE_SIZE // 2 - 4, width=4)
                else:
                    # Empty square legal dot
                    cx, cy = tx + SQUARE_SIZE // 2, ty + SQUARE_SIZE // 2
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    pygame.draw.circle(s, COLOR_LEGAL_DOT, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), 11)
                    self.screen.blit(s, (tx, ty))

        # 5. Sliding Animation
        if self.active_animation and not self.active_animation.is_done:
            curr_pos = self.active_animation.update()
            self.screen.blit(self.active_animation.piece_surf, curr_pos)
            if self.active_animation.is_done:
                self.active_animation = None

        # 6. Dragged Piece (rendered above board centered at cursor)
        if self.dragging_square is not None:
            drag_piece = self.game.board.piece_at(self.dragging_square)
            if drag_piece:
                p_surf = self.piece_renderer.get_piece_surface(drag_piece.piece_type, drag_piece.color, SQUARE_SIZE)
                mx, my = self.drag_mouse_pos
                self.screen.blit(p_surf, (mx - SQUARE_SIZE // 2, my - SQUARE_SIZE // 2))

    # -----------------------------------------------------------------
    # SIDE PANEL (Right Side)
    # -----------------------------------------------------------------

    def _draw_side_panel(self):
        panel_x = 720
        panel_w = 440

        # Background card
        panel_rect = pygame.Rect(panel_x, BOARD_OFFSET_Y - 6, panel_w, BOARD_SIZE + 12)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, width=1, border_radius=8)

        # 1. Opponent Card (Top)
        opp_color_name = "Black" if self.game.player_color == "White" else "White"
        opp_title = f"Shadow AI ({self.game.ai_difficulty})" if self.game.mode == "PVE" else f"Player 2 ({opp_color_name})"
        self._draw_player_card(panel_x + 15, BOARD_OFFSET_Y + 10, panel_w - 30, 80,
                               opp_title, opp_color_name == "White", is_top=True)

        # 2. Move History Table (Center)
        self._draw_move_history_card(panel_x + 15, BOARD_OFFSET_Y + 105, panel_w - 30, 480)

        # 3. Player Card (Bottom)
        player_title = f"Player ({self.game.player_color})" if self.game.mode == "PVE" else f"Player 1 ({self.game.player_color})"
        self._draw_player_card(panel_x + 15, BOARD_OFFSET_Y + 595, panel_w - 30, 80,
                               player_title, self.game.player_color == "White", is_top=False)

        # 4. Control Buttons (Undo, Restart, Draw, Resign)
        for i in range(4):
            self.game_buttons[i].draw(self.screen)

    def _draw_player_card(self, x: int, y: int, w: int, h: int, name: str, is_white: bool, is_top: bool):
        card_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, COLOR_PANEL_SURFACE, card_rect, border_radius=6)
        
        # Active turn border glow
        is_active = (self.game.board.turn == (chess.WHITE if is_white else chess.BLACK))
        border_col = COLOR_GOLD_PRIMARY if is_active else COLOR_PANEL_BORDER
        pygame.draw.rect(self.screen, border_col, card_rect, width=2 if is_active else 1, border_radius=6)

        # Avatar circle
        av_x, av_y = x + 35, y + h // 2
        pygame.draw.circle(self.screen, COLOR_GOLD_PRIMARY, (av_x, av_y), 22, width=2)
        av_fill = (245, 245, 250) if is_white else (25, 25, 32)
        pygame.draw.circle(self.screen, av_fill, (av_x, av_y), 19)

        # King symbol in avatar
        k_char = "♔" if is_white else "♚"
        try:
            sym_surf = self.font_heading.render(k_char, True, (212, 175, 55))
            self.screen.blit(sym_surf, sym_surf.get_rect(center=(av_x, av_y - 2)))
        except Exception:
            pass

        # Player Name
        name_surf = self.font_bold.render(name, True, COLOR_TEXT_WHITE)
        self.screen.blit(name_surf, (x + 70, y + 14))

        # Captured Pieces Tray & Material Advantage
        captured_list = self.game.captured_black if is_white else self.game.captured_white
        mat = self.game.get_material_advantage()
        diff = mat["difference"] if is_white else -mat["difference"]

        tray_x = x + 70
        tray_y = y + 42
        icon_size = 22

        # Draw mini icons of captured pieces
        for i, p_type in enumerate(captured_list[-12:]):  # show up to last 12
            # Render opposite color piece
            p_surf = self.piece_renderer.get_piece_surface(p_type, not is_white, icon_size)
            self.screen.blit(p_surf, (tray_x + i * 16, tray_y))

        # Show material score badge (+3, +5, etc.)
        if diff > 0:
            diff_surf = self.font_small.render(f"+{diff}", True, COLOR_GOLD_LIGHT)
            self.screen.blit(diff_surf, (x + w - 45, y + 15))

    def _draw_move_history_card(self, x: int, y: int, w: int, h: int):
        card_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, COLOR_PANEL_SURFACE, card_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, card_rect, width=1, border_radius=6)

        # Header Row
        pygame.draw.rect(self.screen, (20, 22, 28), (x, y, w, 32), border_top_left_radius=6, border_top_right_radius=6)
        hdr_surf = self.font_small.render("  #     WHITE                  BLACK", True, COLOR_GOLD_PRIMARY)
        self.screen.blit(hdr_surf, (x + 10, y + 8))

        # Move list clipping area
        clip_rect = pygame.Rect(x + 5, y + 36, w - 10, h - 42)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip_rect)

        moves = self.game.get_formatted_move_history()
        row_h = 24
        total_content_h = len(moves) * row_h

        # Auto scroll to bottom when new move made
        max_scroll = max(0, total_content_h - (h - 42))
        if self.history_scroll_y > max_scroll:
            self.history_scroll_y = max_scroll

        for idx, (turn_num, w_san, b_san) in enumerate(moves):
            row_y = y + 38 + idx * row_h - self.history_scroll_y
            if row_y + row_h < y + 36 or row_y > y + h:
                continue

            # Row background alternation
            if idx % 2 == 1:
                pygame.draw.rect(self.screen, (28, 30, 38), (x + 8, row_y, w - 16, row_h - 2), border_radius=4)

            # Move text
            num_surf = self.font_moves.render(f"{turn_num}.", True, COLOR_TEXT_MUTED)
            self.screen.blit(num_surf, (x + 15, row_y + 2))

            w_surf = self.font_moves.render(w_san, True, COLOR_TEXT_WHITE)
            self.screen.blit(w_surf, (x + 65, row_y + 2))

            if b_san:
                b_surf = self.font_moves.render(b_san, True, COLOR_TEXT_WHITE)
                self.screen.blit(b_surf, (x + 220, row_y + 2))

        self.screen.set_clip(old_clip)

    # -----------------------------------------------------------------
    # MODALS & OVERLAYS
    # -----------------------------------------------------------------

    def _draw_promotion_modal(self):
        """Pawn Promotion Piece Selection Dialog."""
        # Backdrop dimming
        dim_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 180))
        self.screen.blit(dim_surf, (0, 0))

        dialog_w, dialog_h = 380, 160
        dx = (WINDOW_WIDTH - dialog_w) // 2
        dy = (WINDOW_HEIGHT - dialog_h) // 2
        d_rect = pygame.Rect(dx, dy, dialog_w, dialog_h)

        # Dialog box
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, d_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GOLD_PRIMARY, d_rect, width=2, border_radius=10)

        # Title
        title_surf = self.font_bold.render("PAWN PROMOTION — CHOOSE PIECE", True, COLOR_GOLD_LIGHT)
        self.screen.blit(title_surf, title_surf.get_rect(center=(dx + dialog_w // 2, dy + 25)))

        # 4 Interactive Piece Options
        p_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        is_white = self.game.board.turn == chess.WHITE
        mouse_pos = pygame.mouse.get_pos()

        for i, p_type in enumerate(p_types):
            bx = dx + 25 + i * 85
            by = dy + 55
            b_rect = pygame.Rect(bx, by, 72, 72)
            hover = b_rect.collidepoint(mouse_pos)

            # Option card
            bg_col = (45, 48, 62) if hover else COLOR_PANEL_SURFACE
            border_col = COLOR_GOLD_LIGHT if hover else COLOR_PANEL_BORDER
            pygame.draw.rect(self.screen, bg_col, b_rect, border_radius=8)
            pygame.draw.rect(self.screen, border_col, b_rect, width=2 if hover else 1, border_radius=8)

            # Piece icon
            p_surf = self.piece_renderer.get_piece_surface(p_type, is_white, 60)
            self.screen.blit(p_surf, (bx + 6, by + 6))

    def _draw_game_over_modal(self):
        """Game Over End Match Result Card."""
        dim_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 180))
        self.screen.blit(dim_surf, (0, 0))

        mw, mh = 440, 270
        mx = (WINDOW_WIDTH - mw) // 2
        my = (WINDOW_HEIGHT - mh) // 2
        m_rect = pygame.Rect(mx, my, mw, mh)

        # Box
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, m_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_GOLD_PRIMARY, m_rect, width=2, border_radius=12)

        # Result Banner
        if self.game.winner == "White":
            banner = "VICTORY FOR WHITE"
            banner_col = COLOR_GOLD_LIGHT
        elif self.game.winner == "Black":
            banner = "VICTORY FOR BLACK"
            banner_col = COLOR_GOLD_LIGHT
        else:
            banner = "GAME DRAW"
            banner_col = COLOR_DRAW

        banner_surf = self.font_title.render(banner, True, banner_col)
        self.screen.blit(banner_surf, banner_surf.get_rect(center=(mx + mw // 2, my + 50)))

        # Reason description
        reason_surf = self.font_body.render(self.game.status_message, True, COLOR_TEXT_WHITE)
        self.screen.blit(reason_surf, reason_surf.get_rect(center=(mx + mw // 2, my + 105)))

        # Move count summary
        total_moves = len(self.game.move_history)
        moves_surf = self.font_small.render(f"Total Moves: {total_moves} plies", True, COLOR_TEXT_MUTED)
        self.screen.blit(moves_surf, moves_surf.get_rect(center=(mx + mw // 2, my + 135)))

        # Buttons (Play Again, Main Menu)
        play_btn = Button((mx + 40, my + 180, 160, 48), "PLAY AGAIN", self.font_bold,
                          callback=self.on_restart_click, variant="gold")
        menu_btn = Button((mx + 240, my + 180, 160, 48), "MAIN MENU", self.font_bold,
                          callback=self.on_exit_to_menu, variant="secondary")

        play_btn.draw(self.screen)
        menu_btn.draw(self.screen)

        # Close 'x' button in corner
        x_surf = self.font_bold.render("✕", True, COLOR_TEXT_MUTED)
        self.screen.blit(x_surf, (mx + mw - 28, my + 12))

    # -----------------------------------------------------------------
    # SETTINGS SCREEN
    # -----------------------------------------------------------------

    def _draw_settings_screen(self):
        self.settings_back_btn.draw(self.screen)

        cx = WINDOW_WIDTH // 2
        title_surf = self.font_title.render("SETTINGS", True, COLOR_GOLD_LIGHT)
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, 60)))

        # Settings Card Container
        card_w, card_h = 760, 580
        card_rect = pygame.Rect(cx - card_w // 2, 110, card_w, card_h)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, card_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, card_rect, width=1, border_radius=10)

        lx = card_rect.x + 40
        rx = card_rect.x + 280

        # Helper for toggle buttons
        def draw_toggle(y, label, key):
            lbl_surf = self.font_heading.render(label, True, COLOR_TEXT_WHITE)
            self.screen.blit(lbl_surf, (lx, y + 4))
            val = self.settings.get(key, True)
            t_rect = pygame.Rect(rx, y, 140, 36)
            col = COLOR_GOLD_PRIMARY if val else COLOR_PANEL_SURFACE
            txt_col = COLOR_TEXT_DARK if val else COLOR_TEXT_MUTED
            pygame.draw.rect(self.screen, col, t_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_GOLD_LIGHT if val else COLOR_PANEL_BORDER, t_rect, width=1, border_radius=6)
            txt_surf = self.font_bold.render("ENABLED" if val else "DISABLED", True, txt_col)
            self.screen.blit(txt_surf, txt_surf.get_rect(center=t_rect.center))

        # Helper for choice pills
        def draw_choices(y, label, options, current_val):
            lbl_surf = self.font_heading.render(label, True, COLOR_TEXT_WHITE)
            self.screen.blit(lbl_surf, (lx, y + 4))

        # 1. Sound Effects Toggle
        draw_toggle(140, "Sound Effects", "sound_enabled")

        # 2. Animations Toggle
        draw_toggle(200, "Smooth Animations", "animations_enabled")

        # 3. Show Legal Moves
        draw_toggle(260, "Show Legal Moves", "show_legal_moves")

        # 4. Board Themes
        draw_choices(330, "Board Theme", list(BOARD_THEMES.keys()), self.settings.get("board_theme"))
        curr_b_theme = self.settings.get("board_theme")
        for i, theme_name in enumerate(BOARD_THEMES.keys()):
            bx = rx + (i % 2) * 210
            by = 320 + (i // 2) * 48
            b_rect = pygame.Rect(bx, by, 195, 38)
            selected = (theme_name == curr_b_theme)
            col = COLOR_GOLD_PRIMARY if selected else COLOR_PANEL_SURFACE
            t_col = COLOR_TEXT_DARK if selected else COLOR_TEXT_WHITE
            pygame.draw.rect(self.screen, col, b_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_GOLD_LIGHT if selected else COLOR_PANEL_BORDER, b_rect, width=1, border_radius=6)
            s = self.font_bold.render(theme_name, True, t_col)
            self.screen.blit(s, s.get_rect(center=b_rect.center))

        # 5. Piece Styles
        draw_choices(440, "Piece Style", PIECE_THEMES, self.settings.get("piece_theme"))
        curr_p_theme = self.settings.get("piece_theme")
        for i, p_theme in enumerate(PIECE_THEMES):
            bx = rx + i * 155
            by = 440
            b_rect = pygame.Rect(bx, by, 145, 38)
            selected = (p_theme == curr_p_theme)
            col = COLOR_GOLD_PRIMARY if selected else COLOR_PANEL_SURFACE
            t_col = COLOR_TEXT_DARK if selected else COLOR_TEXT_WHITE
            pygame.draw.rect(self.screen, col, b_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_GOLD_LIGHT if selected else COLOR_PANEL_BORDER, b_rect, width=1, border_radius=6)
            s = self.font_bold.render(p_theme, True, t_col)
            self.screen.blit(s, s.get_rect(center=b_rect.center))

        # 6. Default AI Difficulty
        draw_choices(510, "AI Difficulty", DIFFICULTIES, self.settings.get("ai_difficulty"))
        curr_diff = self.settings.get("ai_difficulty")
        for i, diff in enumerate(DIFFICULTIES):
            bx = rx + i * 155
            by = 510
            b_rect = pygame.Rect(bx, by, 145, 38)
            selected = (diff == curr_diff)
            col = COLOR_GOLD_PRIMARY if selected else COLOR_PANEL_SURFACE
            t_col = COLOR_TEXT_DARK if selected else COLOR_TEXT_WHITE
            pygame.draw.rect(self.screen, col, b_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_GOLD_LIGHT if selected else COLOR_PANEL_BORDER, b_rect, width=1, border_radius=6)
            s = self.font_bold.render(diff, True, t_col)
            self.screen.blit(s, s.get_rect(center=b_rect.center))

        # 7. Player Color
        draw_choices(580, "Player Color", ["White", "Black"], self.settings.get("player_color"))
        curr_col = self.settings.get("player_color")
        for i, col_name in enumerate(["White", "Black"]):
            bx = rx + i * 155
            by = 580
            b_rect = pygame.Rect(bx, by, 145, 38)
            selected = (col_name == curr_col)
            col = COLOR_GOLD_PRIMARY if selected else COLOR_PANEL_SURFACE
            t_col = COLOR_TEXT_DARK if selected else COLOR_TEXT_WHITE
            pygame.draw.rect(self.screen, col, b_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_GOLD_LIGHT if selected else COLOR_PANEL_BORDER, b_rect, width=1, border_radius=6)
            s = self.font_bold.render(col_name, True, t_col)
            self.screen.blit(s, s.get_rect(center=b_rect.center))

    # -----------------------------------------------------------------
    # STATISTICS SCREEN
    # -----------------------------------------------------------------

    def _draw_statistics_screen(self):
        self.stats_back_btn.draw(self.screen)
        self.stats_reset_btn.draw(self.screen)

        cx = WINDOW_WIDTH // 2
        title_surf = self.font_title.render("MATCH RECORDS & STATISTICS", True, COLOR_GOLD_LIGHT)
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, 60)))

        summary = self.stats.get_summary()

        # Top Overview Cards (Total, Wins, Losses, Draws, Win Rate)
        metrics = [
            ("TOTAL GAMES", str(summary.get("total_games", 0)), COLOR_TEXT_WHITE),
            ("WINS", str(summary.get("wins", 0)), COLOR_WIN),
            ("LOSSES", str(summary.get("losses", 0)), COLOR_LOSS),
            ("DRAWS", str(summary.get("draws", 0)), COLOR_DRAW),
            ("WIN RATE", f"{summary.get('win_percentage', 0.0)}%", COLOR_GOLD_LIGHT)
        ]

        card_w = 195
        card_h = 100
        start_x = (WINDOW_WIDTH - (len(metrics) * card_w + (len(metrics) - 1) * 20)) // 2

        for i, (label, val, val_col) in enumerate(metrics):
            bx = start_x + i * (card_w + 20)
            by = 120
            c_rect = pygame.Rect(bx, by, card_w, card_h)
            pygame.draw.rect(self.screen, COLOR_PANEL_BG, c_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, c_rect, width=1, border_radius=8)

            lbl_surf = self.font_small.render(label, True, COLOR_TEXT_MUTED)
            self.screen.blit(lbl_surf, lbl_surf.get_rect(center=(bx + card_w // 2, by + 28)))

            val_surf = self.font_title.render(val, True, val_col)
            self.screen.blit(val_surf, val_surf.get_rect(center=(bx + card_w // 2, by + 68)))

        # Detailed Breakdown Containers
        # 1. PvE AI Difficulty Performance
        pve_rect = pygame.Rect(start_x, 260, 520, 440)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, pve_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, pve_rect, width=1, border_radius=8)

        pve_title = self.font_heading.render("VS COMPUTER (AI) BREAKDOWN", True, COLOR_GOLD_PRIMARY)
        self.screen.blit(pve_title, (start_x + 25, 280))

        pve_data = summary.get("pve", {})
        diff_order = ["Easy", "Medium", "Hard"]
        for idx, diff in enumerate(diff_order):
            dy = 340 + idx * 110
            d_info = pve_data.get(diff, {})
            d_games = d_info.get("games", 0)
            d_wins = d_info.get("wins", 0)
            d_losses = d_info.get("losses", 0)
            d_draws = d_info.get("draws", 0)
            rate = round((d_wins / d_games) * 100.0, 1) if d_games > 0 else 0.0

            # Row container
            r_rect = pygame.Rect(start_x + 20, dy, 480, 85)
            pygame.draw.rect(self.screen, COLOR_PANEL_SURFACE, r_rect, border_radius=6)

            d_name = self.font_bold.render(f"{diff.upper()} DIFFICULTY", True, COLOR_TEXT_WHITE)
            self.screen.blit(d_name, (r_rect.x + 20, r_rect.y + 16))

            rate_text = self.font_bold.render(f"Win Rate: {rate}%", True, COLOR_GOLD_LIGHT)
            self.screen.blit(rate_text, (r_rect.right - 150, r_rect.y + 16))

            stats_str = f"Matches: {d_games}   •   Wins: {d_wins}   •   Losses: {d_losses}   •   Draws: {d_draws}"
            st_surf = self.font_small.render(stats_str, True, COLOR_TEXT_MUTED)
            self.screen.blit(st_surf, (r_rect.x + 20, r_rect.y + 50))

        # 2. Local PvP Match Records
        pvp_rect = pygame.Rect(start_x + 550, 260, 505, 440)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, pvp_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, pvp_rect, width=1, border_radius=8)

        pvp_title = self.font_heading.render("LOCAL MULTIPLAYER (PVP)", True, COLOR_GOLD_PRIMARY)
        self.screen.blit(pvp_title, (start_x + 575, 280))

        pvp_data = summary.get("pvp", {})
        pvp_items = [
            ("Total PvP Matches", str(pvp_data.get("games", 0))),
            ("White Victories", str(pvp_data.get("white_wins", 0))),
            ("Black Victories", str(pvp_data.get("black_wins", 0))),
            ("Stalemates & Draws", str(pvp_data.get("draws", 0)))
        ]

        for idx, (label, val_str) in enumerate(pvp_items):
            iy = 350 + idx * 75
            ir = pygame.Rect(start_x + 575, iy, 455, 55)
            pygame.draw.rect(self.screen, COLOR_PANEL_SURFACE, ir, border_radius=6)

            lbl = self.font_bold.render(label, True, COLOR_TEXT_WHITE)
            self.screen.blit(lbl, (ir.x + 20, ir.centery - lbl.get_height() // 2))

            v_surf = self.font_bold.render(val_str, True, COLOR_GOLD_LIGHT)
            self.screen.blit(v_surf, (ir.right - 45, ir.centery - v_surf.get_height() // 2))
