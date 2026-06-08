"""
slide_reader.py
---------------
Gets a reference image of the current slide to build a red-content mask.

Priority order:
  1. PowerPoint COM automation  — exports exact current slide as PNG
  2. Monitor screenshot          — captures what's displayed on screen
  3. None                        — red blocking disabled (safe fallback)

IMPORTANT: The camera live feed is NEVER used as the reference image.
  Using a camera frame would risk capturing the laser glow itself,
  which would permanently block laser detection.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

import cv2
import numpy as np


# ──────────────────────────────────────────────────────────────
# Strategy 1 — PowerPoint COM automation
# ──────────────────────────────────────────────────────────────

def _get_slide_via_com(slide_index: int = 0) -> Optional[np.ndarray]:
    """
    Ask the running PowerPoint instance to export the current slide.
    Returns BGR image or None.
    """
    try:
        import win32com.client  # type: ignore
    except ImportError:
        return None

    try:
        ppt = win32com.client.GetActiveObject("PowerPoint.Application")
        prs = ppt.ActivePresentation

        # Try to get the currently displayed slide index
        try:
            current = ppt.SlideShowWindows(1).View.CurrentShowingSlide.SlideIndex
        except Exception:
            current = max(1, slide_index + 1)

        current = max(1, min(current, prs.Slides.Count))
        slide   = prs.Slides(current)

        tmp = os.path.join(tempfile.gettempdir(), "_laser_slide_ref.png")
        slide.Export(tmp, "PNG", 1280, 720)

        img = cv2.imread(tmp)
        if img is not None:
            print(
                f"  [SlideReader] ✅ PowerPoint COM — "
                f"slide {current}/{prs.Slides.Count}"
            )
        return img

    except Exception as e:
        print(f"  [SlideReader] COM unavailable ({e})")
        return None


# ──────────────────────────────────────────────────────────────
# Strategy 2 — Screenshot of monitor
# ──────────────────────────────────────────────────────────────

def _get_slide_via_screenshot() -> Optional[np.ndarray]:
    """
    Capture the primary monitor. Works when the slide is visible
    on screen but PowerPoint COM is not available.
    Returns BGR image or None.
    """
    try:
        from PIL import ImageGrab  # type: ignore
        shot = ImageGrab.grab()
        img  = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
        img  = cv2.resize(img, (1280, 720))
        print("  [SlideReader] 📸 Screenshot captured as slide reference.")
        return img
    except Exception as e:
        print(f"  [SlideReader] Screenshot failed ({e})")
        return None


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────

def get_slide_reference(slide_index: int = 0) -> Optional[np.ndarray]:
    """
    Return a BGR image of the current slide using the best
    available strategy. Returns None if all strategies fail.

    NOTE: Does NOT use the camera feed — that would risk
    capturing the laser dot and permanently blocking it.
    """
    print("\n[SlideReader] Getting slide reference...")

    img = _get_slide_via_com(slide_index)
    if img is not None:
        return img

    img = _get_slide_via_screenshot()
    if img is not None:
        return img

    print(
        "  [SlideReader] ⚠️  No slide reference available.\n"
        "  Red slide content blocking is disabled.\n"
        "  Laser detection will still work normally."
    )
    return None


# ──────────────────────────────────────────────────────────────
# Red mask extractor
# ──────────────────────────────────────────────────────────────

def extract_red_mask(slide_img: np.ndarray) -> np.ndarray:
    """
    Build a binary mask of red regions in the slide image.
    This mask is passed to detect_laser() to permanently exclude
    slide red content from laser detection.

    Uses SATURATED red ranges (typical of designed slide content)
    deliberately different from the overexposed low-saturation
    laser dot profile, so the laser itself is never blocked.

    Returns:
        Single-channel uint8 mask: 255 = red region, 0 = safe.
    """
    hsv = cv2.cvtColor(slide_img, cv2.COLOR_BGR2HSV)

    # Saturated red — typical PowerPoint design colours
    # Note: S >= 80 means real red, NOT the overexposed laser (S < 80)
    lower1 = np.array([0,   80,  60], dtype=np.uint8)
    upper1 = np.array([12, 255, 255], dtype=np.uint8)
    lower2 = np.array([165, 80,  60], dtype=np.uint8)
    upper2 = np.array([180, 255, 255], dtype=np.uint8)

    mask1    = cv2.inRange(hsv, lower1, upper1)
    mask2    = cv2.inRange(hsv, lower2, upper2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # Dilate to also cover colour halos and anti-aliased edges
    kernel   = np.ones((9, 9), np.uint8)
    red_mask = cv2.dilate(red_mask, kernel, iterations=2)

    blocked = cv2.countNonZero(red_mask)
    total   = slide_img.shape[0] * slide_img.shape[1]
    pct     = 100.0 * blocked / total

    if blocked > 0:
        print(
            f"  [RedMask] Blocked {blocked:,} px "
            f"({pct:.1f}% of frame) as slide red content."
        )
    else:
        print("  [RedMask] No red content found in slide — nothing blocked.")

    return red_mask
