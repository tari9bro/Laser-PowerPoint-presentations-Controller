"""
detector.py
-----------
Red-laser detection via OpenCV HSV masking, and freeze-detection logic.
"""

import math
import time
from typing import Optional, Tuple

import cv2
import numpy as np

from config import (
    FREEZE_DURATION,
    FREEZE_RADIUS,
    LOWER_RED1,
    LOWER_RED2,
    MIN_CONTOUR_AREA,
    UPPER_RED1,
    UPPER_RED2,
)

# ── Type aliases ───────────────────────────────────────────────
Point = Tuple[int, int]


# ──────────────────────────────────────────────────────────────
# Laser detection
# ──────────────────────────────────────────────────────────────

def detect_laser(frame: np.ndarray) -> Optional[Point]:
    """
    Locate the brightest red laser dot in *frame*.

    Pipeline:
      BGR → HSV → two red masks → merge → morphological cleanup
      → find contours → largest contour → enclosing circle centre

    Returns:
        (x, y) integer pixel coordinates, or ``None`` if no dot found.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(hsv, LOWER_RED1, UPPER_RED1)
    mask2 = cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    mask  = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((3, 3), np.uint8)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,   kernel)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_CONTOUR_AREA:
        return None

    (cx, cy), _ = cv2.minEnclosingCircle(largest)
    return int(cx), int(cy)


# ──────────────────────────────────────────────────────────────
# Freeze detector
# ──────────────────────────────────────────────────────────────

class FreezeDetector:
    """
    Determines whether a laser dot has been stationary long enough
    to be treated as an intentional slide-change command.

    Logic per frame:
    - No laser → reset.
    - Laser moved > FREEZE_RADIUS from anchor → reset anchor & timer.
    - Laser within FREEZE_RADIUS for >= FREEZE_DURATION → frozen = True.

    After an action fires, call :meth:`reset` so the presenter must
    deliberately re-aim before the next command.
    """

    def __init__(self) -> None:
        self._anchor: Optional[Point] = None
        self._start:  Optional[float] = None
        self._fired:  bool            = False

    # ------------------------------------------------------------------
    def update(self, pos: Optional[Point]) -> Tuple[bool, float]:
        """
        Feed the latest laser position.

        Args:
            pos: ``(x, y)`` from :func:`detect_laser`, or ``None``.

        Returns:
            ``(frozen, progress)`` where *frozen* is ``True`` the first
            frame the hold threshold is crossed, and *progress* is a
            0.0–1.0 value suitable for a progress indicator.
        """
        if pos is None:
            self._reset()
            return False, 0.0

        if self._anchor is None:
            self._anchor = pos
            self._start  = time.monotonic()
            self._fired  = False
            return False, 0.0

        if _distance(pos, self._anchor) > FREEZE_RADIUS:
            self._anchor = pos
            self._start  = time.monotonic()
            self._fired  = False
            return False, 0.0

        elapsed  = time.monotonic() - self._start       # type: ignore[operator]
        progress = min(elapsed / FREEZE_DURATION, 1.0)

        if elapsed >= FREEZE_DURATION and not self._fired:
            self._fired = True
            return True, 1.0

        return False, progress

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Reset all tracking state (call after an action fires)."""
        self._reset()

    def _reset(self) -> None:
        self._anchor = None
        self._start  = None
        self._fired  = False


# ── Helpers ────────────────────────────────────────────────────

def _distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
