"""
tray.py
-------
System-tray icon and menu for the Laser PPT Controller.
The icon colour reflects app state at a glance:

  🟢  Green  –  running, no laser detected
  🔴  Red    –  laser currently visible in camera feed
  ⚫  Gray   –  detection paused by user
"""

import threading
import time
from typing import Callable

import pystray
from PIL import Image, ImageDraw

# Colour palette (R, G, B)
_PALETTE = {
    "green": (50,  205,  50),
    "red":   (220,  50,  50),
    "gray":  (120, 120, 120),
}


def make_icon(color: str = "green") -> Image.Image:
    """Return a 64×64 RGBA circle image for the tray."""
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=_PALETTE.get(color, _PALETTE["gray"]))
    return img


def build_tray(
    *,
    on_calibrate:     Callable,
    on_toggle_pause:  Callable,
    on_show_status:   Callable,
    on_quit:          Callable,
    freeze_duration:  float,
) -> pystray.Icon:
    """
    Construct and return the pystray Icon (not yet running).

    All callback callables receive ``(icon, item)`` as pystray passes them.
    """

    def _calibrate(icon, item):
        on_calibrate()

    def _pause(icon, item):
        on_toggle_pause()

    def _status(icon, item):
        on_show_status()

    def _quit(icon, item):
        on_quit(icon)

    menu = pystray.Menu(
        pystray.MenuItem("📐  Calibrate",        _calibrate),
        pystray.MenuItem("⏸   Pause / Resume",   _pause),
        pystray.MenuItem("📊  Show Status",       _status),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌  Quit",              _quit),
    )

    return pystray.Icon(
        name  = "LaserPPTController",
        icon  = make_icon("green"),
        title = f"Laser PPT Controller  |  Hold {freeze_duration}s to change slide",
        menu  = menu,
    )


def start_icon_pulse(tray: pystray.Icon,
                     get_state: Callable[[], dict],
                     stop_event: threading.Event) -> threading.Thread:
    """
    Spawn a daemon thread that updates the tray icon colour every 300 ms.

    Args:
        tray:       The pystray Icon instance.
        get_state:  Zero-arg callable returning a dict with keys
                    ``paused`` (bool) and ``laser_seen`` (bool).
        stop_event: ``threading.Event`` – set it to stop the thread.
    """

    def _pulse():
        while not stop_event.is_set():
            s     = get_state()
            color = "gray" if s["paused"] else ("red" if s["laser_seen"] else "green")
            try:
                tray.icon = make_icon(color)
            except Exception:
                pass
            time.sleep(0.3)

    t = threading.Thread(target=_pulse, daemon=True, name="IconPulse")
    t.start()
    return t
