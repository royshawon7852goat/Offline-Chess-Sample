# SHADOW CHESS

> **The Master's Board • Premium Offline Desktop Chess Game in Python**

**Shadow Chess** is a commercial-grade, fully offline desktop chess application built with Python, Pygame, and python-chess. It combines a sophisticated dark obsidian & metallic gold visual interface with a high-performance custom Minimax AI engine, smooth animations, and complete FIDE tournament rules.

---

## Key Features

### 1. Visual Design & Themes
- **Palette**: Deep charcoal/obsidian background with rich metallic gold accents.
- **Board Themes**:
  - *Midnight Gold*: Deep charcoal slate with metallic gold trim.
  - *Obsidian & Silver*: Monochrome contrast with platinum accents.
  - *Emerald Shadow*: Rich forest emerald with luminescent green.
  - *Royal Wood*: Warm dark mahogany with antique gold.
- **Piece Styles**:
  - *Shadow Gold*: Lustrous ivory and obsidian charcoal with gold bevels.
  - *Neon Cyber*: Luminescent cyan and magenta neon contours.
  - *Classic Slate*: Minimalist tournament platinum styling.
- **Smooth Animations**: Animated piece gliding, subtle hover states, and glowing check indicators.

### 2. Game Modes
- **Mode A: Player vs Computer (AI)**
  - Play against an intelligent custom offline AI engine.
  - 3 Difficulty Tiers: **Easy (Apprentice)**, **Medium (Knight)**, **Hard (Grandmaster)**.
  - Choose to play as White or Black.
  - Background asynchronous engine thinking (UI stays at a locked 60 FPS).
- **Mode B: Local Multiplayer (PvP)**
  - Two players on the same PC with automatic turn alternation and complete rule validation.

### 3. Full Tournament Chess Rules
- Legal movement validation powered by `python-chess`.
- Check, checkmate, and stalemate detection.
- Castling (kingside and queenside).
- En passant captures.
- Interactive Pawn Promotion modal (Queen, Rook, Bishop, Knight).
- Automatic draw detection:
  - Threefold repetition
  - Fifty-move rule
  - Insufficient material
  - Mutual draw agreement
- Resignation and Draw offer system (AI intelligently evaluates position before accepting).
- Undo functionality (reverts full ply cycle in PvE or single ply in PvP).
- Move history ledger in standard algebraic notation (SAN) with turn pairing.

### 4. Custom Chess AI Engine
- **Search Algorithm**: Minimax with Alpha-Beta Pruning.
- **Tactical Pruning**:
  - Move ordering with **MVV-LVA** (Most Valuable Victim – Least Valuable Attacker).
  - Checks, promotions, and castling bonuses prioritized.
  - **Quiescence Search** at depth boundary to eliminate the horizon effect.
- **Positional Knowledge**:
  - Centipawn material balance.
  - Full Piece-Square Tables (PST) adapted for midgame and endgame.
  - Positional bonuses for bishop pairs, castling rights, and open files.
- **Multithreading**:
  - AI calculates on a background worker thread without ever locking or stuttering the Pygame render thread.

### 5. Sound & Atmosphere
- Synthesized 16-bit acoustic wave sound effects:
  - Piece movement clack
  - Piece capture strike
  - King check alert chime
  - Checkmate victory fanfare
  - UI button clicks and game start arpeggio
- Full hardware fallback: Game runs seamlessly even if audio devices are disabled or sound files are missing.

### 6. Local Statistics & Settings
- Persistent settings (`data/settings.json`) and records (`data/statistics.json`).
- Tracks total games, wins, losses, draws, win percentage, and difficulty breakdown.

---

## Project Structure

```
ShadowChess/
│
├── main.py                  # Main entrypoint and game loop
├── config.py                # Visual constants, color palettes, and dimensions
├── game_logic.py            # Board wrapper, tournament rules, move history
├── chess_ai.py              # Custom Minimax AI with Alpha-Beta pruning
├── ui.py                    # Graphical interface, menus, board, and modals
├── settings.py              # Persistent settings manager (JSON)
├── statistics.py            # Persistent statistics manager (JSON)
├── sound_manager.py         # Audio playback and mixer fallback
├── piece_renderer.py        # High-DPI piece rendering and procedural fallback
├── generate_assets.py       # Procedural asset generator (WAV & PNG)
├── build_executable.py      # PyInstaller packaging script
│
├── assets/
│   ├── pieces/              # High-resolution piece textures per theme
│   ├── sounds/              # 16-bit audio sound effects
│   └── fonts/               # Optional custom typography
│
├── data/
│   ├── settings.json        # User preferences
│   └── statistics.json      # Match records
│
├── tests/
│   └── test_game.py         # Automated unit and integration test suite
│
├── requirements.txt         # Project dependencies
├── README.md                # Documentation
└── .gitignore               # Ignored build and runtime files
```

---

## Installation & Running

### Requirements
- Python 3.11, 3.12, 3.13, or 3.14 on Windows 10/11.
- No internet connection required after package installation.

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

*(Note: `pygame-ce` is recommended for Python 3.11–3.14 compatibility and high performance).*

### Step 2: Generate Assets (Optional / Included)
Assets are pre-generated. If needed, re-generate anytime using:
```bash
python generate_assets.py
```

### Step 3: Run the Game
```bash
python main.py
```

---

## Running Automated Tests

Run the full verification suite to test chess mechanics, AI search, state persistence, and error resilience:
```bash
python -m unittest discover tests
```

---

## Packaging as Windows Executable (.exe)

To bundle Shadow Chess into a standalone Windows executable (`ShadowChess.exe`):

```bash
python build_executable.py
```

The resulting distributable executable and asset bundle will be placed in `dist/ShadowChess/`.

---

## License & Credits
Developed with pure Python, Pygame-CE, and python-chess. Completely offline and DRM-free.
