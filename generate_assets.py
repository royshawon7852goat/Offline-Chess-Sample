"""
SHADOW CHESS - Asset Generator
Generates high-fidelity audio assets (.wav) and sleek high-DPI chess piece textures (.png).
Uses purely standard Python and Pillow.
"""

import math
import os
import struct
import wave
from PIL import Image, ImageDraw, ImageFilter
from config import COLOR_BG_DARK

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
PIECES_DIR = os.path.join(ASSETS_DIR, "pieces")


# =====================================================================
# AUDIO ASSET GENERATION
# =====================================================================

def write_wav(filepath, samples, sample_rate=44100):
    """Writes a 16-bit mono WAV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        data = bytearray()
        for s in samples:
            # Clamp to 16-bit signed integer range
            clamped = max(-32767, min(32767, int(s * 32767)))
            data += struct.pack("<h", clamped)
        f.writeframes(data)


def generate_sounds():
    """Generates all game sound effects procedurally."""
    sample_rate = 44100

    # 1. MOVE SOUND (Tactile wooden piece placed on wooden board)
    duration = 0.09
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        # Envelope: sharp attack, fast natural decay
        env = math.exp(-t * 45.0)
        # Low wooden pitch drop (220Hz down to 140Hz)
        freq = 220.0 - (t / duration) * 80.0
        tone = math.sin(2 * math.pi * freq * t)
        # Body resonance overtone
        tone += 0.4 * math.sin(2 * math.pi * (freq * 2.3) * t)
        # Initial transient impact click
        noise = (math.sin(t * 18000.0) * math.sin(t * 9000.0)) * math.exp(-t * 200.0) * 0.3
        val = (tone + noise) * env * 0.85
        samples.append(val)
    write_wav(os.path.join(SOUNDS_DIR, "move.wav"), samples, sample_rate)

    # 2. CAPTURE SOUND (Punchy, crisp clack of piece strike)
    duration = 0.14
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-t * 30.0)
        # Dual resonant strike
        tone1 = math.sin(2 * math.pi * 320.0 * t)
        tone2 = 0.6 * math.sin(2 * math.pi * 510.0 * t)
        tone3 = 0.3 * math.sin(2 * math.pi * 160.0 * t)
        # Sharp impact transient
        noise = (math.sin(t * 22000.0) + math.sin(t * 14000.0)) * math.exp(-t * 160.0) * 0.5
        val = (tone1 + tone2 + tone3 + noise) * env * 0.95
        samples.append(val)
    write_wav(os.path.join(SOUNDS_DIR, "capture.wav"), samples, sample_rate)

    # 3. CHECK SOUND (Dual-tone alert bell)
    duration = 0.45
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-t * 7.0)
        # Chord: E5 (659Hz) and B5 (987Hz)
        tone = 0.6 * math.sin(2 * math.pi * 659.25 * t) + 0.4 * math.sin(2 * math.pi * 987.77 * t)
        tone += 0.2 * math.sin(2 * math.pi * 1318.5 * t)
        val = tone * env * 0.8
        samples.append(val)
    write_wav(os.path.join(SOUNDS_DIR, "check.wav"), samples, sample_rate)

    # 4. CHECKMATE SOUND (Triumphant brass/organ chord with royal reverberation)
    duration = 1.3
    n_samples = int(sample_rate * duration)
    samples = []
    # Major triad: C4 (261Hz), G4 (392Hz), C5 (523Hz), E5 (659Hz)
    chord = [(261.63, 0.4), (392.0, 0.35), (523.25, 0.4), (659.25, 0.35), (1046.5, 0.2)]
    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-t * 2.8) if t > 0.05 else (t / 0.05)
        tone = sum(amp * math.sin(2 * math.pi * freq * t) for freq, amp in chord)
        # Shimmer harmonic
        shimmer = 0.1 * math.sin(2 * math.pi * 1567.98 * t) * math.exp(-t * 4.0)
        val = (tone + shimmer) * env * 0.85
        samples.append(val)
    write_wav(os.path.join(SOUNDS_DIR, "checkmate.wav"), samples, sample_rate)

    # 5. CLICK SOUND (Subtle UI button click)
    duration = 0.035
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-t * 120.0)
        val = math.sin(2 * math.pi * 950.0 * t) * env * 0.6
        samples.append(val)
    write_wav(os.path.join(SOUNDS_DIR, "click.wav"), samples, sample_rate)

    # 6. GAME START SOUND (Rising chime arpeggio)
    duration = 0.6
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        val = 0.0
        # Note 1: C5 (523Hz) at t=0
        if 0.0 <= t < 0.4:
            val += 0.5 * math.sin(2 * math.pi * 523.25 * t) * math.exp(-(t - 0.0) * 12.0)
        # Note 2: E5 (659Hz) at t=0.1
        if 0.1 <= t < 0.5:
            val += 0.5 * math.sin(2 * math.pi * 659.25 * (t - 0.1)) * math.exp(-(t - 0.1) * 12.0)
        # Note 3: G5 (784Hz) at t=0.2
        if 0.2 <= t < 0.6:
            val += 0.6 * math.sin(2 * math.pi * 784.0 * (t - 0.2)) * math.exp(-(t - 0.2) * 8.0)
        samples.append(val * 0.8)
    write_wav(os.path.join(SOUNDS_DIR, "game_start.wav"), samples, sample_rate)

    # 7. DRAW SOUND (Harmonic serene chime)
    duration = 0.6
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-t * 5.0)
        tone = 0.5 * math.sin(2 * math.pi * 440.0 * t) + 0.5 * math.sin(2 * math.pi * 659.25 * t)
        val = tone * env * 0.7
        samples.append(val)
    write_wav(os.path.join(SOUNDS_DIR, "draw.wav"), samples, sample_rate)

    # 8. ILLEGAL SOUND (Low muted bump)
    duration = 0.08
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-t * 40.0)
        val = math.sin(2 * math.pi * 130.0 * t) * env * 0.6
        samples.append(val)
    write_wav(os.path.join(SOUNDS_DIR, "illegal.wav"), samples, sample_rate)

    print("[AssetGenerator] Sound effects generated successfully.")


# =====================================================================
# CHESS PIECE HIGH-DPI TEXTURE GENERATION
# =====================================================================

def draw_supersampled_piece(piece_char, color, theme="Shadow Gold", target_size=256):
    """
    Renders a piece with 4x supersampling (1024x1024 downscaled to 256x256)
    with smooth anti-aliased polygons, bevels, gold trims, and soft drop shadows.
    """
    canvas_size = 1024
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = canvas_size // 2
    cy = canvas_size // 2

    # Color configurations
    if theme == "Shadow Gold":
        if color == "w":
            primary_fill = (245, 245, 248, 255)      # Lustrous Ivory
            inner_fill = (220, 222, 230, 255)        # Pearl shade
            accent_gold = (212, 175, 55, 255)        # Metallic Gold Trim
            gold_highlight = (248, 225, 130, 255)    # Shiny Gold
            shadow_color = (0, 0, 0, 160)
        else:
            primary_fill = (28, 30, 36, 255)         # Deep Obsidian Charcoal
            inner_fill = (18, 19, 23, 255)           # Shadow Black
            accent_gold = (218, 165, 32, 255)        # Rich Amber Gold Trim
            gold_highlight = (255, 215, 80, 255)     # Bright Accent
            shadow_color = (0, 0, 0, 180)
    elif theme == "Neon Cyber":
        if color == "w":
            primary_fill = (220, 250, 255, 255)
            inner_fill = (180, 230, 245, 255)
            accent_gold = (0, 220, 255, 255)         # Cyan Neon
            gold_highlight = (140, 245, 255, 255)
            shadow_color = (0, 100, 150, 140)
        else:
            primary_fill = (35, 20, 45, 255)
            inner_fill = (20, 10, 30, 255)
            accent_gold = (255, 60, 140, 255)        # Magenta / Violet Neon
            gold_highlight = (255, 130, 190, 255)
            shadow_color = (120, 0, 80, 140)
    else:  # Classic Slate
        if color == "w":
            primary_fill = (235, 238, 242, 255)
            inner_fill = (205, 210, 218, 255)
            accent_gold = (160, 175, 195, 255)       # Platinum Silver
            gold_highlight = (240, 245, 255, 255)
            shadow_color = (0, 0, 0, 150)
        else:
            primary_fill = (32, 34, 40, 255)
            inner_fill = (20, 22, 26, 255)
            accent_gold = (110, 120, 135, 255)
            gold_highlight = (160, 175, 195, 255)
            shadow_color = (0, 0, 0, 170)

    # Drop shadow layer
    shadow_img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)

    def draw_base_pedestal(d, offset_y=0, fill_col=primary_fill, trim_col=accent_gold):
        # Bottom pedestal
        by = cy + 320 + offset_y
        # Lower tier
        d.rounded_rectangle([cx - 240, by - 40, cx + 240, by + 40], radius=25, fill=fill_col, outline=trim_col, width=14)
        # Gold accent ring
        d.rounded_rectangle([cx - 210, by - 65, cx + 210, by - 35], radius=15, fill=trim_col)
        # Upper base tier
        d.rounded_rectangle([cx - 180, by - 100, cx + 180, by - 55], radius=20, fill=fill_col, outline=trim_col, width=12)

    # 1. PAWN
    if piece_char == "p":
        # Shadow
        draw_base_pedestal(s_draw, offset_y=25, fill_col=shadow_color, trim_col=(0, 0, 0, 0))
        s_draw.ellipse([cx - 110, cy - 220 + 25, cx + 110, cy + 0 + 25], fill=shadow_color)
        s_draw.polygon([(cx - 110, cy + 220 + 25), (cx + 110, cy + 220 + 25), (cx + 60, cy - 80 + 25), (cx - 60, cy - 80 + 25)], fill=shadow_color)

        # Base
        draw_base_pedestal(draw)
        # Body / Stem
        draw.polygon([(cx - 130, cy + 220), (cx + 130, cy + 220), (cx + 70, cy - 70), (cx - 70, cy - 70)], fill=primary_fill, outline=accent_gold)
        # Body bevel
        draw.polygon([(cx - 80, cy + 200), (cx + 80, cy + 200), (cx + 40, cy - 50), (cx - 40, cy - 50)], fill=inner_fill)
        # Collar ring
        draw.rounded_rectangle([cx - 105, cy - 95, cx + 105, cy - 65], radius=15, fill=accent_gold, outline=gold_highlight, width=6)
        # Head ball
        draw.ellipse([cx - 115, cy - 305, cx + 115, cy - 75], fill=primary_fill, outline=accent_gold, width=14)
        # Head highlight
        draw.ellipse([cx - 75, cy - 265, cx + 75, cy - 115], fill=inner_fill)
        draw.ellipse([cx - 45, cy - 280, cx - 15, cy - 250], fill=gold_highlight)

    # 2. KNIGHT
    elif piece_char == "n":
        draw_base_pedestal(s_draw, offset_y=25, fill_col=shadow_color, trim_col=(0, 0, 0, 0))
        draw_base_pedestal(draw)

        # Majestic horse head polygon
        points = [
            (cx - 140, cy + 220),  # back base
            (cx - 140, cy + 20),   # arching neck back
            (cx - 170, cy - 100),  # mane crest peak 1
            (cx - 130, cy - 120),  # mane valley
            (cx - 160, cy - 200),  # mane crest peak 2
            (cx - 100, cy - 230),  # mane valley
            (cx - 90, cy - 330),   # ear back
            (cx - 40, cy - 350),   # ear tip
            (cx - 10, cy - 280),   # ear front
            (cx + 80, cy - 240),   # crown / brow
            (cx + 190, cy - 140),  # snout top
            (cx + 200, cy - 60),   # snout tip / nose
            (cx + 120, cy - 20),   # lower jaw
            (cx + 140, cy + 40),   # chin curve
            (cx + 70, cy + 120),   # throat / chest
            (cx + 130, cy + 220),  # front base
        ]
        draw.polygon(points, fill=primary_fill, outline=accent_gold)
        # Inner shading
        inner_points = [
            (cx - 100, cy + 190),
            (cx - 100, cy + 30),
            (cx - 110, cy - 160),
            (cx - 30, cy - 240),
            (cx + 50, cy - 200),
            (cx + 140, cy - 110),
            (cx + 130, cy - 50),
            (cx + 80, cy + 40),
            (cx + 30, cy + 110),
            (cx + 90, cy + 190),
        ]
        draw.polygon(inner_points, fill=inner_fill)

        # Eye (glowing gold diamond/almond)
        eye_pts = [(cx + 40, cy - 160), (cx + 80, cy - 175), (cx + 60, cy - 150), (cx + 30, cy - 145)]
        draw.polygon(eye_pts, fill=accent_gold, outline=gold_highlight)

        # Muzzle / nostril
        draw.ellipse([cx + 145, cy - 85, cx + 175, cy - 65], fill=accent_gold)

        # Mane decorative lines
        for my in [-180, -90, 0, 90]:
            draw.line([(cx - 130, cy + my), (cx - 70, cy + my - 30)], fill=accent_gold, width=8)

    # 3. BISHOP
    elif piece_char == "b":
        draw_base_pedestal(s_draw, offset_y=25, fill_col=shadow_color, trim_col=(0, 0, 0, 0))
        draw_base_pedestal(draw)

        # Stem
        draw.polygon([(cx - 120, cy + 220), (cx + 120, cy + 220), (cx + 65, cy - 40), (cx - 65, cy - 40)], fill=primary_fill, outline=accent_gold)
        draw.polygon([(cx - 70, cy + 190), (cx + 70, cy + 190), (cx + 35, cy - 20), (cx - 35, cy - 20)], fill=inner_fill)

        # Collar
        draw.rounded_rectangle([cx - 115, cy - 65, cx + 115, cy - 35], radius=15, fill=accent_gold, outline=gold_highlight, width=6)

        # Mitre head (Oval dome)
        draw.ellipse([cx - 130, cy - 290, cx + 130, cy - 40], fill=primary_fill, outline=accent_gold, width=14)
        draw.ellipse([cx - 85, cy - 250, cx + 85, cy - 70], fill=inner_fill)

        # Finial cross/ball at peak
        draw.ellipse([cx - 25, cy - 340, cx + 25, cy - 290], fill=accent_gold, outline=gold_highlight, width=6)

        # Signature Bishop angled cleft / slash
        draw.line([(cx - 40, cy - 240), (cx + 60, cy - 130)], fill=accent_gold, width=16)
        draw.line([(cx - 40, cy - 240), (cx + 60, cy - 130)], fill=COLOR_BG_DARK if color == 'b' else (80, 80, 80), width=8)

        # Regal cross engraving
        draw.line([(cx, cy - 200), (cx, cy - 100)], fill=accent_gold, width=10)
        draw.line([(cx - 40, cy - 150), (cx + 40, cy - 150)], fill=accent_gold, width=10)

    # 4. ROOK
    elif piece_char == "r":
        draw_base_pedestal(s_draw, offset_y=25, fill_col=shadow_color, trim_col=(0, 0, 0, 0))
        draw_base_pedestal(draw)

        # Solid castle pillar tower
        draw.polygon([(cx - 140, cy + 220), (cx + 140, cy + 220), (cx + 105, cy - 120), (cx - 105, cy - 120)], fill=primary_fill, outline=accent_gold)
        draw.polygon([(cx - 90, cy + 190), (cx + 90, cy + 190), (cx + 65, cy - 100), (cx - 65, cy - 100)], fill=inner_fill)

        # Tower cornice
        draw.rounded_rectangle([cx - 145, cy - 155, cx + 145, cy - 115], radius=15, fill=accent_gold, outline=gold_highlight, width=6)

        # Crenellated battlements
        # Main top block
        draw.rectangle([cx - 150, cy - 270, cx + 150, cy - 155], fill=primary_fill, outline=accent_gold, width=14)
        # Cutouts (embrasures)
        draw.rectangle([cx - 70, cy - 280, cx - 20, cy - 210], fill=COLOR_BG_DARK if color == 'b' else (70, 75, 85))
        draw.rectangle([cx + 20, cy - 280, cx + 70, cy - 210], fill=COLOR_BG_DARK if color == 'b' else (70, 75, 85))

        # Battlements gold trim
        draw.line([(cx - 150, cy - 270), (cx + 150, cy - 270)], fill=accent_gold, width=12)

        # Arrow slit window in center of tower
        draw.rounded_rectangle([cx - 20, cy - 20, cx + 20, cy + 90], radius=10, fill=accent_gold, outline=gold_highlight, width=4)

    # 5. QUEEN
    elif piece_char == "q":
        draw_base_pedestal(s_draw, offset_y=25, fill_col=shadow_color, trim_col=(0, 0, 0, 0))
        draw_base_pedestal(draw)

        # Waist and flowing dress
        draw.polygon([
            (cx - 140, cy + 220), (cx + 140, cy + 220),
            (cx + 80, cy + 50), (cx + 115, cy - 80),
            (cx - 115, cy - 80), (cx - 80, cy + 50)
        ], fill=primary_fill, outline=accent_gold)
        draw.polygon([(cx - 80, cy + 190), (cx + 80, cy + 190), (cx + 50, cy - 60), (cx - 50, cy - 60)], fill=inner_fill)

        # Collar
        draw.rounded_rectangle([cx - 125, cy - 105, cx + 125, cy - 75], radius=15, fill=accent_gold, outline=gold_highlight, width=6)

        # Queen Coronet (5 radiating spikes with pearls)
        coronet_pts = [
            (cx - 140, cy - 250),  # outer left
            (cx - 80, cy - 140),
            (cx - 50, cy - 270),   # mid left
            (cx - 20, cy - 140),
            (cx, cy - 300),        # center spike (tallest)
            (cx + 20, cy - 140),
            (cx + 50, cy - 270),   # mid right
            (cx + 80, cy - 140),
            (cx + 140, cy - 250),  # outer right
            (cx + 115, cy - 90),
            (cx - 115, cy - 90),
        ]
        draw.polygon(coronet_pts, fill=primary_fill, outline=accent_gold)
        # Pearls on coronet tips
        pearl_coords = [
            (cx - 140, cy - 250),
            (cx - 50, cy - 270),
            (cx, cy - 300),
            (cx + 50, cy - 270),
            (cx + 140, cy - 250)
        ]
        for px, py in pearl_coords:
            draw.ellipse([px - 25, py - 25, px + 25, py + 25], fill=accent_gold, outline=gold_highlight, width=6)

    # 6. KING
    elif piece_char == "k":
        draw_base_pedestal(s_draw, offset_y=25, fill_col=shadow_color, trim_col=(0, 0, 0, 0))
        draw_base_pedestal(draw)

        # Royal robe pillar
        draw.polygon([
            (cx - 145, cy + 220), (cx + 145, cy + 220),
            (cx + 85, cy + 40), (cx + 120, cy - 70),
            (cx - 120, cy - 70), (cx - 85, cy + 40)
        ], fill=primary_fill, outline=accent_gold)
        draw.polygon([(cx - 85, cy + 190), (cx + 85, cy + 190), (cx + 55, cy - 50), (cx - 55, cy - 50)], fill=inner_fill)

        # Collar
        draw.rounded_rectangle([cx - 130, cy - 95, cx + 130, cy - 65], radius=15, fill=accent_gold, outline=gold_highlight, width=6)

        # Imperial Crown Dome
        draw.ellipse([cx - 135, cy - 235, cx + 135, cy - 65], fill=primary_fill, outline=accent_gold, width=14)
        draw.ellipse([cx - 90, cy - 200, cx + 90, cy - 85], fill=inner_fill)

        # Crown side arches
        draw.line([(cx - 120, cy - 150), (cx - 40, cy - 220)], fill=accent_gold, width=10)
        draw.line([(cx + 120, cy - 150), (cx + 40, cy - 220)], fill=accent_gold, width=10)

        # Grand Imperial Cross atop the crown
        cross_y = cy - 280
        # Vertical crossbar
        draw.rectangle([cx - 20, cross_y - 80, cx + 20, cross_y + 40], fill=accent_gold, outline=gold_highlight, width=6)
        # Horizontal crossbar
        draw.rectangle([cx - 55, cross_y - 45, cx + 55, cross_y - 15], fill=accent_gold, outline=gold_highlight, width=6)
        # Central jewel
        draw.ellipse([cx - 12, cross_y - 37, cx + 12, cross_y - 23], fill=(235, 60, 60))

    # Apply soft Gaussian blur to shadow layer and composite
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=18))
    composite = Image.alpha_composite(shadow_img, img)

    # Downscale with high quality LANCZOS resampling to target size
    final_img = composite.resize((target_size, target_size), Image.Resampling.LANCZOS)
    return final_img


def generate_piece_images():
    """Generates all piece textures for themes into assets/pieces/."""
    pieces = ["k", "q", "r", "b", "n", "p"]
    colors = ["w", "b"]
    themes = ["Shadow Gold", "Neon Cyber", "Classic Slate"]

    for theme in themes:
        theme_slug = theme.lower().replace(" ", "_")
        folder = os.path.join(PIECES_DIR, theme_slug)
        os.makedirs(folder, exist_ok=True)

        for col in colors:
            for p in pieces:
                filename = f"{col}_{p}.png"
                filepath = os.path.join(folder, filename)
                img = draw_supersampled_piece(p, col, theme=theme, target_size=256)
                img.save(filepath, "PNG")

        # Also place default theme files directly in assets/pieces/ for easy fallback
        if theme == "Shadow Gold":
            for col in colors:
                for p in pieces:
                    filename = f"{col}_{p}.png"
                    filepath = os.path.join(PIECES_DIR, filename)
                    img = draw_supersampled_piece(p, col, theme=theme, target_size=256)
                    img.save(filepath, "PNG")

    print("[AssetGenerator] All piece textures generated successfully.")


if __name__ == "__main__":
    generate_sounds()
    generate_piece_images()
