<div align="center">

# 🔴 Laser PPT Controller

**Control your PowerPoint presentations using a red laser pointer and your laptop's built-in webcam.**

No clicker hardware. No Bluetooth dongle. No extra device.
Just your laser, your laptop, and a double-click.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green?logo=opencv)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-informational?logo=windows)](https://www.microsoft.com/windows)

</div>

---

## 📖 What Is This?

**Laser PPT Controller** is an open-source Python application that turns any **red laser pointer** into a wireless presentation remote.

It uses your laptop's **built-in webcam** to watch the projection wall. When you hold the laser still in the left or right zone of the slide for **2 seconds**, the app automatically presses the arrow key to change the slide — without touching the keyboard or any remote control.

The app runs **silently in the background** as a system tray icon while PowerPoint stays in full focus on the projector.

---

## 🎯 Who Is This For?

| User | Use Case |
|---|---|
| 👨‍🏫 Teachers & Trainers | Control slides while moving freely around the classroom |
| 🎤 Conference Speakers | Present without holding a remote clicker |
| 🧑‍💼 Lecturers | Point at content AND change slides with the same laser |
| 🏫 Training Centers | Works with any projector + laptop setup |

---

## 🚀 How It Works

### The Classroom Setup

```
┌──────────────────────────────────┐
│         PROJECTION WALL          │
│                                  │
│  [◀ PREV]  (neutral)  [NEXT ▶]  │
│   35 %       30 %       35 %    │
│                                  │
└──────────────────────────────────┘
             ↑ projected by
         [Projector]
             ↑ HDMI cable
    [Laptop on teacher's desk]
     • Runs PowerPoint (fullscreen)
     • Runs this app (system tray)
     • Built-in camera faces the wall ✅

  You (presenter) move freely in the room
  and aim the laser at the wall.
```

### The Freeze-to-Trigger Logic

This is the key design decision that makes the app practical in a real classroom:

```
Laser moves freely   →  NO action   (point at content for students)
Laser freezes 2s     →  SLIDE CHANGES   (intentional command)
```

You can point at anything on the slide as long as you want. The app only triggers when the dot **stops moving for exactly 2 full seconds** inside the left or right zone.

### The Detection Pipeline

```
Camera frame (BGR)
    → Convert to HSV colorspace
    → Two red masks  (hue 0–10  and  hue 170–180)
    → Merge masks + morphological cleanup
    → Find contours → largest contour → laser center (x, y)
    → Apply Homography correction  (if calibrated)
    → Check zone: left / neutral / right
    → FreezeDetector: still for 2 seconds?
    → pyautogui.press("left" or "right")
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🖱 **Double-click to install** | `setup.bat` handles everything — no terminal knowledge needed |
| 🖱 **Double-click to run** | `run.bat` launches the app every time |
| 🔴 **Red laser detection** | HSV colour masking with morphological noise cleanup |
| ⏱ **Freeze-to-trigger** | 2-second hold required — no accidental triggers while pointing |
| 📐 **Homography calibration** | Corrects for any camera angle, height, or offset |
| ⏭ **Calibration is optional** | Skip it if you have no projector yet — recalibrate anytime |
| 🖥 **Silent background mode** | Runs as a system tray icon — PowerPoint stays in focus |
| 🟢🔴⚫ **Visual status indicator** | Tray icon colour shows app state at a glance |
| ⚙️ **Single config file** | All settings in `src/config.py` — no deep code editing needed |
| 🧩 **Clean modular code** | Separated into detector / calibrator / controller / tray modules |
| 🔄 **Re-calibrate on the fly** | Right-click tray → Calibrate at any time during a session |
| ⏸ **Pause & resume** | Temporarily disable detection without quitting |

---

## 📦 Requirements

### Hardware
- A **laptop or desktop** with a webcam that faces the projection wall
- A **red laser pointer** (any standard presentation laser)
- A **projector** connected via HDMI *(not needed for testing)*

### Software
- **Python 3.9 or newer** — download from [python.org](https://www.python.org/downloads/)
  - ⚠️ During installation, check **"Add Python to PATH"**
- **Windows 10 or 11**

---

## 🛠 Installation — First Time Only

> You only do this once. After setup, just double-click `run.bat` every time.

### Step 1 — Download the project

Click the green **Code** button on GitHub → **Download ZIP** → extract the folder anywhere on your PC.

Or if you have Git:
```bash
git clone https://github.com/YOUR_USERNAME/laser-ppt-controller.git
```

### Step 2 — Double-click `setup.bat`

```
📁 laser-ppt-controller\
    ├── 👆 setup.bat   ← double-click this
    ├── run.bat
    └── ...
```

`setup.bat` will automatically:
- ✅ Check that Python is installed
- ✅ Create a virtual environment (`.venv` folder)
- ✅ Install all required libraries
- ✅ Verify everything works

When you see this message, setup is complete:

```
============================================
  Setup complete!
  Double-click run.bat to launch the app.
============================================
```

That's it. You never need to open a terminal.

---

## ▶️ Running the App — Every Time

```
📁 laser-ppt-controller\
    ├── setup.bat
    ├── 👆 run.bat   ← double-click this every time
    └── ...
```

Double-click **`run.bat`** — the app starts immediately.

---

## 📐 Calibration Window

When the app starts, a **calibration window** opens showing your camera feed.

### If you have a projector

Click the **4 corners** of the projection screen in this order:

```
  1 ─────────── 2
  │             │
  │  Projected  │
  │   Screen    │
  │             │
  4 ─────────── 3
```

The app draws a green polygon as you click. Once all 4 corners are set, the window closes automatically.

### If you don't have a projector right now

No problem — calibration is **completely optional**.

Press **S**, **ESC**, or click the **SKIP button** visible on screen:

```
┌──────────────────────────────────────────────────┐
│  CALIBRATION — Click the 4 corners of your       │
│  projection screen                               │
│  → Click the TOP-LEFT corner                     │
│                                                  │
│         [live camera feed]                       │
│                                                  │
│  0 / 4 corners              ┌────────────────┐  │
│                             │  SKIP (S/ESC)  │  │
└─────────────────────────────└────────────────┘──┘
```

The app works without calibration. You can recalibrate any time from the tray menu.

---

## 🎮 Using the App During a Presentation

### Recommended order

```
1. Open PowerPoint → start slideshow fullscreen on projector
2. Double-click run.bat
3. Complete calibration (or skip)
4. App disappears to system tray
5. Present freely!
```

### Slide Control

| What you want | What you do |
|---|---|
| **Next slide ▶** | Hold laser still in the **right 35%** of the screen for 2 seconds |
| **Previous slide ◀** | Hold laser still in the **left 35%** of the screen for 2 seconds |
| **Point at content** | Move the laser freely — nothing happens |

### Tray Icon — What the Colours Mean

Find the tray icon in the **bottom-right corner of the taskbar**:

| Icon Colour | Meaning |
|---|---|
| 🟢 Green | Running — no laser detected |
| 🔴 Red | Laser currently visible in camera |
| ⚫ Gray | Detection paused |

### Tray Menu — Right-Click the Icon

| Option | What It Does |
|---|---|
| 📐 Calibrate | Re-opens the calibration window |
| ⏸ Pause / Resume | Temporarily disables laser detection |
| 📊 Show Status | Prints current state to the console |
| ❌ Quit | Closes the app cleanly |

---

## ❌ How to Close the App

| Method | How |
|---|---|
| ✅ **Recommended** | Right-click tray icon → **❌ Quit** |
| ✅ **Terminal** | Press `Ctrl + C` in the console window |
| ⚠️ **Force close** | Task Manager → find `python.exe` → End Task |

---

## ⚙️ Configuration

All settings are in **`src/config.py`** — open it in Notepad or any text editor:

```python
CAMERA_INDEX     = 0      # Built-in webcam = 0. External USB webcam = 1 or 2
FREEZE_DURATION  = 2.0    # Seconds to hold still before action fires
FREEZE_RADIUS    = 20     # Pixel radius of stillness tolerance (tremor buffer)
COOLDOWN         = 1.5    # Minimum seconds between two consecutive slide actions
ZONE_SPLIT       = 0.35   # Size of left/right zones (35% of frame width each)
MIN_CONTOUR_AREA = 5      # Raise this if red objects trigger false positives
```

### Common adjustments

| Situation | Fix |
|---|---|
| Slides change too slowly | Lower `FREEZE_DURATION` to `1.5` |
| Accidental triggers while pointing | Raise `FREEZE_DURATION` to `3.0` |
| Red objects in background cause false triggers | Raise `MIN_CONTOUR_AREA` to `15` or `20` |
| Wrong camera opens | Change `CAMERA_INDEX` to `1` or `2` |
| Zones feel too wide or narrow | Adjust `ZONE_SPLIT` (e.g. `0.3` or `0.45`) |

---

## 🏗 Project Structure

```
laser-ppt-controller/
│
├── setup.bat            ← Run ONCE to install everything
├── run.bat              ← Run EVERY TIME to launch the app
├── main.py              ← App entry point
├── requirements.txt     ← Python dependencies list
├── .gitignore
├── README.md
│
└── src/
    ├── config.py        ← All tunable settings in one place
    ├── detector.py      ← HSV laser detection + FreezeDetector class
    ├── calibrator.py    ← Interactive Homography calibration with SKIP button
    ├── controller.py    ← pyautogui slide key actions
    └── tray.py          ← System tray icon and right-click menu
```

---

## 🐛 Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| `setup.bat` says Python not found | Python not installed or not in PATH | Reinstall Python, check **"Add to PATH"** |
| Camera doesn't open | Wrong camera index | Change `CAMERA_INDEX` to `1` or `2` in `config.py` |
| Laser not detected | Bright room or weak laser | Dim the room lights slightly |
| Too many false positives | Red objects in background | Raise `MIN_CONTOUR_AREA` to `15`–`20` |
| Slides don't change | PowerPoint lost keyboard focus | Click the slideshow window, then test again |
| Calibration window is confusing | No projector connected | Press **S** or click **SKIP** — calibration is optional |
| Wrong slide direction | Camera image mirrored | Add `frame = cv2.flip(frame, 1)` in `detector.py` |
| App crashes silently | Missing dependency | Run `setup.bat` again |
| Tray icon not visible | Icon hidden by Windows | Click the `^` arrow in the taskbar to find it |

---

## 🔬 Technical Details

### Why HSV instead of RGB?

RGB colour values change drastically with lighting. The same red laser looks very different under fluorescent lights vs daylight. HSV separates **hue** (the actual colour) from **brightness**, making red detection consistent across environments.

### Why two HSV ranges for red?

The HSV hue channel is circular — red lives at both ends: **0–10°** and **170–180°**. Using only one range misses half of all detections. Both masks are merged with `bitwise_or`.

### What is Homography?

A **Homography Matrix** is a 3×3 mathematical transform computed by OpenCV. The camera sits below the projection screen at an angle, so a laser dot at the centre of the screen might appear at the bottom-left of the camera frame. The 4-corner calibration step lets OpenCV calculate the exact transform so every laser position maps correctly to the screen — regardless of camera angle or distance.

### Why freeze instead of zone-entry?

Earlier versions triggered the moment the laser entered a zone. This caused constant accidental triggers while the presenter was pointing at content near the edge of the slide. The freeze approach means **you must deliberately pause** the laser — natural pointing movement never triggers a slide change.

---

## 📋 Dependencies

| Library | Version | Purpose |
|---|---|---|
| `opencv-python` | ≥ 4.8.0 | Camera capture, HSV masking, Homography |
| `numpy` | ≥ 1.24.0 | Array math for image processing |
| `pyautogui` | ≥ 0.9.54 | Simulating keyboard arrow key presses |
| `pystray` | ≥ 0.19.0 | System tray icon and menu |
| `Pillow` | ≥ 10.0.0 | Drawing the tray icon image |

---

## 🗺 Roadmap

- [ ] Green and blue laser support
- [ ] GUI settings panel (no config file editing needed)
- [ ] On-screen countdown overlay visible on projector
- [ ] Support for Google Slides and Keynote
- [ ] Packaged `.exe` installer (no Python required)

---

## 🤝 Contributing

Pull requests are welcome. For major changes please open an issue first.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📜 License

MIT — free to use, modify, and distribute for any purpose.

---

## 👤 Author

Built for classroom and training centre use.
Developed with Python, OpenCV, and pyautogui.

---

<div align="center">

**⭐ If this project helped you, please give it a star on GitHub! ⭐**

</div>
