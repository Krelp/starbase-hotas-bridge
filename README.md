# Starbase HOTAS Bridge

> **Best experienced with VKB dual-stick + pedals** — pre-tuned profiles included out of the box.

Maps HOTAS flight sticks to keyboard inputs for [Starbase](https://store.steampowered.com/app/454120/Starbase/) using PWM (pulse-width modulation) at 120Hz, giving analog-feeling precision control from digital key presses.

---
SCREENSHOTS
---
<img width="1572" height="870" alt="Screenshot 2026-05-31 145512" src="https://github.com/user-attachments/assets/1a34ccbb-a9e1-4ea6-b016-a623efcf066e" />
<img width="1571" height="1867" alt="Screenshot 2026-05-31 145736" src="https://github.com/user-attachments/assets/792de23d-213a-407d-bc94-d21a2920dd30" />
<img width="1512" height="352" alt="Screenshot 2026-05-31 145642" src="https://github.com/user-attachments/assets/b63f5493-0056-44b2-9496-334da4666f92" />
---

## ⚡ Download & Run — No Setup Required

### Step 1 — Download the EXE

Go to the [**Releases**](../../releases) page and download:

```
StarbaseHOTASBridge.exe
```

### Step 2 — Run It

Double-click `StarbaseHOTASBridge.exe`.

**That's it.** No Python. No install. No setup. Just run it.

> **Windows SmartScreen warning?** Click **More info → Run anyway**.
> This is normal for new unsigned apps. The full source code is public on GitHub so you can verify exactly what it does.

> **Antivirus flag?** The app uses `pynput` to send keypresses (the same technique keyloggers use, which triggers heuristic detection). It does **not** log, transmit, or store any keystrokes — it only sends them to the active window. Check the source if in doubt.

Your profiles and settings are saved automatically to `Documents\StarbaseHOTAS\` and persist between sessions.

---

## 🎮 Recommended Hardware — VKB Setup

This app was designed and tuned specifically for the **VKB dual-stick + pedals** configuration:

| Device | Role |
|--------|------|
| **VKBsim Gladiator EVO R SEM** | Right stick — Pitch, Roll, Yaw (twist) |
| **VKBsim Gladiator EVO L** | Left stick — Thrust, Strafe Up/Down (twist) |
| **VKBSim T-Rudder** | Pedals — Strafe Left/Right |

A **pre-tuned profile** with custom response curves for every axis loads automatically on first launch.

---

## ⚠️ Critical Starbase Setting

Before flying, go to **Settings → Controls → Key Hold Detection** and set it to **0.0** or **0.1** seconds.

The default is 0.6 seconds. At 0.6s the game buffers rapid keypresses and movement feels jerky. At 0.0–0.1s the PWM input is smooth and responsive.

---

## 🕹 Other HOTAS Hardware

Any joystick Windows recognizes will work. On first launch, choose **Start Blank** and use the **DETECT** button in each movement card to map your axes manually.

---

## 🚀 About the Feel

Control through this bridge is not artificially snappy — zero-latency response is not the goal.

Think of it like landing on the Moon with a real spacecraft: the ship needs momentum to get moving, and momentum to stop. Starbase uses a thruster pulse system — each keypress fires a real thruster burst that builds velocity over time.

- **Thruster Fire Rate** = how many times per second the thruster fires (keypresses/sec)
- **Thruster Burn Time** = how long each firing lasts (key hold duration)

Tune both to work *with* the ship physics, not against it.

---

## 🛠 Setup Guide

### Step 0 — Connect Your Devices
Assign each physical device to its role using the dropdowns. Click **SCAN FOR DEVICES** if they don't appear.

### Step 1 — Detect Axes
In each movement card:
1. Click **DETECT**
2. Move the physical axis on your stick
3. Click the bar that lights up
4. The axis is now assigned

### Step 2 — Set Keys
Click any key field and press the key. Works with Shift, Ctrl, Alt, F-keys, arrows, and all standard keys.

### Step 3 — Tune the Feel

**Dead Zone** — How far you must move before it responds. Hard minimum of 15% to cover hardware drift.

**Thruster Fire Rate** — How many times per second the thruster fires. Functional range 15–85%.
- Below 15%: too slow to feel
- Above 85%: key holds continuously anyway (same as 85%)

**Thruster Burn Time** — How long each thruster firing lasts. Functional range 8–50%.
- Below 8%: hold is <0.7ms — game may not register it
- Above 50%: same effect as raising Fire Rate

**Curve Graph** — Shows thruster fires/sec vs stick angle. Drag the 7 handles to shape the response. Use the preset buttons (Gentle / Expo / Linear / Early / Aggressive) for common shapes. Double-click to reset.

---

## 🐢 Turtle Mode

Toggle between your normal profile and a slower, precision profile instantly — live without stopping.

1. Click **CONFIGURE TURTLE PROFILE** in the turtle mode banner
2. Choose **Copy Current Settings** (then lower sliders) or **Load From Saved Profile**
3. Toggle with the 🐢 button in the profile bar or in the banners at top/bottom of the page

Changes made while in turtle mode auto-save back to the turtle profile.

---

## 💾 Profiles & Autosave

The app **autosaves everything continuously** — your settings, theme, and color choices are never lost. It reopens exactly where you left it.

- **SAVE** — Save to current profile name (asks before overwriting)
- **SAVE AS** — Save with a new name
- **LOAD** — Switch to a different profile
- **NEW** — Create a blank or VKB-default profile
- **DELETE** — Remove a profile

Saves go to `Documents\StarbaseHOTAS\` with automatic `.bak` backup before each write.

---

## 🎨 Themes

**8 themes** in the top bar dropdown:

| Theme | Character |
|-------|-----------|
| Space | Dark purple — the default |
| Midnight | Pure black with gold accents |
| Rainbow | 10-color cycling — every swatch is different |
| Spring | Forest greens and lime |
| Summer | Warm golds and burnt orange |
| Autumn | Russet, amber, and deep red |
| Winter | Navy, ice blue, and steel |
| Christmas | Deep red and forest green |
| Halloween | Pumpkin orange and purple |

**4 color toggles** in the title bar — **BG / TEXT / BTN / GRAPH** — each cycles through 4 preset shades. The header color automatically matches your BG selection. Mix and match for 256+ combinations per theme.

---

## 📋 Default VKB Key Bindings

| Movement | Negative Key | Positive Key |
|----------|-------------|-------------|
| Yaw | Q (turn left) | E (turn right) |
| Pitch | W (nose up) | S (nose down) |
| Roll | A (roll left) | D (roll right) |
| Thrust | Shift (forward) | Ctrl (backward) |
| Strafe L/R | ← Arrow | → Arrow |
| Strafe U/D | ↓ Arrow | ↑ Arrow |

---

## 🔧 How PWM Works

The app pulses keyboard keys at **120Hz** (8.3ms cycles). Stick deflection controls the duty cycle:

- **Light stick touch** → short key taps → slow, precise movement
- **Full deflection** → long key holds → fast movement (continuous above 70% deflection)
- **Thruster Burn Time** sets the minimum hold so even gentle inputs feel solid

---

## 🔒 Security

- **100% local** — no network calls, no telemetry, no external connections
- **No admin rights required** — runs entirely in user space
- **Profile validation** — profiles are validated and values clamped to safe ranges before loading
- **Atomic saves** — session state writes to a temp file first, then renames, with `.bak` backup
- **Open source** — every line of code is public on GitHub

---

## 📁 Save File Structure

```
Documents\StarbaseHOTAS\
├── VKB Default.json        ← Pre-tuned VKB profile (copied on first run)
├── .autosave.json          ← Continuous autosave (do not delete)
├── .autosave.bak           ← Backup of last good autosave
└── .session_state.json     ← Theme and swatch settings
```

---

## 🔨 For Developers — Build From Source

1. Install Python 3.11+ from [python.org](https://www.python.org) (check **Add to PATH**)
2. Run `launch.bat` to install dependencies and run from source
3. Run `build_exe.bat` to build `dist\StarbaseHOTASBridge.exe`

```
starbase_hotas.py           ← Main application (single file)
launch.bat                  ← Run from source with auto-install
build_exe.bat               ← Build the .exe with PyInstaller
StarbaseHOTASBridge.spec    ← PyInstaller config
LICENSE                     ← MIT License
```

---

## License

MIT — free to use, modify, and share.

**Made for the Starbase community.** Share it on the [Starbase Discord](https://discord.gg/starbase)!
