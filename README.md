# Starbase HOTAS Bridge

> **Version 0.1.0-alpha** — Early access. Best experienced with VKB dual-stick + pedals. Works with any joystick Windows can see.

Maps HOTAS flight sticks to keyboard inputs for [Starbase](https://store.steampowered.com/app/454120/Starbase/) using PWM (pulse-width modulation) at 120Hz, giving analog-feeling precision control from digital key presses.

---

## ⚠️ Alpha Notice

This is an early alpha release. Core functionality is working but you may encounter rough edges. If you find a bug, please [open an issue](../../issues) with:
- What you were doing
- What happened vs what you expected
- Your joystick hardware

NOTE: Ctrl + S is bound to "save" by Windows, so you can't pitch while moving backwards, which also affects the game without HOTAS. You can only pitch in one direction while pressing ctrl, with or without HOTAS.

---
<img width="1571" height="2041" alt="Screenshot 2026-05-31 154832" src="https://github.com/user-attachments/assets/fbaefcee-9c70-4b7f-9186-d9aa0ba3b272" />
---
<img width="1571" height="2037" alt="Screenshot 2026-05-31 154927" src="https://github.com/user-attachments/assets/95c4563f-9791-4f14-b226-0f9d9813735b" />
---

## ⚡ Download & Run — No Setup Required

Go to the [**Releases**](../../releases) page and download `StarbaseHOTASBridge.exe`. Double-click to run. No Python, no install.

> **Windows SmartScreen warning?** Click **More info → Run anyway**. Normal for new unsigned apps — full source is public on GitHub.

> **Antivirus flag?** The app uses `pynput` to send keypresses to Starbase. Same API keyloggers use, so AV heuristics may flag it. It does **not** log, transmit, or store any keystrokes. Check the source if in doubt.

Settings save automatically to `Documents\StarbaseHOTAS\` and restore on next launch.

---

## ⚠️ Critical Starbase Setting — Do This First

In Starbase go to **Settings → Controls → Key Hold Detection** and set it to **0.0** or **0.1** seconds.

The default is **0.6 seconds**. At 0.6s the game buffers rapid keypresses and movement feels jerky. At 0.0–0.1s the 120Hz PWM input is smooth and responsive. **This is the single most important setup step.**

---

## 🎮 Recommended Hardware — VKB Setup

| Device | Role |
|--------|------|
| **VKBsim Gladiator EVO R SEM** | Right stick — Pitch, Roll, Yaw (twist) |
| **VKBsim Gladiator EVO L** | Left stick — Thrust, Strafe Up/Down (twist) |
| **VKBSim T-Rudder** | Pedals — Strafe Left/Right |

A pre-tuned profile loads automatically on first launch for VKB users.

---

## 🕹 Other HOTAS Hardware

**Any joystick Windows recognizes will work.** On first launch, choose **Start Blank** and use **DETECT** in each movement card to map your axes.

**Tips for non-VKB users:**
- Use **DETECT** to find your axis — don't guess axis numbers
- If an axis is inverted, toggle the **INVERTED** button
- If you don't have a device for a movement (e.g. no pedals), click **NOT USED**
- Adjust **Dead Zone** to match your hardware — quality sticks may need as little as 5%

---

## 🚀 About the Feel

Control through this bridge is not artificially snappy — zero-latency response is not the goal.

Think of it like landing on the Moon with a real spacecraft: the ship needs momentum to get moving, and momentum to stop. Starbase uses a thruster pulse system — each keypress fires a real thruster burst that builds velocity over time.

- **Thruster Fire Rate** — keypresses per second = how often the thruster fires
- **Thruster Burn Time** — key hold duration = how long each firing lasts

Tune both to work *with* the ship physics, not against it.

---

## 🛠 Setup Guide

### Step 0 — Connect Your Devices
Assign each device to its role in the dropdowns. Click **SCAN FOR DEVICES** if they don't appear. Plug in sticks before launching.

### Step 1 — Detect Axes
In each movement card:
1. Click **DETECT**
2. Move that axis on your stick
3. Click the bar that lights up

Mark anything you don't have as **NOT USED**.

### Step 2 — Set Keys
Click any key field and press the key you want. Works with letters, Shift, Ctrl, Alt, F1–F12, arrows.

### Step 3 — Tune the Feel

| Slider | Range | What it does |
|--------|-------|-------------|
| **Dead Zone** | 5–40% | How far to move before responding |
| **Thruster Fire Rate** | 15–85% | Keypresses per second at full deflection |
| **Thruster Burn Time** | 8–50% | Key hold duration per 8.3ms cycle |

**Curve Graph** — drag the 7 handles to shape thruster response. Use presets (Gentle / Expo / Linear / Early / Aggressive) or double-click to reset.

---

## 🐢 Turtle Mode

Swap between your normal profile and a slower precision profile instantly — live without stopping.

1. Click **CONFIGURE TURTLE PROFILE** in the turtle banner
2. Choose **Copy Current Settings** or **Load From Saved Profile**
3. Toggle with the 🐢 button

Edits made in turtle mode auto-save to the turtle profile.

---

## 💾 Profiles & Autosave

Autosaves continuously. Reopens exactly where you left it.

- **SAVE / SAVE AS / LOAD / NEW / DELETE** — full profile management
- Profiles validated on load — corrupt values clamped to safe defaults
- Save location: `Documents\StarbaseHOTAS\` (follows OneDrive redirect if active)

---

## 🎨 Themes

9 themes: **Space · Midnight · Rainbow · Spring · Summer · Autumn · Winter · Christmas · Halloween**

4 color toggles — **BG / TEXT / BTN / GRAPH** — each cycles through 4 preset shades. 256+ combinations per theme.

---

## 📋 Default VKB Key Bindings

| Movement | Keys |
|----------|------|
| Yaw | Q / E |
| Pitch | W / S |
| Roll | A / D |
| Thrust | Shift / Ctrl |
| Strafe L/R | ← / → |
| Strafe U/D | ↓ / ↑ |

---

## 🔧 How PWM Works

Keys pulse at **120Hz** (8.3ms cycles). Stick position controls duty cycle:
- Light touch → short taps → slow precise movement
- Full deflection → long holds → fast movement
- Above 70% deflection → continuous hold (no pulsing)

---

## 🔒 Security

- 100% local — no network, no telemetry, no external connections
- No admin rights required
- Open source — every line auditable on GitHub
- Profile validation and atomic saves with `.bak` backup

---

## 📁 Save Files

```
Documents\StarbaseHOTAS\
├── VKB Default.json        ← Pre-tuned VKB profile
├── .autosave.json          ← Continuous autosave
├── .autosave.bak           ← Backup of last good autosave
└── .session_state.json     ← Theme and last state
```

---

## 🔨 Build From Source

1. Install Python 3.11+ — check **Add to PATH**
2. Run `launch.bat` — installs dependencies and runs from source
3. Run `build_exe.bat` — builds `dist\StarbaseHOTASBridge.exe`

### Dependencies (auto-installed)
`pygame` · `pynput` · `PyQt6` · Windows 10/11

---

## Versioning

| Version | Meaning |
|---------|---------|
| `0.x.x-alpha` | Early access, may have bugs |
| `0.x.x-beta` | Feature complete, bug fixing |
| `1.0.0` | First stable public release |

---

## License

MIT — free to use, modify, and share.

**Made for the Starbase community.**
