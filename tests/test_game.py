"""
SHADOW CHESS - Test Suite
Verifies chess rules, AI engine, persistence, undo mechanics, and error handling.
"""

import unittest
import os
import sys
import chess

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_logic import (
    ChessGame, STATUS_IN_PROGRESS, STATUS_CHECKMATE, STATUS_STALEMATE,
    STATUS_DRAW_INSUFFICIENT, STATUS_RESIGNED, STATUS_DRAW_AGREED
)
from chess_ai import find_best_move, evaluate_board
from settings import SettingsManager, DEFAULT_SETTINGS
from statistics import StatisticsManager
from sound_manager import SoundManager


class TestChessRules(unittest.TestCase):
    """Verifies chess movements, validations, and tournament rules."""

    def setUp(self):
        self.game = ChessGame(mode="PVP")

    def test_initial_state(self):
        self.assertEqual(self.game.turn, chess.WHITE)
        self.assertEqual(len(self.game.move_history), 0)
        self.assertEqual(self.game.status, STATUS_IN_PROGRESS)
        self.assertFalse(self.game.is_game_over())

    def test_legal_and_illegal_moves(self):
        # e2 to e4 is legal
        e2 = chess.E2
        e4 = chess.E4
        self.assertTrue(self.game.make_move(e2, e4))
        self.assertEqual(self.game.turn, chess.BLACK)
        self.assertEqual(len(self.game.move_history), 1)

        # Illegal move: Black knight trying to jump to e5 through illegal square
        self.assertFalse(self.game.make_move(chess.B8, chess.E5))
        self.assertEqual(self.game.turn, chess.BLACK)

    def test_castling(self):
        # Set up kingside castling for White
        # 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O
        moves = [
            (chess.E2, chess.E4), (chess.E7, chess.E5),
            (chess.G1, chess.F3), (chess.B8, chess.C6),
            (chess.F1, chess.C4), (chess.F8, chess.C5)
        ]
        for f, t in moves:
            self.assertTrue(self.game.make_move(f, t))

        # White castles kingside: e1 to g1
        self.assertTrue(self.game.make_move(chess.E1, chess.G1))
        # King should now be at g1, Rook should be at f1
        self.assertEqual(self.game.board.piece_at(chess.G1).piece_type, chess.KING)
        self.assertEqual(self.game.board.piece_at(chess.F1).piece_type, chess.ROOK)

    def test_en_passant(self):
        # 1. e4 a6 2. e5 d5 3. exd6 (en passant capture)
        self.game.make_move(chess.E2, chess.E4)
        self.game.make_move(chess.A7, chess.A6)
        self.game.make_move(chess.E4, chess.E5)
        self.game.make_move(chess.D7, chess.D5)

        # e5 can capture d6 en passant
        self.assertTrue(self.game.make_move(chess.E5, chess.D6))
        # The captured pawn on d5 should be removed
        self.assertIsNone(self.game.board.piece_at(chess.D5))
        self.assertEqual(len(self.game.captured_black), 1)

    def test_pawn_promotion(self):
        # Set up a board with a white pawn on a7
        self.game.board = chess.Board("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        # Trying to move a7 -> a8 without promotion should trigger pending_promotion
        self.assertFalse(self.game.make_move(chess.A7, chess.A8))
        self.assertEqual(self.game.pending_promotion, (chess.A7, chess.A8))

        # Complete promotion to Queen
        self.assertTrue(self.game.complete_promotion(chess.QUEEN))
        promoted_piece = self.game.board.piece_at(chess.A8)
        self.assertIsNotNone(promoted_piece)
        self.assertEqual(promoted_piece.piece_type, chess.QUEEN)

    def test_checkmate_fools_mate(self):
        # Fool's Mate: 1. f3 e5 2. g4 Qh4#
        self.game.make_move(chess.F2, chess.F3)
        self.game.make_move(chess.E7, chess.E5)
        self.game.make_move(chess.G2, chess.G4)
        self.game.make_move(chess.D8, chess.H4)

        self.assertEqual(self.game.status, STATUS_CHECKMATE)
        self.assertEqual(self.game.winner, "Black")
        self.assertTrue(self.game.is_game_over())

    def test_stalemate(self):
        # Stalemate position
        self.game.board = chess.Board("k7/8/1Q6/8/8/8/8/7K b - - 0 1")
        self.game._update_game_status()
        self.assertEqual(self.game.status, STATUS_STALEMATE)
        self.assertEqual(self.game.winner, "Draw")
        self.assertTrue(self.game.is_game_over())

    def test_undo_functionality(self):
        self.game.make_move(chess.E2, chess.E4)
        self.game.make_move(chess.E7, chess.E5)
        self.assertEqual(len(self.game.move_history), 2)

        # Undo in PVP mode reverts 1 move
        self.assertTrue(self.game.undo_move())
        self.assertEqual(len(self.game.move_history), 1)
        self.assertEqual(self.game.turn, chess.BLACK)

        # Re-undo
        self.assertTrue(self.game.undo_move())
        self.assertEqual(len(self.game.move_history), 0)
        self.assertEqual(self.game.turn, chess.WHITE)

    def test_resignation(self):
        self.game.resign("White")
        self.assertEqual(self.game.status, STATUS_RESIGNED)
        self.assertEqual(self.game.winner, "Black")
        self.assertTrue(self.game.is_game_over())

    def test_draw_offer(self):
        # In PVP, draw is agreed immediately
        accepted = self.game.offer_draw("White")
        self.assertTrue(accepted)
        self.assertEqual(self.game.status, STATUS_DRAW_AGREED)
        self.assertEqual(self.game.winner, "Draw")

    def test_insufficient_material(self):
        # King vs King is insufficient material
        self.game.board = chess.Board("8/8/8/4k3/8/8/4K3/8 w - - 0 1")
        self.game._update_game_status()
        self.assertEqual(self.game.status, STATUS_DRAW_INSUFFICIENT)
        self.assertEqual(self.game.winner, "Draw")
        self.assertTrue(self.game.is_game_over())

    def test_sound_manager_resilience(self):
        sm = SoundManager()
        # Should not crash when playing nonexistent or existing sound
        sm.play("move")
        sm.play("nonexistent_sound")

    def test_piece_renderer_fallback(self):
        from piece_renderer import PieceRenderer
        pr = PieceRenderer()
        surf = pr.get_piece_surface(chess.KING, True, size=80)
        self.assertIsNotNone(surf)
        self.assertEqual(surf.get_width(), 80)
        self.assertEqual(surf.get_height(), 80)


class TestChessAI(unittest.TestCase):
    """Verifies AI engine move search and evaluation."""

    def test_find_best_move_easy(self):
        board = chess.Board()
        move = find_best_move(board, difficulty="Easy")
        self.assertIsNotNone(move)
        self.assertIn(move, board.legal_moves)

    def test_find_best_move_medium(self):
        board = chess.Board()
        move = find_best_move(board, difficulty="Medium")
        self.assertIsNotNone(move)
        self.assertIn(move, board.legal_moves)

    def test_tactical_punishment(self):
        # Black queen hanging on d4: White pawn on c3 can capture it
        board = chess.Board("rnb1kbnr/pppp1ppp/8/8/3q4/2P5/PP1PPPPP/RNBQKBNR w KQkq - 0 1")
        best_move = find_best_move(board, difficulty="Medium")
        self.assertEqual(best_move, chess.Move.from_uci("c3d4"))

    def test_evaluate_board(self):
        board = chess.Board()
        initial_eval = evaluate_board(board)
        # Should be roughly equal at starting position
        self.assertAlmostEqual(initial_eval, 0, delta=50)


class TestManagers(unittest.TestCase):
    """Verifies settings and statistics persistence."""

    def setUp(self):
        self.test_settings_path = "test_settings.json"
        self.test_stats_path = "test_stats.json"

    def tearDown(self):
        for p in [self.test_settings_path, self.test_stats_path,
                 self.test_settings_path + ".tmp", self.test_stats_path + ".tmp"]:
            if os.path.exists(p):
                os.remove(p)

    def test_settings_save_and_load(self):
        sm = SettingsManager(filepath=self.test_settings_path)
        sm.set("sound_volume", 0.5)
        sm.set("ai_difficulty", "Hard")

        sm2 = SettingsManager(filepath=self.test_settings_path)
        self.assertEqual(sm2.get("sound_volume"), 0.5)
        self.assertEqual(sm2.get("ai_difficulty"), "Hard")

    def test_statistics_record(self):
        stm = StatisticsManager(filepath=self.test_stats_path)
        stm.record_pve_game("win", "Hard")
        stm.record_pve_game("loss", "Hard")
        stm.record_pvp_game("White")

        stm2 = StatisticsManager(filepath=self.test_stats_path)
        summary = stm2.get_summary()
        self.assertEqual(summary["total_games"], 3)
        self.assertEqual(summary["wins"], 1)
        self.assertEqual(summary["losses"], 1)
        self.assertEqual(summary["win_percentage"], 50.0)


if __name__ == "__main__":
    unittest.main()
