"""
controller.py
-------------
Translates a zone name into a PowerPoint keyboard action.

Keeps pyautogui calls in one place so the rest of the codebase
never touches the presentation layer directly.
"""

import pyautogui

# Disable the fail-safe corner-of-screen crash guard so the background
# thread never raises an exception during normal operation.
pyautogui.FAILSAFE = False


def next_slide() -> None:
    """Send the RIGHT ARROW key → advance one slide in PowerPoint."""
    pyautogui.press("right")


def prev_slide() -> None:
    """Send the LEFT ARROW key → go back one slide in PowerPoint."""
    pyautogui.press("left")


def zone_to_action(zone: str) -> str:
    """
    Execute the slide action for *zone* and return a human-readable label.

    Args:
        zone: ``"left"`` or ``"right"``.

    Returns:
        Action label string, e.g. ``"▶  Next slide"``.

    Raises:
        ValueError: If *zone* is not ``"left"`` or ``"right"``.
    """
    if zone == "right":
        next_slide()
        return "▶  Next slide"
    elif zone == "left":
        prev_slide()
        return "◀  Previous slide"
    else:
        raise ValueError(f"zone_to_action() called with non-action zone: {zone!r}")
