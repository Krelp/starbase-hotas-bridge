# Starbase HOTAS Bridge

Maps VKB (and other) HOTAS flight sticks to keyboard inputs for [Starbase](https://store.steampowered.com/app/454120/Starbase/) using PWM (pulse-width modulation) — giving analog-feeling control from digital key presses.

## ⚡ Quick Start (No setup required)

1. **Double-click `launch.bat`**

That's it. The launcher automatically:
- Detects if Python is installed, downloads and installs it if not
- Installs all required packages (pygame, pynput, PyQt6)
- Launches the app

On the first run it may take 1–2 minutes to install. Every run after that starts in seconds.

> **Note:** Windows may show a SmartScreen warning because the `.bat` file is new. Click **More info → Run anyway**.

---

## 🎮 Supported Hardware

Pre-tuned profile included for:
- **VKBsim Gladiator EVO R SEM** — Right stick (Pitch / Roll / Yaw twist)
- **VKBsim Gladiator EVO L** — Left stick / Throttle (Thrust + Strafe U/D)
- **VKBSim T-Rudder** — Pedals (Strafe L/R)

Works with **any joystick** recognized by Windows. Use the DETECT button to map any axis.

---

## 🛠 Setup Guide

### Step 0 — Connect Your Devices
Assign each physical device to its role using the dropdowns. Click **SCAN FOR DEVICES** if they don't appear.

### Step 1 — Detect Axes
In each movement card, click **DETECT**, move the physical axis, click the bar that lights up, and the axis is assigned.

### Step 2 — Set Keys
Click any key field and press the key. Works with shift, ctrl, alt, arrows, F-keys, etc.

### Step 3 — Tune Feel
- **Dead Zone** — How far to move before responding
- **Maximum Speed** — How fast at full deflection
- **Pulse Length** — Minimum hold time per key cycle (light taps vs heavy holds)
- **Drag the 7 curve handles** to shape the response at each stick angle

---

## 💾 Profiles & Autosave

The app **automatically restores** your exact last state on every launch — profile, settings, theme, color choices. No manual saving required.

Manual saves work like a video game: **SAVE** asks before overwriting, **SAVE AS** always prompts for a name.

---

## 🎨 Themes

Two themes in the top bar: **Space** (dark purple) and **Midnight** (pure black).

Three color toggles (BG / TEXT / BTN) let you cycle each through 4 preset shades.

---

## 📁 Files

```
starbase-hotas-bridge/
├── launch.bat              ← Double-click to run (auto-installs everything)
├── starbase_hotas.py       ← Main application
├── README.md               ← This file
└── hotas_profiles/
    └── VKB Default.json    ← Pre-tuned VKB profile
```

---

## 🔧 How PWM Works

The app pulses keyboard keys at 20 Hz. Stick deflection controls the duty cycle:
- Gentle stick → short key taps → slow, precise movement
- Full stick → long key holds → fast movement
- **Pulse Length** sets a minimum hold so even light inputs feel solid

---

## 📋 Requirements (auto-installed by launch.bat)

- Windows 10/11
- Python 3.10+ (downloaded automatically if missing)
- pygame, pynput, PyQt6 (installed automatically)

---

## License

MIT — free to use, modify, and share.

Made for the Starbase community. Share it on Discord!
