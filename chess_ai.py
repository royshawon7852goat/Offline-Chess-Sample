"""
SHADOW CHESS - Custom Chess AI Engine
Implements Negamax with Alpha-Beta Pruning, Quiescence Search, Move Ordering (MVV-LVA),
Piece-Square Tables, and Asynchronous Search.
"""

import chess
import random
import threading
import time
from typing import Optional, Tuple, List, Callable

# Piece Material Values (Centipawns)
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Piece-Square Tables (White perspective, flipped for Black)
# Centered on e4/d4, 8x8 flattened from rank 8 (top) to rank 1 (bottom)
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MIDGAME_TABLE = [
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_ENDGAME_TABLE = [
   -50,-40,-30,-20,-20,-30,-40,-50,
   -30,-20,-10,  0,  0,-10,-20,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-30,  0,  0,  0,  0,-30,-30,
   -50,-30,-30,-30,-30,-30,-30,-50
]

PST_MAP = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE
}


def get_pst_value(piece_type: int, square: int, color: chess.Color, is_endgame: bool = False) -> int:
    """Returns the piece-square positional value from the perspective of White."""
    sq_idx = (63 - square) if color == chess.WHITE else square
    
    if piece_type == chess.KING:
        table = KING_ENDGAME_TABLE if is_endgame else KING_MIDGAME_TABLE
    else:
        table = PST_MAP.get(piece_type, None)
        
    if table is None:
        return 0
    return table[sq_idx]


def evaluate_board(board: chess.Board) -> int:
    """
    Evaluates board position from the perspective of the side to move (Negamax convention).
    Positive: Advantage for the current turn.
    Negative: Advantage for the opponent.
    """
    if board.is_checkmate():
        # The player whose turn it is has no legal moves and is in check -> losing
        return -99999
        
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition():
        return 0

    # Determine if position is in endgame
    white_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
    black_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
    white_majors = len(board.pieces(chess.ROOK, chess.WHITE)) + white_queens
    black_majors = len(board.pieces(chess.ROOK, chess.BLACK)) + black_queens
    is_endgame = (white_majors <= 1 and black_majors <= 1)

    white_score = 0
    
    # Material and Piece-Square Table evaluation
    for square, piece in board.piece_map().items():
        base_val = PIECE_VALUES[piece.piece_type]
        pst_val = get_pst_value(piece.piece_type, square, piece.color, is_endgame)
        piece_score = base_val + pst_val
        
        if piece.color == chess.WHITE:
            white_score += piece_score
        else:
            white_score -= piece_score

    # Positional heuristics
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        white_score += 35
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        white_score -= 35

    if board.has_castling_rights(chess.WHITE):
        white_score += 25
    if board.has_castling_rights(chess.BLACK):
        white_score -= 25

    # Negamax: score from side to move's perspective
    return white_score if board.turn == chess.WHITE else -white_score


def order_moves(board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
    """
    Orders moves using MVV-LVA (Most Valuable Victim - Least Valuable Attacker),
    checks, promotions, and captures to maximize alpha-beta cutoffs.
    """
    def score_move(move: chess.Move) -> int:
        score = 0
        from_piece = board.piece_at(move.from_square)
        to_piece = board.piece_at(move.to_square)

        # Captures: MVV-LVA
        if to_piece:
            victim_val = PIECE_VALUES.get(to_piece.piece_type, 0)
            attacker_val = PIECE_VALUES.get(from_piece.piece_type, 0) if from_piece else 0
            score += 10000 + (victim_val * 10 - attacker_val)
        elif board.is_en_passant(move):
            score += 10000 + (100 * 10 - 100)

        # Pawn promotion
        if move.promotion:
            score += 9000 + PIECE_VALUES.get(move.promotion, 0)

        # Checks
        if board.gives_check(move):
            score += 500

        # Castling
        if board.is_castling(move):
            score += 300

        return score

    return sorted(moves, key=score_move, reverse=True)


def quiescence_search(board: chess.Board, alpha: int, beta: int, depth_limit: int = 3) -> int:
    """
    Quiescence search in Negamax format to evaluate noisy captures and eliminate horizon effect.
    """
    stand_pat = evaluate_board(board)

    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    if depth_limit <= 0 or board.is_game_over():
        return alpha

    # Generate only capture and promotion moves
    capture_moves = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
    ordered_captures = order_moves(board, capture_moves)

    for move in ordered_captures:
        board.push(move)
        score = -quiescence_search(board, -beta, -alpha, depth_limit - 1)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    """
    Negamax search with Alpha-Beta Pruning.
    """
    if depth <= 0:
        return quiescence_search(board, alpha, beta, depth_limit=2)

    if board.is_game_over():
        return evaluate_board(board)

    legal_moves = order_moves(board, list(board.legal_moves))
    if not legal_moves:
        return evaluate_board(board)

    best_score = -float("inf")

    for move in legal_moves:
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha)
        board.pop()

        if score >= beta:
            return beta
        if score > best_score:
            best_score = score
        if score > alpha:
            alpha = score

    return best_score


def find_best_move(board: chess.Board, difficulty: str = "Medium") -> Optional[chess.Move]:
    """
    Finds the best move for the current board position using Negamax with Alpha-Beta Pruning.
    """
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    # Easy difficulty: fast depth 1-2 with chance of human-like sub-optimal move
    if difficulty == "Easy":
        if random.random() < 0.35:
            captures = [m for m in legal_moves if board.is_capture(m)]
            return random.choice(captures) if captures else random.choice(legal_moves)
        depth = 1
    elif difficulty == "Hard":
        depth = 4
    else:  # Medium
        depth = 3

    ordered_moves = order_moves(board, legal_moves)
    best_move = ordered_moves[0]
    best_score = -float("inf")
    alpha = -float("inf")
    beta = float("inf")

    scored_moves = []

    for move in ordered_moves:
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha)
        board.pop()

        scored_moves.append((move, score))

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    # In Medium difficulty, small chance to pick 2nd best move if nearly equal
    if difficulty == "Medium" and len(scored_moves) > 1 and random.random() < 0.10:
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        second_move, second_score = scored_moves[1]
        if abs(second_score - best_score) <= 30:
            return second_move

    return best_move


class ChessAIWorker:
    """Manages asynchronous AI calculation in a worker thread."""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self.is_calculating = False
        self.latest_move: Optional[chess.Move] = None

    def start_search(self, board_fen: str, difficulty: str, callback: Callable[[Optional[chess.Move]], None]):
        """Starts asynchronous calculation using a clone of the board from FEN."""
        if self.is_calculating:
            return

        self.is_calculating = True
        self.latest_move = None

        def worker():
            start_time = time.time()
            try:
                board_clone = chess.Board(board_fen)
                # Ensure at least a slight delay for realism (0.4s)
                move = find_best_move(board_clone, difficulty)
                elapsed = time.time() - start_time
                if elapsed < 0.35:
                    time.sleep(0.35 - elapsed)
            except Exception as e:
                print(f"[ChessAIWorker] Error during search: {e}")
                try:
                    fallback_board = chess.Board(board_fen)
                    move = next(iter(fallback_board.legal_moves), None)
                except Exception:
                    move = None
            finally:
                self.is_calculating = False
                self.latest_move = move
                if callback:
                    callback(move)

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()
