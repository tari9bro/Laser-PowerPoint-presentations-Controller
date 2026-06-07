"""
calibrator.py
-------------
Interactive calibration: user clicks the four corners of the
projection screen in the live camera feed.  OpenCV then computes
a Homography matrix that maps camera-space coordinates to
screen-space coordinates, correcting for any camera angle or offset.

UX improvements:
  - Clear on-screen instructions with visible SKIP button (press S or ESC)
  - Calibration is fully optional — app works without it
  - Status bar shows exactly what to do at each step
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np

Point = Tuple[int, int]

_CORNER_LABELS = [
    "1 — Top Left",
    "2 — Top Right",
    "3 — Bottom Right",
    "4 — Bottom Left",
]

_CORNER_HINTS = [
    "Click the TOP-LEFT corner of the projection screen",
    "Click the TOP-RIGHT corner of the projection screen",
    "Click the BOTTOM-RIGHT corner of the projection screen",
    "Click the BOTTOM-LEFT corner of the projection screen",
]


class Calibrator:
    """
    Encapsulates calibration state and the Homography transform.

    Usage::

        cal = Calibrator()
        cal.run(cap)                          # shows window, blocking
        x2, y2 = cal.transform(x, y, w, h)   # map any point afterward
    """

    def __init__(self) -> None:
        self._matrix:     Optional[np.ndarray] = None
        self._calibrated: bool                 = False

    # ──────────────────────────────────────────────────────────
    @property
    def is_calibrated(self) -> bool:
        return self._calibrated

    # ──────────────────────────────────────────────────────────
    def run(self, cap: cv2.VideoCapture) -> None:
        """
        Open a calibration window and block until the user has:
          - clicked all 4 corners (calibration applied), OR
          - pressed S / ESC / clicked the on-screen SKIP button (no calibration)

        Args:
            cap: An already-opened cv2.VideoCapture object.
        """
        ret, sample = cap.read()
        if not ret:
            print("[Calibrator] Cannot read from camera — skipping calibration.")
            return

        frame_h, frame_w = sample.shape[:2]
        clicked: List[List[int]] = []
        skip_requested = [False]   # mutable flag accessible in nested callback

        # ── Skip button geometry ───────────────────────────────
        btn = {
            "x1": frame_w - 160, "y1": frame_h - 55,
            "x2": frame_w - 10,  "y2": frame_h - 10,
        }

        def _on_mouse(event: int, x: int, y: int, flags: int, param) -> None:
            if event != cv2.EVENT_LBUTTONDOWN:
                return

            # Did user click the SKIP button?
            if btn["x1"] <= x <= btn["x2"] and btn["y1"] <= y <= btn["y2"]:
                skip_requested[0] = True
                return

            # Otherwise register a corner (max 4)
            if len(clicked) < 4:
                clicked.append([x, y])
                print(f"  Corner {len(clicked)}/4 — ({x}, {y})")

        win = "Laser PPT Controller — Calibration"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win, frame_w, frame_h)
        cv2.setMouseCallback(win, _on_mouse)

        _print_instructions()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            display = _draw_overlay(
                frame.copy(), clicked, frame_w, frame_h, btn
            )
            cv2.imshow(win, display)

            key = cv2.waitKey(1) & 0xFF

            # Skip: S key or ESC key or button click
            if key in (ord("s"), ord("S"), 27) or skip_requested[0]:
                print(
                    "\n  [Calibrator] Skipped — app will use raw camera "
                    "coordinates.\n"
                    "  Tip: recalibrate from the tray menu when you have "
                    "a projector.\n"
                )
                break

            # All 4 corners collected — auto-close after brief pause
            if len(clicked) == 4:
                cv2.waitKey(800)
                break

        cv2.destroyWindow(win)

        if len(clicked) == 4:
            self._compute(clicked, frame_w, frame_h)

    # ──────────────────────────────────────────────────────────
    def transform(
        self, x: int, y: int, frame_w: int, frame_h: int
    ) -> Tuple[int, int]:
        """
        Map a camera-space point to screen-space.
        Falls through unchanged if not calibrated.
        """
        if self._matrix is None:
            return x, y

        pt     = np.float32([[[x, y]]])
        result = cv2.perspectiveTransform(pt, self._matrix)
        tx, ty = result[0][0]
        return (
            int(max(0, min(frame_w - 1, tx))),
            int(max(0, min(frame_h - 1, ty))),
        )

    # ──────────────────────────────────────────────────────────
    def _compute(
        self, corners: List[List[int]], frame_w: int, frame_h: int
    ) -> None:
        src = np.float32(corners)
        dst = np.float32([
            [0,           0          ],
            [frame_w - 1, 0          ],
            [frame_w - 1, frame_h - 1],
            [0,           frame_h - 1],
        ])
        self._matrix, _  = cv2.findHomography(src, dst)
        self._calibrated = True
        print(
            "  [Calibrator] ✅ Homography matrix computed — "
            "calibration complete.\n"
        )


# ──────────────────────────────────────────────────────────────
# Drawing helpers
# ──────────────────────────────────────────────────────────────

def _draw_overlay(
    frame: np.ndarray,
    clicked: List[List[int]],
    frame_w: int,
    frame_h: int,
    btn: dict,
) -> np.ndarray:

    # ── Semi-transparent dark top bar ─────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame_w, 70), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # ── Title ─────────────────────────────────────────────────
    cv2.putText(
        frame, "CALIBRATION  —  Click the 4 corners of your projection screen",
        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2,
    )

    # ── Current instruction ───────────────────────────────────
    if len(clicked) < 4:
        hint = _CORNER_HINTS[len(clicked)]
        cv2.putText(
            frame, hint,
            (12, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2,
        )
    else:
        cv2.putText(
            frame, "All 4 corners set!  Closing...",
            (12, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 255, 50), 2,
        )

    # ── Clicked corner dots + labels ──────────────────────────
    for i, pt in enumerate(clicked):
        cv2.circle(frame, tuple(pt), 10, (0, 255, 0), -1)
        cv2.circle(frame, tuple(pt), 12, (255, 255, 255), 1)
        cv2.putText(
            frame, _CORNER_LABELS[i],
            (pt[0] + 16, pt[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
        )

    # ── Polygon outline ───────────────────────────────────────
    if len(clicked) >= 2:
        pts = np.array(clicked, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], len(clicked) == 4, (0, 255, 255), 2)

    # ── Corner counter badge ──────────────────────────────────
    badge = f"{len(clicked)} / 4  corners"
    cv2.putText(
        frame, badge,
        (12, frame_h - 18),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2,
    )

    # ── SKIP button ───────────────────────────────────────────
    # Button background
    cv2.rectangle(
        frame,
        (btn["x1"], btn["y1"]), (btn["x2"], btn["y2"]),
        (40, 40, 200), -1,
    )
    cv2.rectangle(
        frame,
        (btn["x1"], btn["y1"]), (btn["x2"], btn["y2"]),
        (255, 255, 255), 1,
    )
    cv2.putText(
        frame, "SKIP  (S / ESC)",
        (btn["x1"] + 8, btn["y2"] - 12),
        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2,
    )

    return frame


def _print_instructions() -> None:
    sep = "─" * 60
    print(f"\n{sep}")
    print("  CALIBRATION")
    print("  Click the 4 corners of the projection screen in order:")
    for label in _CORNER_LABELS:
        print(f"    • {label}")
    print()
    print("  No projector right now?")
    print("  → Press S, ESC, or click the SKIP button on screen.")
    print("  → You can recalibrate later from the tray menu.")
    print(f"{sep}\n")
