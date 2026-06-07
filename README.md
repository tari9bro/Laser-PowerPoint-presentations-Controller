<div align="center">

# 🔴 Laser PowerPoint presentations Controller

**Control your PowerPoint presentations using a red laser pointer and your laptop's built-in webcam.**

No clicker hardware. No Bluetooth dongle. No extra device.  
Just your laser, your laptop, and Python.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green?logo=opencv)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-informational?logo=windows)](https://www.microsoft.com/windows)

</div>

---

## 📖 What Is This?

**Laser PowerPoint presentations Controller** is an open-source Python application that turns any **red laser pointer** into a wireless presentation remote.

It uses your laptop's **built-in webcam** to watch the projection wall. When you hold the laser still in the left or right zone of the slide for **2 seconds**, the app automatically presses the arrow key to change the slide — without you touching the keyboard or any remote control.

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

### The Detection Pipeline

Every camera frame goes through this pipeline:

```
BGR frame → HSV colorspace → Two red masks (hue 0-10 and 170-180)
    → Merge & morphological cleanup → Find contours → Laser center (x, y)
    → Homography correction → Zone check → Freeze timer
    → 2 seconds still? → pyautogui.press("right" or "left")
```

### The Freeze-to-Trigger Logic

This is the key design decision that makes the app practical:

```
Laser moves freely   →  NO action  (point at content for students)
Laser freezes 2s     →  SLIDE CHANGES  (intentional command)
```

You can point at anything on the slide as long as you want — the app only triggers when the dot stops moving for exactly 2 full seconds in the left or right zone.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔴 **Red laser detection** | HSV colour masking with morphological noise cleanup — works in typical classroom lighting |
| ⏱ **Freeze-to-trigger** | 2-second hold required — eliminates accidental triggers while pointing at content |
| 📐 **Homography calibration** | Corrects for any camera angle, height, or offset from the projection screen |
| 🖥 **Silent background mode** | Runs as a system tray icon — PowerPoint always stays in focus |
| 🟢🔴⚫ **Visual status indicator** | Tray icon changes colour to show app state at a glance |
| ⚙️ **Single config file** | All settings in `src/config.py` — no code editing needed for normal use |
| 🧩 **Clean modular code** | Separated into detector / calibrator / controller / tray modules |
| 🔄 **Re-calibrate on the fly** | Right-click tray → Calibrate at any time during a session |
| ⏸ **Pause & resume** | Temporarily disable detection without quitting the app |

---

## 📦 Requirements

### Hardware
- A laptop or desktop with a **webcam facing the projection wall**
- A **red laser pointer** (any standard presentation laser)
- A **projector** connected via HDMI

### Software
- **Python 3.9 or newer**
- **Windows 10 / 11** *(primary platform — Linux/macOS may need minor adjustments for the system tray)*
- **PowerPoint** or any presentation software that responds to arrow keys

---

## 🛠 Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/laser-ppt-controller.git
cd laser-ppt-controller
```

### Step 2 — Create a virtual environment

```bash
python -m venv .venv
```

### Step 3 — Activate the virtual environment

```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

That's it. No system-level installs, no drivers, no external hardware setup.

---

## ▶️ Running the App

```bash
python main.py
```

---

## 📐 First-Time Calibration

When the app starts, a **calibration window** opens automatically showing your camera feed.

**Click the 4 corners of the projection screen** in this exact order:

```
  1 ─────────── 2
  │             │
  │  Projected  │
  │   Screen    │
  │             │
  4 ─────────── 3
```

The app draws a green polygon as you click. Once all 4 corners are marked, the window closes automatically and the app moves to the **system tray**.

> Press **ESC** to skip calibration. The app will still work but zone detection may be less accurate if the camera is at an angle to the screen.

---

## 🎮 Using the App During a Presentation

### Open PowerPoint first, then run the app

```
1. Open PowerPoint → Start slideshow (fullscreen on projector)
2. python main.py
3. Complete calibration
4. App disappears to system tray — PowerPoint keeps focus
5. Present freely!
```

### Slide Control

| Action | What You Do |
|---|---|
| **Next slide ▶** | Point laser at the **right 35%** of the screen and hold still for 2 seconds |
| **Previous slide ◀** | Point laser at the **left 35%** of the screen and hold still for 2 seconds |
| **Point at content** | Move the laser freely — no action fires while it's moving |

### Tray Icon Status

Right-click the tray icon (bottom-right corner of taskbar) at any time:

| Tray Icon Color | Meaning |
|---|---|
| 🟢 Green | App running — no laser detected |
| 🔴 Red | Laser currently detected in camera |
| ⚫ Gray | Detection paused |

### Tray Menu Options

| Option | What It Does |
|---|---|
| 📐 Calibrate | Re-opens the calibration window |
| ⏸ Pause / Resume | Temporarily disables laser detection |
| 📊 Show Status | Prints current state to the console |
| ❌ Quit | Closes the app cleanly |

---

## ⚙️ Configuration

All settings are in **`src/config.py`**. Open it in any text editor:

```python
CAMERA_INDEX     = 0      # Built-in webcam = 0. External USB webcam = 1 or 2
FREEZE_DURATION  = 2.0    # Seconds to hold still before action fires
FREEZE_RADIUS    = 20     # Pixel radius of "stillness" tolerance (tremor buffer)
COOLDOWN         = 1.5    # Minimum seconds between two consecutive slide actions
ZONE_SPLIT       = 0.35   # Size of left/right zones (35% of frame width each)
MIN_CONTOUR_AREA = 5      # Raise this if red objects in background cause false triggers
```

**Common adjustments:**

| Situation | Fix |
|---|---|
| Slides change too slowly | Lower `FREEZE_DURATION` to `1.5` |
| Accidental triggers while pointing | Raise `FREEZE_DURATION` to `3.0` |
| Room has red objects causing false triggers | Raise `MIN_CONTOUR_AREA` to `15` or `20` |
| Wrong camera opens | Change `CAMERA_INDEX` to `1` or `2` |
| Zones feel too wide or narrow | Adjust `ZONE_SPLIT` (0.3 = smaller zones, 0.45 = larger zones) |

---

## 🏗 Project Structure

```
laser-ppt-controller/
│
├── main.py              ← Entry point — launch this to run the app
├── requirements.txt     ← Python dependencies
├── .gitignore
├── README.md
│
└── src/
    ├── config.py        ← All tunable settings in one place
    ├── detector.py      ← HSV laser detection + FreezeDetector class
    ├── calibrator.py    ← Interactive Homography calibration
    ├── controller.py    ← pyautogui slide key actions
    └── tray.py          ← System tray icon and right-click menu
```

---

## 🔬 Technical Details

### Why HSV and not BGR?

RGB/BGR colour values are sensitive to lighting. The same red laser can look very different under fluorescent lights vs natural light. HSV (Hue, Saturation, Value) separates the **colour** from the **brightness**, making red detection far more consistent across environments.

### Why two HSV ranges for red?

The HSV hue channel is circular. Red sits at both the **start** (0–10°) and **end** (170–180°) of the wheel. Using only one range misses half of all red detections. Both masks are combined with `bitwise_or`.

### What is Homography?

A **Homography Matrix** is a 3×3 mathematical transform that maps one 2D plane to another. In this app:

- The camera sits at an angle below the projection screen
- A laser dot at the centre of the screen might appear at the bottom-left of the camera frame
- The 4-corner calibration step captures the real corners of the screen in camera space
- OpenCV computes the matrix that transforms any camera pixel into the correct screen pixel

This means zone detection is accurate **regardless of camera position or angle**.

### The FreezeDetector class

```
Every frame:
  ├── No laser? → Reset anchor and timer
  ├── Laser moved > 20px from anchor? → Reset anchor and timer  
  └── Laser within 20px for >= 2.0 seconds? → TRIGGER ACTION
```

After an action fires, the detector resets — the presenter must move the laser and re-aim to trigger again. This prevents a single long freeze from spamming slide changes.

---

## 🐛 Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| Camera doesn't open | Wrong camera index | Change `CAMERA_INDEX` to `1` or `2` in `config.py` |
| Laser not detected | Bright room / weak laser | Try dimming room lights; lower `MIN_CONTOUR_AREA` |
| Too many false positives | Red objects in background | Raise `MIN_CONTOUR_AREA` to `15`–`20` |
| Wrong slide direction | Camera mirrored | Add `frame = cv2.flip(frame, 1)` in `detector.py` |
| Slides don't change | PowerPoint lost focus | Click the slideshow window before using the laser |
| Calibration feels off | Poor corner selection | Right-click tray → Calibrate again, click corners carefully |
| App crashes on startup | Missing dependencies | Run `pip install -r requirements.txt` again |

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
- [ ] GUI settings panel (no code editing required)
- [ ] Click simulation for non-PowerPoint apps
- [ ] On-screen progress indicator overlay (OBS-compatible)
- [ ] Kotlin Compose Desktop version (distributable `.exe`)
- [ ] Automatic camera calibration using screen corner detection

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📜 License

MIT — free to use, modify, and distribute for any purpose.

---

## 👤 Author

Built for classroom and training centre use.  
Developed with Python + OpenCV + pyautogui.

---

<div align="center">

**⭐ If this project helped you, please give it a star on GitHub! ⭐**

</div>