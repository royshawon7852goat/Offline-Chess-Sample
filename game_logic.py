"""
SHADOW CHESS - Game Logic Engine
Wraps python-chess with complete tournament rules, state tracking, and move history.
"""

import chess
from typing import List, Optional, Tuple, Dict

# Game Status Enums
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_CHECKMATE = "CHECKMATE"
STATUS_STALEMATE = "STALEMATE"
STATUS_DRAW_INSUFFICIENT = "DRAW_INSUFFICIENT_MATERIAL"
STATUS_DRAW_FIFTY_MOVES = "DRAW_FIFTY_MOVES"
STATUS_DRAW_REPETITION = "DRAW_REPETITION"
STATUS_RESIGNED = "RESIGNED"
STATUS_DRAW_AGREED = "DRAW_AGREED"

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}


class MoveRecord:
    """Stores detailed data for a played move."""
    def __init__(self, move: chess.Move, san: str, captured: Optional[chess.Piece] = None, is_check: bool = False):
        self.move = move
        self.san = san
        self.captured = captured
        self.is_check = is_check


class ChessGame:
    """Manages the chess board, move validations, captured pieces, and game conditions."""

    def __init__(self, mode="PVE", player_color="White", ai_difficulty="Medium"):
        self.mode = mode                     # 'PVE' or 'PVP'
        self.player_color = player_color     # 'White' or 'Black'
        self.ai_difficulty = ai_difficulty   # 'Easy', 'Medium', 'Hard'
        
        self.board = chess.Board()
        self.move_history: List[MoveRecord] = []
        self.captured_white: List[int] = []  # Pieces captured by black (were white)
        self.captured_black: List[int] = []  # Pieces captured by white (were black)
        
        self.selected_square: Optional[int] = None
        self.legal_targets: List[int] = []
        self.last_move: Optional[Tuple[int, int]] = None
        
        self.status = STATUS_IN_PROGRESS
        self.winner: Optional[str] = None  # 'White', 'Black', or 'Draw'
        self.status_message: str = "Game in progress."
        
        # Pending pawn promotion move waiting for user piece choice
        self.pending_promotion: Optional[Tuple[int, int]] = None
        
        # Flag if AI is currently calculating
        self.is_ai_thinking = False

    def reset(self):
        """Resets the game to initial state."""
        self.board.reset()
        self.move_history.clear()
        self.captured_white.clear()
        self.captured_black.clear()
        self.selected_square = None
        self.legal_targets.clear()
        self.last_move = None
        self.status = STATUS_IN_PROGRESS
        self.winner = None
        self.status_message = "Game in progress."
        self.pending_promotion = None
        self.is_ai_thinking = False

    @property
    def turn(self) -> chess.Color:
        return self.board.turn

    @property
    def turn_name(self) -> str:
        return "White" if self.board.turn == chess.WHITE else "Black"

    def is_player_turn(self) -> bool:
        """True if it is a human player's turn to act."""
        if self.mode == "PVP":
            return True
        # In PVE, check if current turn matches chosen player_color
        current = "White" if self.board.turn == chess.WHITE else "Black"
        return current == self.player_color

    def get_legal_moves_for_square(self, square: int) -> List[int]:
        """Returns all destination squares for legal moves starting at the given square."""
        if square is None:
            return []
        piece = self.board.piece_at(square)
        if not piece or piece.color != self.board.turn:
            return []
        
        targets = []
        for move in self.board.legal_moves:
            if move.from_square == square:
                targets.append(move.to_square)
        return list(set(targets))

    def select_square(self, square: int) -> bool:
        """Selects a square and computes legal destination targets."""
        if self.is_game_over() or self.is_ai_thinking:
            return False
            
        piece = self.board.piece_at(square)
        if piece and piece.color == self.board.turn:
            self.selected_square = square
            self.legal_targets = self.get_legal_moves_for_square(square)
            return True
        else:
            self.selected_square = None
            self.legal_targets.clear()
            return False

    def is_promotion(self, from_sq: int, to_sq: int) -> bool:
        """Checks if a move from from_sq to to_sq constitutes a pawn promotion."""
        piece = self.board.piece_at(from_sq)
        if not piece or piece.piece_type != chess.PAWN:
            return False
        dest_rank = chess.square_rank(to_sq)
        return (piece.color == chess.WHITE and dest_rank == 7) or (piece.color == chess.BLACK and dest_rank == 0)

    def make_move(self, from_sq: int, to_sq: int, promotion_piece: Optional[int] = None) -> bool:
        """
        Executes a move on the board if legal.
        If the move is a promotion and promotion_piece is None, sets pending_promotion and returns False.
        """
        if self.is_game_over() or self.is_ai_thinking:
            return False

        # Check for pawn promotion requirement
        if self.is_promotion(from_sq, to_sq):
            if promotion_piece is None:
                # Need user input for promotion
                self.pending_promotion = (from_sq, to_sq)
                return False
            else:
                move = chess.Move(from_sq, to_sq, promotion=promotion_piece)
        else:
            move = chess.Move(from_sq, to_sq)

        if move not in self.board.legal_moves:
            return False

        # Capture tracking
        captured_piece = self.board.piece_at(to_sq)
        # Handle en passant capture tracking
        if not captured_piece and self.board.is_en_passant(move):
            captured_sq = chess.square(chess.square_file(to_sq), chess.square_rank(from_sq))
            captured_piece = self.board.piece_at(captured_sq)

        if captured_piece:
            if captured_piece.color == chess.WHITE:
                self.captured_white.append(captured_piece.piece_type)
            else:
                self.captured_black.append(captured_piece.piece_type)

        # Generate SAN before pushing
        san = self.board.san(move)
        
        # Execute move
        self.board.push(move)
        self.last_move = (from_sq, to_sq)
        self.selected_square = None
        self.legal_targets.clear()
        self.pending_promotion = None

        # Record move
        record = MoveRecord(move, san, captured_piece, self.board.is_check())
        self.move_history.append(record)

        # Check end-game conditions
        self._update_game_status()
        return True

    def complete_promotion(self, promotion_piece: int) -> bool:
        """Completes a pending promotion with selected piece (Queen, Rook, Bishop, Knight)."""
        if not self.pending_promotion:
            return False
        from_sq, to_sq = self.pending_promotion
        return self.make_move(from_sq, to_sq, promotion_piece=promotion_piece)

    def cancel_promotion(self):
        """Cancels a pending promotion dialog."""
        self.pending_promotion = None
        self.selected_square = None
        self.legal_targets.clear()

    def undo_move(self) -> bool:
        """
        Undoes the last move(s).
        In PVE mode: undoes both the AI move and the player move so it's back to player's turn.
        In PVP mode: undoes single ply.
        """
        if self.is_ai_thinking or len(self.move_history) == 0:
            return False

        if self.mode == "PVE":
            # If AI just moved, undo both AI and player moves
            # But if game ended on player's move, undo 1 move
            current_is_player = self.is_player_turn()
            steps_to_undo = 2 if current_is_player and len(self.move_history) >= 2 else 1
        else:
            steps_to_undo = 1

        for _ in range(steps_to_undo):
            if len(self.move_history) == 0:
                break
            last_record = self.move_history.pop()
            self.board.pop()
            
            # Revert captured list
            if last_record.captured:
                if last_record.captured.color == chess.WHITE:
                    if self.captured_white:
                        self.captured_white.pop()
                else:
                    if self.captured_black:
                        self.captured_black.pop()

        # Update last move
        if self.move_history:
            prev = self.move_history[-1].move
            self.last_move = (prev.from_square, prev.to_square)
        else:
            self.last_move = None

        self.selected_square = None
        self.legal_targets.clear()
        self.pending_promotion = None
        self.status = STATUS_IN_PROGRESS
        self.winner = None
        self.status_message = "Game in progress."
        return True

    def resign(self, player_color: str):
        """Current player resigns."""
        if self.is_game_over() or self.is_ai_thinking:
            return
        self.status = STATUS_RESIGNED
        self.winner = "Black" if player_color == "White" else "White"
        self.status_message = f"{player_color} resigned. {self.winner} wins by resignation."

    def offer_draw(self, player_color: str) -> bool:
        """
        Offers a draw.
        In PVP: always accepted.
        In PVE: AI evaluates position; accepts if equal or losing, declines if winning.
        Returns True if accepted.
        """
        if self.is_game_over() or self.is_ai_thinking:
            return False

        if self.mode == "PVP":
            self.status = STATUS_DRAW_AGREED
            self.winner = "Draw"
            self.status_message = "Draw agreed by both players."
            return True
        else:
            # PVE: Check AI evaluation
            from chess_ai import evaluate_board
            # evaluate_board returns score from perspective of side to move (the player offering draw)
            player_eval = evaluate_board(self.board)

            # If player is winning by > 150 centipawns (1.5 pawns), AI happily accepts draw
            # If AI is winning (player_eval < -150), AI declines
            if player_eval < -150:
                return False
            else:
                self.status = STATUS_DRAW_AGREED
                self.winner = "Draw"
                self.status_message = "AI accepted the draw offer."
                return True

    def _update_game_status(self):
        """Updates internal status based on python-chess checks."""
        if self.board.is_checkmate():
            self.status = STATUS_CHECKMATE
            self.winner = "Black" if self.board.turn == chess.WHITE else "White"
            self.status_message = f"Checkmate! {self.winner} wins!"
        elif self.board.is_stalemate():
            self.status = STATUS_STALEMATE
            self.winner = "Draw"
            self.status_message = "Draw by Stalemate."
        elif self.board.is_insufficient_material():
            self.status = STATUS_DRAW_INSUFFICIENT
            self.winner = "Draw"
            self.status_message = "Draw by Insufficient Material."
        elif self.board.is_seventyfive_moves() or self.board.is_fifty_moves():
            self.status = STATUS_DRAW_FIFTY_MOVES
            self.winner = "Draw"
            self.status_message = "Draw by Fifty-Move Rule."
        elif self.board.is_fivefold_repetition() or self.board.can_claim_threefold_repetition():
            self.status = STATUS_DRAW_REPETITION
            self.winner = "Draw"
            self.status_message = "Draw by Threefold Repetition."
        else:
            self.status = STATUS_IN_PROGRESS
            self.winner = None
            if self.board.is_check():
                self.status_message = f"Check! {self.turn_name} is in check."
            else:
                self.status_message = f"{self.turn_name}'s turn."

    def is_game_over(self) -> bool:
        return self.status != STATUS_IN_PROGRESS

    def get_king_square_in_check(self) -> Optional[int]:
        """Returns the square of the king currently under check, or None."""
        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            return king_sq
        return None

    def get_material_advantage(self) -> Dict[str, int]:
        """Calculates material score difference between White and Black."""
        white_score = sum(PIECE_VALUES.get(p, 0) for p in self.captured_black)
        black_score = sum(PIECE_VALUES.get(p, 0) for p in self.captured_white)
        diff = white_score - black_score
        return {
            "white_score": white_score,
            "black_score": black_score,
            "difference": diff  # Positive = White ahead, Negative = Black ahead
        }

    def get_formatted_move_history(self) -> List[Tuple[int, str, Optional[str]]]:
        """
        Returns history in turn-paired format:
        [(1, "e4", "e5"), (2, "Nf3", "Nc6"), ...]
        """
        paired = []
        for i in range(0, len(self.move_history), 2):
            move_num = (i // 2) + 1
            white_san = self.move_history[i].san
            black_san = self.move_history[i + 1].san if i + 1 < len(self.move_history) else None
            paired.append((move_num, white_san, black_san))
        return paired
