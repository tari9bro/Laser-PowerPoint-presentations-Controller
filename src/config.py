"""
config.py
---------
All tunable settings for the Laser PPT Controller.
Edit this file to adapt the app to your environment.
"""

import numpy as np

# ── Camera ────────────────────────────────────────────────────
CAMERA_INDEX: int = 0
"""
Index of the webcam to use.
0 = built-in / default camera.
Change to 1 or 2 if the wrong camera opens.
"""

# ── Freeze / trigger logic ─────────────────────────────────────
FREEZE_DURATION: float = 2.0
"""
Seconds the laser must remain STILL before a slide action fires.
Increase to require a longer hold; decrease for quicker response.
"""

FREEZE_RADIUS: int = 20
"""
Pixel radius within which the laser is considered 'still'.
Accounts for natural hand tremor. Raise if triggers fire too easily.
"""

COOLDOWN: float = 1.5
"""
Minimum seconds between two consecutive slide actions.
Prevents double-triggers after a freeze event.
"""

# ── Zone geometry ──────────────────────────────────────────────
ZONE_SPLIT: float = 0.35
"""
Fraction of the frame width that forms each action zone.
0.35 → left 35 % = Previous, right 35 % = Next, middle 30 % = neutral.
"""

# ── Laser detection ────────────────────────────────────────────
MIN_CONTOUR_AREA: int = 5
"""
Minimum contour area (pixels²) to be treated as a laser dot.
Raise this if random red objects trigger false positives.
"""

# HSV colour ranges for RED (red wraps around the hue wheel → two ranges)
LOWER_RED1 = np.array([0,   120, 120], dtype=np.uint8)
UPPER_RED1 = np.array([10,  255, 255], dtype=np.uint8)
LOWER_RED2 = np.array([170, 120, 120], dtype=np.uint8)
UPPER_RED2 = np.array([180, 255, 255], dtype=np.uint8)
