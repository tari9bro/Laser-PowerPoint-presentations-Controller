"""
config.py — All tunable settings for the Laser PPT Controller.
"""

import numpy as np

# ── Camera ─────────────────────────────────────────────────────
CAMERA_INDEX: int = 0

# ── Freeze / trigger logic ─────────────────────────────────────
FREEZE_DURATION: float = 0.2   # was 2.0 — much faster for flickering detection
FREEZE_RADIUS:   int   = 35    # was 20 — more forgiving for hand jitter
COOLDOWN:        float = 1.5

# ── Zone geometry ──────────────────────────────────────────────
ZONE_SPLIT: float = 0.35

# ── Laser detection — TUNED from real laser image analysis ─────
#
# This laser appears PINKISH-WHITE on camera due to overexposure.
# HSV profile (measured):
#   H = 0–20   (warm pinkish-orange tint)
#   S = 0–80   (very low saturation — washed out / overexposed)
#   V = 180–255 (extremely bright)
#
# Detection uses BRIGHTNESS as the primary signal,
# combined with a warm hue and tiny size.

LOWER_LASER = np.array([0,   0,  180], dtype=np.uint8)
UPPER_LASER = np.array([30, 80,  255], dtype=np.uint8)

# Legacy red ranges kept for fallback
LOWER_RED1 = np.array([0,   120, 120], dtype=np.uint8)
UPPER_RED1 = np.array([10,  255, 255], dtype=np.uint8)
LOWER_RED2 = np.array([170, 120, 120], dtype=np.uint8)
UPPER_RED2 = np.array([180, 255, 255], dtype=np.uint8)

# Size gates (px²)
# LOWERED to handle very small laser dots that move
MIN_CONTOUR_AREA: int = 10        # was 50 — now catches tiny dots
MAX_CONTOUR_AREA: int = 5000      # was 3000 — more forgiving

# Circularity threshold (0=any shape, 1=perfect circle)
# LOWERED to be more tolerant of hand jitter + distortion
MIN_CIRCULARITY: float = 0.35     # was 0.40 — more forgiving

# Minimum HSV brightness to count as laser
# LOWERED slightly for dim/distant lasers
MIN_LASER_BRIGHTNESS: int = 170   # was 180

# Background learning
BG_LEARNING_FRAMES: int = 30
