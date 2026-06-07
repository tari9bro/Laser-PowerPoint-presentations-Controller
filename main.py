"""
main.py
-------
Entry point for the Laser PPT Controller.

Run with:
    python main.py

The app:
  1. Opens the webcam.
  2. Shows a calibration window (click 4 corners of the projection screen).
  3. Disappears into the system tray — PowerPoint stays in focus.
  4. Watches the camera feed in a background thread.
  5. When the laser holds still for FREEZE_DURATION seconds inside a
     left/right zone → fires the corresponding arrow key.

Right-click the tray icon to calibrate, pause, check status, or quit.
"""

import sys
import threading
import time

import cv2

import config
from calibrator import Calibrator
from controller import zone_to_action
from detector   import FreezeDetector, detect_laser
from tray       import build_tray, start_icon_pulse

# ──────────────────────────────────────────────────────────────
# Shared state
# ──────────────────────────────────────────────────────────────
_state: dict = {
    "running":     True,
    "paused":      False,
    "calibrating": False,
    "laser_seen":  False,
    "last_action": "—",
    "calibrated":  False,
}
_lock = threading.Lock()


def _get_state() -> dict:
    with _lock:
        return dict(_state)


# ──────────────────────────────────────────────────────────────
# Zone helper
# ──────────────────────────────────────────────────────────────

def _get_zone(x: int, frame_w: int) -> str:
    if x < frame_w * config.ZONE_SPLIT:
        return "left"
    if x > frame_w * (1 - config.ZONE_SPLIT):
        return "right"
    return "neutral"


# ──────────────────────────────────────────────────────────────
# Camera / detection thread
# ──────────────────────────────────────────────────────────────

def _camera_loop(cap: cv2.VideoCapture, calibrator: Calibrator) -> None:
    freeze        = FreezeDetector()
    last_action_t = 0.0

    print(
        f"[Tracker] Active — hold laser still for "
        f"{config.FREEZE_DURATION}s in a zone to change slide.\n"
    )

    while True:
        with _lock:
            if not _state["running"]:
                break
            paused      = _state["paused"]
            calibrating = _state["calibrating"]

        if calibrating:
            time.sleep(0.05)
            continue

        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        if paused:
            freeze.reset()
            time.sleep(0.1)
            continue

        frame_h, frame_w = frame.shape[:2]

        # Detect laser
        pos = detect_laser(frame)

        with _lock:
            _state["laser_seen"] = pos is not None

        # Apply Homography if calibrated
        if pos is not None and calibrator.is_calibrated:
            pos = calibrator.transform(pos[0], pos[1], frame_w, frame_h)

        # Freeze detection
        frozen, _progress = freeze.update(pos)

        if frozen and pos is not None:
            zone = _get_zone(pos[0], frame_w)
            if zone != "neutral":
                now = time.monotonic()
                if now - last_action_t > config.COOLDOWN:
                    action = zone_to_action(zone)
                    print(f"  [{action}]  laser frozen at {pos}")
                    with _lock:
                        _state["last_action"] = action
                        _state["calibrated"]  = calibrator.is_calibrated
                    last_action_t = now
                    freeze.reset()

    cap.release()
    print("[Tracker] Camera released.")


# ──────────────────────────────────────────────────────────────
# Tray callbacks
# ──────────────────────────────────────────────────────────────

def _make_calibrate_cb(cap: cv2.VideoCapture, calibrator: Calibrator):
    def _calibrate():
        with _lock:
            _state["calibrating"] = True
        calibrator.run(cap)
        with _lock:
            _state["calibrating"]  = False
            _state["calibrated"]   = calibrator.is_calibrated

    def callback():
        t = threading.Thread(target=_calibrate, daemon=True, name="Calibration")
        t.start()

    return callback


def _make_toggle_pause():
    def callback():
        with _lock:
            _state["paused"] = not _state["paused"]
            label = "PAUSED" if _state["paused"] else "RESUMED"
        print(f"  [Tray] Detection {label}.")
    return callback


def _make_show_status():
    def callback():
        s = _get_state()
        sep = "─" * 38
        print(f"\n{sep}")
        print("  STATUS")
        print(f"  Calibrated  : {'✅ Yes' if s['calibrated']  else '❌ No'}")
        print(f"  Laser seen  : {'✅ Yes' if s['laser_seen']  else '❌ No'}")
        print(f"  Paused      : {'✅ Yes' if s['paused']       else '❌ No'}")
        print(f"  Last action : {s['last_action']}")
        print(f"  Freeze time : {config.FREEZE_DURATION}s")
        print(f"  Freeze radius: {config.FREEZE_RADIUS}px")
        print(f"{sep}\n")
    return callback


def _make_quit_cb(stop_event: threading.Event):
    def callback(icon):
        print("\n[App] Shutting down…")
        with _lock:
            _state["running"] = False
        stop_event.set()
        icon.stop()
    return callback


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────

def main() -> None:
    _print_banner()

    # Open camera
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(
            f"[Error] Cannot open camera (index {config.CAMERA_INDEX}).\n"
            "        Try changing CAMERA_INDEX in src/config.py."
        )
        sys.exit(1)

    ret, sample = cap.read()
    if not ret:
        print("[Error] Cannot read a frame from the camera.")
        sys.exit(1)

    # Calibration (blocking, shows window)
    calibrator = Calibrator()
    calibrator.run(cap)

    # Background camera thread
    cam_thread = threading.Thread(
        target=_camera_loop,
        args=(cap, calibrator),
        daemon=True,
        name="CameraLoop",
    )
    cam_thread.start()

    # Stop event shared between tray pulse and quit callback
    stop_event = threading.Event()

    # Build tray
    tray = build_tray(
        on_calibrate    = _make_calibrate_cb(cap, calibrator),
        on_toggle_pause = _make_toggle_pause(),
        on_show_status  = _make_show_status(),
        on_quit         = _make_quit_cb(stop_event),
        freeze_duration = config.FREEZE_DURATION,
    )

    # Icon pulse thread
    start_icon_pulse(tray, _get_state, stop_event)

    print("[App] Running in system tray. Right-click the tray icon to control.\n")
    tray.run()   # blocks until quit

    # Ensure state is flushed for camera thread
    with _lock:
        _state["running"] = False

    print("[App] Goodbye.")


def _print_banner() -> None:
    banner = """
╔══════════════════════════════════════════════╗
║        🔴  Laser PPT Controller              ║
║                                              ║
║  Aim the laser at the LEFT  zone  → ◀ Prev  ║
║  Aim the laser at the RIGHT zone  → ▶ Next  ║
║  Hold still for {dur}s to trigger             ║
║                                              ║
║  Right-click tray icon for options           ║
╚══════════════════════════════════════════════╝
""".format(dur=config.FREEZE_DURATION)
    print(banner)


if __name__ == "__main__":
    main()
