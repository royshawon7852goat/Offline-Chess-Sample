"""
SHADOW CHESS - Statistics Manager
Tracks match records, win rates, and difficulty breakdowns locally via JSON.
"""

import json
import os
from config import DATA_DIR, STATISTICS_FILE

DEFAULT_STATISTICS = {
    "total_games": 0,
    "wins": 0,
    "losses": 0,
    "draws": 0,
    "win_percentage": 0.0,
    "pve": {
        "Easy": {"games": 0, "wins": 0, "losses": 0, "draws": 0},
        "Medium": {"games": 0, "wins": 0, "losses": 0, "draws": 0},
        "Hard": {"games": 0, "wins": 0, "losses": 0, "draws": 0}
    },
    "pvp": {
        "games": 0,
        "white_wins": 0,
        "black_wins": 0,
        "draws": 0
    }
}


class StatisticsManager:
    """Manages player statistics with persistent JSON storage."""

    def __init__(self, filepath=STATISTICS_FILE):
        self.filepath = filepath
        self.stats = DEFAULT_STATISTICS.copy()
        self.load()

    def load(self):
        """Loads statistics from JSON file or initializes defaults."""
        if not os.path.exists(self.filepath):
            self.save()
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self._merge_stats(data)
                self._recalculate()
        except Exception as e:
            print(f"[StatisticsManager] Warning: Failed loading stats ({e}). Initializing.")
            self.stats = DEFAULT_STATISTICS.copy()
            self.save()

    def _merge_stats(self, data):
        """Carefully merges loaded data with default schema to preserve integrity."""
        self.stats["total_games"] = data.get("total_games", 0)
        self.stats["wins"] = data.get("wins", 0)
        self.stats["losses"] = data.get("losses", 0)
        self.stats["draws"] = data.get("draws", 0)
        self.stats["win_percentage"] = data.get("win_percentage", 0.0)

        pve_data = data.get("pve", {})
        for diff in ["Easy", "Medium", "Hard"]:
            if diff in pve_data and isinstance(pve_data[diff], dict):
                self.stats["pve"][diff] = {
                    "games": pve_data[diff].get("games", 0),
                    "wins": pve_data[diff].get("wins", 0),
                    "losses": pve_data[diff].get("losses", 0),
                    "draws": pve_data[diff].get("draws", 0)
                }

        pvp_data = data.get("pvp", {})
        self.stats["pvp"] = {
            "games": pvp_data.get("games", 0),
            "white_wins": pvp_data.get("white_wins", 0),
            "black_wins": pvp_data.get("black_wins", 0),
            "draws": pvp_data.get("draws", 0)
        }

    def _recalculate(self):
        """Recalculates win rate and totals."""
        total_pve = self.stats["wins"] + self.stats["losses"] + self.stats["draws"]
        if total_pve > 0:
            self.stats["win_percentage"] = round((self.stats["wins"] / total_pve) * 100.0, 1)
        else:
            self.stats["win_percentage"] = 0.0
        self.stats["total_games"] = total_pve + self.stats["pvp"]["games"]

    def record_pve_game(self, result, difficulty):
        """
        Record a Player vs AI game.
        result: 'win', 'loss', or 'draw'
        difficulty: 'Easy', 'Medium', or 'Hard'
        """
        if difficulty not in self.stats["pve"]:
            difficulty = "Medium"

        diff_record = self.stats["pve"][difficulty]
        diff_record["games"] += 1

        if result == "win":
            self.stats["wins"] += 1
            diff_record["wins"] += 1
        elif result == "loss":
            self.stats["losses"] += 1
            diff_record["losses"] += 1
        elif result == "draw":
            self.stats["draws"] += 1
            diff_record["draws"] += 1

        self._recalculate()
        self.save()

    def record_pvp_game(self, winner):
        """
        Record a Local Multiplayer game.
        winner: 'White', 'Black', or 'Draw'
        """
        pvp = self.stats["pvp"]
        pvp["games"] += 1
        if winner == "White":
            pvp["white_wins"] += 1
        elif winner == "Black":
            pvp["black_wins"] += 1
        else:
            pvp["draws"] += 1

        self._recalculate()
        self.save()

    def save(self):
        """Saves current statistics to disk atomically."""
        try:
            dirname = os.path.dirname(self.filepath)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            temp_file = self.filepath + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=4)
            if os.path.exists(self.filepath):
                os.replace(temp_file, self.filepath)
            else:
                os.rename(temp_file, self.filepath)
        except Exception as e:
            print(f"[StatisticsManager] Error saving statistics: {e}")

    def reset(self):
        """Resets all statistics to zero."""
        self.stats = {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_percentage": 0.0,
            "pve": {
                "Easy": {"games": 0, "wins": 0, "losses": 0, "draws": 0},
                "Medium": {"games": 0, "wins": 0, "losses": 0, "draws": 0},
                "Hard": {"games": 0, "wins": 0, "losses": 0, "draws": 0}
            },
            "pvp": {
                "games": 0,
                "white_wins": 0,
                "black_wins": 0,
                "draws": 0
            }
        }
        self.save()

    def get_summary(self):
        return self.stats
