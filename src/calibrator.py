"""
calibrator.py
-------------
Interactive calibration: user clicks the four corners of the
projection screen in the live camera feed.  OpenCV then computes
a Homography matrix that maps camera-space coordinates to
screen-space coordinates, correcting for any camera angle or offset.
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np

Point = Tuple[int, int]

# Corner labels shown in the calibration window
_LABELS = ["1: Top-Left", "2: Top-Right", "3: Bottom-Right", "4: Bottom-Left"]
_COLORS = {
    "dot":    (0, 255,   0),
    "poly":   (0, 255, 255),
    "text":   (255, 255, 255),
    "done":   (0, 255,   0),
}


class Calibrator:
    """
    Encapsulates calibration state and the Homography transform.

    Usage::

        cal = Calibrator()
        cal.run(cap)              # blocking – shows window until done/skipped
        x2, y2 = cal.transform(x, y)   # map any point afterward
    """

    def __init__(self) -> None:
        self._matrix:    Optional[np.ndarray] = None
        self._calibrated: bool                = False

    # ------------------------------------------------------------------
    @property
    def is_calibrated(self) -> bool:
        return self._calibrated

    # ------------------------------------------------------------------
    def run(self, cap: cv2.VideoCapture) -> None:
        """
        Open a calibration window and block until the user has clicked
        4 corners **or** pressed ESC to skip.

        Args:
            cap: An already-opened ``cv2.VideoCapture`` object.
        """
        ret, sample = cap.read()
        if not ret:
            print("[Calibrator] Cannot read from camera – skipping calibration.")
            return

        frame_h, frame_w = sample.shape[:2]
        clicked: List[List[int]] = []

        def _on_mouse(event: int, x: int, y: int, flags: int, param: object) -> None:
            if event == cv2.EVENT_LBUTTONDOWN and len(clicked) < 4:
                clicked.append([x, y])
                print(f"  Corner {len(clicked)}/4  →  ({x}, {y})")

        win_name = "Calibration  |  Click the 4 corners of the projection screen  |  ESC to skip"
        cv2.namedWindow(win_name)
        cv2.setMouseCallback(win_name, _on_mouse)

        _print_instructions()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            display = _draw_overlay(frame.copy(), clicked, frame_w, frame_h)
            cv2.imshow(win_name, display)

            key = cv2.waitKey(1) & 0xFF

            if len(clicked) == 4:
                cv2.waitKey(800)   # brief pause so user sees the complete polygon
                break
            if key == 27:          # ESC
                print("  [Calibrator] Skipped – using raw camera coordinates.\n")
                break

        cv2.destroyWindow(win_name)

        if len(clicked) == 4:
            self._compute(clicked, frame_w, frame_h)

    # ------------------------------------------------------------------
    def transform(self, x: int, y: int,
                  frame_w: int, frame_h: int) -> Tuple[int, int]:
        """
        Map a camera-space point to screen-space using the stored
        Homography matrix.  Falls through unchanged if not calibrated.
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

    # ------------------------------------------------------------------
    def _compute(self, corners: List[List[int]],
                 frame_w: int, frame_h: int) -> None:
        src = np.float32(corners)
        dst = np.float32([
            [0,          0          ],
            [frame_w - 1, 0         ],
            [frame_w - 1, frame_h-1 ],
            [0,          frame_h - 1],
        ])
        self._matrix, _   = cv2.findHomography(src, dst)
        self._calibrated  = True
        print("  [Calibrator] ✅  Homography matrix computed – calibration complete.\n")


# ── Drawing helpers ────────────────────────────────────────────

def _draw_overlay(frame: np.ndarray,
                  clicked: List[List[int]],
                  frame_w: int,
                  frame_h: int) -> np.ndarray:
    # Corner dots and labels
    for i, pt in enumerate(clicked):
        cv2.circle(frame, tuple(pt), 10, _COLORS["dot"], -1)
        cv2.putText(
            frame, _LABELS[i],
            (pt[0] + 14, pt[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            _COLORS["dot"], 2,
        )

    # Polygon outline
    if len(clicked) >= 2:
        pts = np.array(clicked, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], len(clicked) == 4, _COLORS["poly"], 2)

    # Status text
    if len(clicked) < 4:
        msg   = f"Click corner  {len(clicked) + 1} / 4"
        color = _COLORS["text"]
    else:
        msg   = "Done!  Closing calibration window..."
        color = _COLORS["done"]

    cv2.putText(frame, msg, (12, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
    return frame


def _print_instructions() -> None:
    sep = "─" * 58
    print(f"\n{sep}")
    print("  CALIBRATION")
    print("  Click the 4 corners of the projection screen in order:")
    for label in _LABELS:
        print(f"    • {label}")
    print("  Press ESC to skip calibration.")
    print(f"{sep}\n")
