# Starbase HOTAS Bridge

> **Best experienced with VKB dual-stick + pedals** — pre-tuned profiles included out of the box.

Maps HOTAS flight sticks to keyboard inputs for [Starbase](https://store.steampowered.com/app/454120/Starbase/) using PWM (pulse-width modulation), giving analog-feeling precision control from digital key presses.
---
SCREENSHOTS
<img width="1574" height="875" alt="Screenshot 2026-05-31 041415" src="https://github.com/user-attachments/assets/13ce9ce5-616e-4a15-9233-fc0f6666cedf" />
<img width="1573" height="875" alt="Screenshot 2026-05-31 041453" src="https://github.com/user-attachments/assets/7e207c01-9b24-41d0-957c-ad0b77ece004" />
<img width="1571" height="872" alt="Screenshot 2026-05-31 041511" src="https://github.com/user-attachments/assets/b1fadd92-2541-4be7-946f-86f1f398e26c" />
<img width="1576" height="873" alt="Screenshot 2026-05-31 041852" src="https://github.com/user-attachments/assets/6f50fe13-4505-4f00-b64a-37eaeab212ef" />
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
> This is normal for new unsigned apps downloaded from the internet.

Your profiles and settings are saved automatically to `Documents\StarbaseHOTAS\` and persist between sessions.

---

## 🎮 Recommended Hardware — VKB Setup

This app was designed and tuned specifically for the **VKB dual-stick + pedals** configuration:

| Device | Role |
|--------|------|
| **VKBsim Gladiator EVO R SEM** | Right stick — Pitch, Roll, Yaw (twist) |
| **VKBsim Gladiator EVO L** | Left stick — Thrust, Strafe Up/Down (twist) |
| **VKBSim T-Rudder** | Pedals — Strafe Left/Right |

### Why VKB?

The VKB Gladiator EVO sticks have high-resolution sensors, clean analog output, and a twist axis on each grip — giving you 6-DOF spacecraft control without using thumb hats. The T-Rudder adds dedicated left/right strafe on a third device. Together they cover all 6 movement axes Starbase uses, with no axis conflicts and no compromises.

A **pre-tuned profile** with custom response curves for every axis is loaded automatically on first launch.

---

## 🕹 Other HOTAS Hardware

Any joystick Windows recognizes will work. On first launch, choose **Start Blank** and use the **DETECT** button in each movement card to map your axes manually.

Popular alternatives that work well:
- Thrustmaster T.16000M FCS (stick + throttle)
- Logitech X56 / X52
- Thrustmaster HOTAS Warthog
- Any single joystick with a twist axis

---

## 🛠 How It Works

The app pulses keyboard keys at 20 Hz. Stick deflection controls how long each key is held:

- **Light stick touch** → short key taps → slow, precise movement
- **Full deflection** → long key holds → fast movement
- **Pulse Length** slider → minimum hold per cycle (makes light inputs feel solid)
- **7 draggable curve handles** → shape the exact response at every stick angle

This gives you analog-feeling control in a game that only accepts keyboard input.

---

## 🎨 Interface

- **Space** and **Midnight** themes
- Three color toggles (BG / TEXT / BTN) to customize each theme
- The app remembers your exact state between sessions — theme, profile, curve shapes, everything

---

## 💾 Profiles

The app autosaves your state continuously. Manual saves work like a video game:
- **SAVE** — asks before overwriting
- **SAVE AS** — always prompts for a name
- **LOAD** — switch between saved configurations

---

## 📁 File Structure

After first launch, your data lives here:

```
Documents\StarbaseHOTAS\
├── VKB Default.json        ← Pre-tuned VKB profile (copied on first run)
├── .autosave.json          ← Continuous autosave (do not delete)
└── .session_state.json     ← Theme and swatch settings
```

---

## 🔨 For Developers — Build From Source

If you want to build the exe yourself or run from source:

1. Install Python 3.11+ from [python.org](https://www.python.org) (check **Add to PATH**)
2. Run `launch.bat` to install dependencies and launch the script directly
3. Run `build_exe.bat` to build a standalone `StarbaseHOTASBridge.exe`

Source files:
```
starbase_hotas.py           ← Main application (single file)
launch.bat                  ← Run from source with auto-dependency install
build_exe.bat               ← Build the .exe with PyInstaller
StarbaseHOTASBridge.spec    ← PyInstaller config
```

---

## 📋 Default VKB Key Bindings

| Movement | Left Key | Right Key |
|----------|----------|-----------|
| Yaw | Q (turn left) | E (turn right) |
| Pitch | W (nose up) | S (nose down) |
| Roll | A (roll left) | D (roll right) |
| Thrust | Shift (forward) | Ctrl (backward) |
| Strafe L/R | ← Arrow | → Arrow |
| Strafe U/D | ↓ Arrow | ↑ Arrow |

---

## License

MIT — free to use, modify, and share.

**Made for the Starbase community.** Share it on the [Starbase Discord](https://discord.gg/starbase)!
