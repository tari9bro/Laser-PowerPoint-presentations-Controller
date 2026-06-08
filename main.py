"""
main.py — Entry point for the Laser PPT Controller.
Double-click run.bat to launch.
"""

import sys
import threading
import time
from typing import Optional

import cv2
import numpy as np

from src import config
from src.calibrator   import Calibrator
from src.controller   import zone_to_action
from src.detector     import FreezeDetector, detect_laser
from src.slide_reader import extract_red_mask, get_slide_reference
from src.tray         import build_tray, start_icon_pulse

# ──────────────────────────────────────────────────────────────
# Shared state
# ──────────────────────────────────────────────────────────────
_state: dict = {
    "running":      True,
    "paused":       False,
    "calibrating":  False,
    "laser_seen":   False,
    "last_action":  "—",
    "calibrated":   False,
}
_lock = threading.Lock()


def _get_state() -> dict:
    with _lock:
        return dict(_state)


def _get_zone(x: int, frame_w: int) -> str:
    if x < frame_w * config.ZONE_SPLIT:
        return "left"
    if x > frame_w * (1 - config.ZONE_SPLIT):
        return "right"
    return "neutral"


# ──────────────────────────────────────────────────────────────
# Build red mask — PPT or screenshot only, never camera
# ──────────────────────────────────────────────────────────────

def _build_red_mask(slide_index: int = 0) -> Optional["cv2.typing.MatLike"]:
    ref = get_slide_reference(slide_index)
    if ref is None:
        return None
    return extract_red_mask(ref)


# ──────────────────────────────────────────────────────────────
# Camera / detection thread
# ──────────────────────────────────────────────────────────────

def _camera_loop(
    cap:        cv2.VideoCapture,
    calibrator: Calibrator,
    red_mask,
) -> None:

    freeze        = FreezeDetector()
    last_action_t = 0.0
    frame_count = 0
    last_laser_seen = False

    print(
        f"\n[Tracker] Active.\n"
        f"  Hold laser still {config.FREEZE_DURATION}s in "
        f"LEFT or RIGHT zone to change slide.\n"
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

        frame_count += 1
        frame_h, frame_w = frame.shape[:2]

        # ── Detect laser ───────────────────────────────────────
        pos = detect_laser(frame, red_mask=red_mask)
        laser_detected = pos is not None

        # Show detection status change (when laser appears or disappears)
        if laser_detected != last_laser_seen:
            if laser_detected:
                print(f"  🔴 [Frame {frame_count}] LASER DETECTED at {pos}")
            else:
                print(f"  ⚫ [Frame {frame_count}] Laser lost")
            last_laser_seen = laser_detected

        with _lock:
            _state["laser_seen"] = laser_detected

        # ── Apply Homography ───────────────────────────────────
        if pos is not None and calibrator.is_calibrated:
            pos = calibrator.transform(pos[0], pos[1], frame_w, frame_h)

        # ── Freeze detection ───────────────────────────────────
        frozen, hold_time = freeze.update(pos)
        
        # Show freeze progress when laser is held still
        if pos is not None and hold_time > 0.1:
            progress = min(hold_time / config.FREEZE_DURATION, 1.0)
            bar_len = int(progress * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            zone = _get_zone(pos[0], frame_w)
            print(f"  ⏱ Hold: [{bar}] {hold_time:.1f}s / {config.FREEZE_DURATION}s — Zone: {zone}", end='\r')

        if frozen and pos is not None:
            zone = _get_zone(pos[0], frame_w)
            if zone != "neutral":
                now = time.monotonic()
                if now - last_action_t > config.COOLDOWN:
                    action = zone_to_action(zone)
                    print(f"\n  ✅ [{action}] TRIGGERED! Laser held at {pos} for {config.FREEZE_DURATION}s")

                    with _lock:
                        _state["last_action"] = action
                        _state["calibrated"]  = calibrator.is_calibrated

                    last_action_t = now
                    freeze.reset()

                    # Refresh red mask for the new slide after brief render delay
                    def _refresh():
                        time.sleep(0.5)
                        new_mask = _build_red_mask()
                        nonlocal red_mask
                        if new_mask is not None:
                            red_mask = new_mask
                    threading.Thread(target=_refresh, daemon=True).start()

    cap.release()
    print("[Tracker] Camera released.")


# ──────────────────────────────────────────────────────────────
# Tray callbacks
# ──────────────────────────────────────────────────────────────

def _make_calibrate_cb(cap, calibrator):
    def _run():
        with _lock:
            _state["calibrating"] = True
        calibrator.run(cap)
        with _lock:
            _state["calibrating"] = False
            _state["calibrated"]  = calibrator.is_calibrated
    def cb():
        threading.Thread(target=_run, daemon=True, name="Calibration").start()
    return cb


def _make_toggle_pause():
    def cb():
        with _lock:
            _state["paused"] = not _state["paused"]
            lbl = "PAUSED" if _state["paused"] else "RESUMED"
        print(f"  [Tray] Detection {lbl}.")
    return cb


def _make_show_status():
    def cb():
        s   = _get_state()
        sep = "─" * 42
        print(f"\n{sep}")
        print("  STATUS")
        print(f"  Calibrated   : {'✅' if s['calibrated']  else '❌ (use tray → Calibrate)'}")
        print(f"  Laser seen   : {'✅' if s['laser_seen']  else '❌'}")
        print(f"  Paused       : {'✅' if s['paused']       else '❌'}")
        print(f"  Last action  : {s['last_action']}")
        print(f"  Freeze time  : {config.FREEZE_DURATION}s")
        print(f"  Freeze radius: {config.FREEZE_RADIUS}px")
        print(f"{sep}\n")
    return cb


def _make_quit_cb(stop_event):
    def cb(icon):
        print("\n[App] Shutting down…")
        with _lock:
            _state["running"] = False
        stop_event.set()
        icon.stop()
    return cb


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────

def main() -> None:
    _print_banner()

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[Error] Cannot open camera (index {config.CAMERA_INDEX}).")
        sys.exit(1)

    ret, _ = cap.read()
    if not ret:
        print("[Error] Cannot read frame from camera.")
        sys.exit(1)

    # Calibration (optional, shows window with SKIP button)
    calibrator = Calibrator()
    calibrator.run(cap)

    # Build red mask from PPT or screenshot (never from camera)
    red_mask = _build_red_mask()

    # Start detection thread
    cam_thread = threading.Thread(
        target=_camera_loop,
        args=(cap, calibrator, red_mask),
        daemon=True,
        name="CameraLoop",
    )
    cam_thread.start()

    stop_event = threading.Event()

    tray = build_tray(
        on_calibrate    = _make_calibrate_cb(cap, calibrator),
        on_toggle_pause = _make_toggle_pause(),
        on_show_status  = _make_show_status(),
        on_quit         = _make_quit_cb(stop_event),
        freeze_duration = config.FREEZE_DURATION,
    )

    start_icon_pulse(tray, _get_state, stop_event)
    print("[App] Running in tray. Right-click icon to control.\n")
    tray.run()

    with _lock:
        _state["running"] = False
    print("[App] Goodbye.")


def _print_banner() -> None:
    print("""
╔═══════════════════════════════════════════════════╗
║          🔴  Laser PPT Controller                 ║
║                                                   ║
║  LEFT  zone (35%) → ◀ Previous slide             ║
║  RIGHT zone (35%) → ▶ Next slide                 ║
║  Hold still for {dur}s to trigger                  ║
║                                                   ║
║  PPT open   → reads current slide automatically  ║
║  PPT closed → screenshot used as reference       ║
║  No reference → detection works without masking  ║
╚═══════════════════════════════════════════════════╝
""".format(dur=config.FREEZE_DURATION))


if __name__ == "__main__":
    main()
