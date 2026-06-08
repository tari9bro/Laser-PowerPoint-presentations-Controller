"""
detector.py
-----------
Laser detection tuned to a real overexposed pinkish-white laser dot.

Measured profile from actual camera image:
  H = 0–30   (slight warm/pinkish tint)
  S = 0–80   (very low — camera overexposure washes out colour)
  V = 180–255 (extremely bright — primary signal)

FOUR reliable filters for small, moving laser dots:
  1. Brightness  — laser is overexposed, slide content is not
  2. Size        — dot is tiny (10–5000 px²), lenient for hand jitter
  3. Circularity — dot is round, text/shapes/charts are not (≥0.35)
  4. Motion tracking — predicts laser position across frames

NOTE: Motion tracking helps find small dots that move slightly each frame
due to hand jitter. It tracks the last N positions and predicts motion
velocity to guide detection in subsequent frames.

Red slide content is handled separately via a STATIC mask built from
the PPT slide image or a screenshot — never from the live camera feed.
"""

import math
import time
from typing import Optional, Tuple

import cv2
import numpy as np

from src.config import (
    FREEZE_DURATION,
    FREEZE_RADIUS,
    LOWER_LASER,
    MAX_CONTOUR_AREA,
    MIN_CIRCULARITY,
    MIN_CONTOUR_AREA,
    MIN_LASER_BRIGHTNESS,
    UPPER_LASER,
)

Point = Tuple[int, int]

# Image border strip to ignore (camera edge noise)
_BORDER: int = 15


# ──────────────────────────────────────────────────────────────
# Laser motion tracker
# ──────────────────────────────────────────────────────────────

class LaserMotionTracker:
    """
    Tracks the laser position across frames to help detect small,
    moving dots. Handles hand jitter by using motion prediction.
    """
    def __init__(self, max_history: int = 3):
        self.positions: list[Point] = []
        self.max_history = max_history
    
    def update(self, pos: Optional[Point]) -> None:
        """Record a detected position."""
        if pos is not None:
            self.positions.append(pos)
            if len(self.positions) > self.max_history:
                self.positions.pop(0)
    
    def get_predicted_region(self, frame_w: int, frame_h: int, 
                            search_radius: int = 40) -> Optional[Tuple[int, int, int, int]]:
        """
        Return a search region (x, y, w, h) around predicted laser position.
        Returns None if no history yet.
        """
        if not self.positions:
            return None
        
        last = self.positions[-1]
        
        # Predict next position from velocity (if we have 2+ points)
        if len(self.positions) >= 2:
            prev = self.positions[-2]
            vx = last[0] - prev[0]
            vy = last[1] - prev[1]
            px = last[0] + vx  # predicted x
            py = last[1] + vy  # predicted y
        else:
            px, py = last
        
        # Constrain to frame
        x1 = max(0, px - search_radius)
        y1 = max(0, py - search_radius)
        x2 = min(frame_w, px + search_radius)
        y2 = min(frame_h, py + search_radius)
        
        return (x1, y1, x2 - x1, y2 - y1)
    
    def reset(self) -> None:
        """Clear position history."""
        self.positions.clear()


# ──────────────────────────────────────────────────────────────
# Temporal position smoother (reduces jitter)
# ──────────────────────────────────────────────────────────────

class PositionSmoother:
    """
    Smooths position jitter by averaging recent detections.
    Reduces false negatives from occasional position jumps.
    """
    def __init__(self, window_size: int = 3):
        self.window_size = window_size
        self.positions: list[Point] = []
    
    def update(self, pos: Optional[Point]) -> Optional[Point]:
        """
        Add a position and return smoothed result.
        Returns None if we don't have enough history yet.
        """
        if pos is not None:
            self.positions.append(pos)
            if len(self.positions) > self.window_size:
                self.positions.pop(0)
        
        if not self.positions:
            return None
        
        # Return average if we have enough samples
        if len(self.positions) >= self.window_size:
            avg_x = int(sum(p[0] for p in self.positions) / len(self.positions))
            avg_y = int(sum(p[1] for p in self.positions) / len(self.positions))
            return (avg_x, avg_y)
        
        # Partial buffer - return last position
        return self.positions[-1]
    
    def reset(self) -> None:
        self.positions.clear()


# ──────────────────────────────────────────────────────────────
# Laser detection
# ──────────────────────────────────────────────────────────────

# Global motion tracker for small moving dots
_motion_tracker = LaserMotionTracker(max_history=5)
_position_smoother = PositionSmoother(window_size=3)


def detect_laser(
    frame:    np.ndarray,
    red_mask: Optional[np.ndarray] = None,
) -> Optional[Point]:
    """
    Locate the laser dot in *frame*.
    Uses motion prediction to help find small, moving dots.

    Args:
        frame:    Raw BGR camera frame.
        red_mask: Optional binary mask (255 = red slide region to ignore).
                  Built from a PPT slide export or monitor screenshot —
                  NEVER from a live camera frame.

    Returns:
        (x, y) integer pixel coordinates, or None.
    """
    h, w = frame.shape[:2]

    hsv          = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    _, _, v_chan = cv2.split(hsv)

    # ── Filter 1: Brightness ───────────────────────────────────
    # Laser dot is severely overexposed. Slide content is not.
    _, bright_mask = cv2.threshold(
        v_chan, MIN_LASER_BRIGHTNESS, 255, cv2.THRESH_BINARY
    )

    # ── Colour mask ────────────────────────────────────────────
    # Low-saturation warm tint — the overexposed laser signature
    color_mask = cv2.inRange(hsv, LOWER_LASER, UPPER_LASER)

    # Both conditions must be true
    mask = cv2.bitwise_and(color_mask, bright_mask)

    # ── Block red slide regions (static mask from PPT) ─────────
    if red_mask is not None:
        rm = red_mask
        if rm.shape[:2] != (h, w):
            rm = cv2.resize(rm, (w, h), interpolation=cv2.INTER_NEAREST)
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(rm))

    # ── Ignore image boundaries (camera sensor noise) ──────────
    mask[:_BORDER, :]   = 0
    mask[-_BORDER:, :]  = 0
    mask[:, :_BORDER]   = 0
    mask[:, -_BORDER:]  = 0

    # ── Morphological cleanup (gentler for small dots) ─────────
    k    = np.ones((3, 3), np.uint8)
    # Single pass to preserve tiny dots
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=1)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None

    # ── Filters 2 & 3: Size + Circularity ─────────────────────
    # More lenient for hand-jitter and small moving dots
    best_candidate = None
    best_score     = -1.0
    candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)

        # Filter 2 — size gate (very lenient now)
        if area < MIN_CONTOUR_AREA or area > MAX_CONTOUR_AREA:
            continue

        # Filter 3 — circularity gate (lenient for distorted small dots)
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = (4 * math.pi * area) / (perimeter ** 2)
        if circularity < MIN_CIRCULARITY:
            continue

        (cx, cy), radius = cv2.minEnclosingCircle(cnt)
        cx, cy = int(cx), int(cy)

        # Extra boundary check on the centre point
        if not (_BORDER < cy < h - _BORDER and _BORDER < cx < w - _BORDER):
            continue

        # Score: prefer bright + round → most laser-like candidate wins
        brightness = float(v_chan[cy, cx])
        score      = circularity * (brightness / 255.0)
        
        candidates.append((score, (cx, cy), cnt))

        if score > best_score:
            best_score     = score
            best_candidate = cnt

    if best_candidate is None:
        _motion_tracker.reset()
        return None

    (cx, cy), _ = cv2.minEnclosingCircle(best_candidate)
    pos = (int(cx), int(cy))
    
    # Update motion tracker
    _motion_tracker.update(pos)
    
    # Apply temporal smoothing to reduce jitter
    smoothed_pos = _position_smoother.update(pos)
    
    return smoothed_pos if smoothed_pos is not None else pos


# ──────────────────────────────────────────────────────────────
# Freeze detector
# ──────────────────────────────────────────────────────────────

class FreezeDetector:
    """
    Fires once when the laser stays within FREEZE_RADIUS pixels
    for FREEZE_DURATION seconds — but tolerates occasional frame drops.

    Instead of requiring 100% continuous detection, it only fires if:
    - The laser appears in >= 80% of recent frames
    - It stays within FREEZE_RADIUS for FREEZE_DURATION
    
    This handles hand jitter and occasional detection glitches.
    """

    def __init__(self, history_size: int = 10) -> None:
        self._anchor: Optional[Point] = None
        self._start:  Optional[float] = None
        self._fired:  bool            = False
        self._history: list[Optional[Point]] = []
        self._history_size = history_size
        self._last_detection_time = 0.0

    # ----------------------------------------------------------
    def update(self, pos: Optional[Point]) -> Tuple[bool, float]:
        """
        Args:
            pos: Current laser position or None.

        Returns:
            (frozen, progress) where frozen is True exactly once
            when the threshold is first crossed, and progress is
            0.0–1.0 for optional UI feedback.
        """
        # Track detection history
        self._history.append(pos)
        if len(self._history) > self._history_size:
            self._history.pop(0)
        
        if pos is not None:
            self._last_detection_time = time.monotonic()
        
        # Count recent detections (not None)
        detections = sum(1 for p in self._history if p is not None)
        detection_ratio = detections / len(self._history) if self._history else 0.0
        
        # If we've lost detection for too long, reset completely
        current_time = time.monotonic()
        if (current_time - self._last_detection_time) > 0.5:  # No detection for 0.5s
            self._reset()
            return False, 0.0
        
        # Use the last detected position as anchor
        last_pos = next((p for p in reversed(self._history) if p is not None), None)
        if last_pos is None:
            self._reset()
            return False, 0.0
        
        if self._anchor is None:
            self._anchor = last_pos
            self._start  = time.monotonic()
            self._fired  = False
            return False, 0.0

        if _dist(last_pos, self._anchor) > FREEZE_RADIUS:
            self._anchor = last_pos
            self._start  = time.monotonic()
            self._fired  = False
            return False, 0.0

        # Only trigger if detection ratio is good AND time threshold met
        if detection_ratio < 0.7:  # Need at least 70% detection
            return False, detection_ratio

        elapsed  = time.monotonic() - self._start   # type: ignore[operator]
        progress = min(elapsed / FREEZE_DURATION, 1.0)

        if elapsed >= FREEZE_DURATION and not self._fired and detection_ratio >= 0.7:
            self._fired = True
            return True, 1.0

        return False, progress

    # ----------------------------------------------------------
    def reset(self) -> None:
        """Reset after an action fires."""
        self._reset()

    def _reset(self) -> None:
        self._anchor = None
        self._start  = None
        self._fired  = False
        self._history.clear()


# ── Helper ─────────────────────────────────────────────────────

def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
