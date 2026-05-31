# -*- coding: utf-8 -*-
"""
STARBASE HOTAS BRIDGE - v14
Install: pip install pygame pynput PyQt6
Run:     python starbase_hotas.py
"""
import sys, os, math, json, time, threading, copy
from pathlib import Path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from pynput.keyboard import Controller as KeyController, Key
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QGroupBox, QPushButton, QFrame,
    QLineEdit, QComboBox, QMessageBox, QScrollArea, QInputDialog,
    QSizePolicy, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPainterPath

# Init mixer FIRST with good settings before pygame.init() can override them
pygame.init()
pygame.joystick.init()

WIN_W, WIN_H = 1580, 880
MONO = "Courier New"
NO_AXIS = 99
import sys as _sys

def _get_data_dir():
    """
    Find the real Documents folder, respecting OneDrive redirection on Windows.
    Uses the Windows shell API (SHGetFolderPath) when available so the path
    matches what Windows Explorer shows as 'Documents'.
    """
    try:
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        # CSIDL_PERSONAL = 0x0005 = My Documents (follows OneDrive redirect)
        ctypes.windll.shell32.SHGetFolderPathW(None, 0x0005, None, 0, buf)
        docs = Path(buf.value) / "StarbaseHOTAS"
    except Exception:
        # Fallback for non-Windows or if shell32 unavailable
        docs = Path.home() / "Documents" / "StarbaseHOTAS"
    docs.mkdir(parents=True, exist_ok=True)
    return docs

_DATA_DIR = _get_data_dir()

PROFILES_DIR       = _DATA_DIR
LAST_PROFILE_FILE  = _DATA_DIR / ".last_profile"
AUTOSAVE_FILE      = _DATA_DIR / ".autosave.json"
SESSION_STATE_FILE = _DATA_DIR / ".session_state.json"

PROFILES_DIR.mkdir(exist_ok=True)

SPECIAL_KEYS = {
    "shift":Key.shift,"ctrl":Key.ctrl,"alt":Key.alt,"space":Key.space,
    "tab":Key.tab,"enter":Key.enter,"esc":Key.esc,"escape":Key.esc,
    "up":Key.up,"down":Key.down,"left":Key.left,"right":Key.right,
    "f1":Key.f1,"f2":Key.f2,"f3":Key.f3,"f4":Key.f4,
    "f5":Key.f5,"f6":Key.f6,"f7":Key.f7,"f8":Key.f8,
    "f9":Key.f9,"f10":Key.f10,"f11":Key.f11,"f12":Key.f12,
    "backspace":Key.backspace,"delete":Key.delete,
    "home":Key.home,"end":Key.end,
    "page_up":Key.page_up,"page_down":Key.page_down,
    "lshift":Key.shift_l,"rshift":Key.shift_r,
    "lctrl":Key.ctrl_l,"rctrl":Key.ctrl_r,
    "lalt":Key.alt_l,"ralt":Key.alt_r,
}

def resolve_key(k):
    if not k: return None
    k = k.strip().lower()
    return SPECIAL_KEYS.get(k, k)

# ─────────────────────────────────────────────────────────────
#  DEFAULT PROFILE  — VKB dual stick + pedals setup from user's config
# ─────────────────────────────────────────────────────────────
MOVEMENTS = ["yaw", "pitch", "roll", "thrust", "strafe_lr", "strafe_ud", "pedals"]

# Shipped profiles
VKB_PROFILE_NAME = "VKB Default"

# Blank profile for first-time users with unknown hardware
BLANK_PROFILE = {
    "name": "New Setup",
    "devices": {"stick": 0, "throttle": -1, "pedals": -1},
    "movements": {
        "yaw":       {"physical_axis": NO_AXIS, "key_left": "q",    "key_right": "e",    "deadzone": 15, "speed": 40, "pulse": 20, "inverted": False},
        "pitch":     {"physical_axis": NO_AXIS, "key_left": "w",    "key_right": "s",    "deadzone": 15, "speed": 40, "pulse": 20, "inverted": False},
        "roll":      {"physical_axis": NO_AXIS, "key_left": "a",    "key_right": "d",    "deadzone": 15, "speed": 40, "pulse": 20, "inverted": False},
        "thrust":    {"physical_axis": NO_AXIS, "key_left": "shift","key_right": "ctrl", "deadzone": 15, "speed": 55, "pulse": 40, "inverted": False},
        "strafe_lr": {"physical_axis": NO_AXIS, "key_left": "left", "key_right": "right", "deadzone": 15, "speed": 40, "pulse": 20, "inverted": False},
        "strafe_ud": {"physical_axis": NO_AXIS, "key_left": "down", "key_right": "up",   "deadzone": 15, "speed": 40, "pulse": 20, "inverted": False},
        "pedals":    {"physical_axis": NO_AXIS, "key_left": "q",    "key_right": "e",    "deadzone": 15, "speed": 40, "pulse": 20, "inverted": False},
    }
}

DEFAULT_PROFILE = {
    "name": "VKB Default",
    "turtle_profile": None,
    "devices": {
        "stick":    0,   # VKBsim Gladiator EVO R SEM
        "throttle": 2,   # VKBsim Gladiator EVO L
        "pedals":   1,   # VKBSim T-Rudder
    },
    "movements": {
        "yaw":       {"physical_axis": 5,       "key_left": "q",    "key_right": "e",    "deadzone": 15, "speed": 50, "pulse": 10,  "inverted": True,  "control_points": [[0.125, 0.2333], [0.25, 0.3789], [0.375, 0.5033], [0.5, 0.6156], [0.625, 0.7196], [0.75, 0.8176], [0.875, 0.9108]]},
        "pitch":     {"physical_axis": 1,       "key_left": "w",    "key_right": "s",    "deadzone": 15, "speed": 50, "pulse": 12, "inverted": False, "control_points": [[0.125, 0.2333], [0.25, 0.3789], [0.375, 0.5033], [0.5, 0.6156], [0.625, 0.7196], [0.75, 0.8176], [0.875, 0.9108]]},
        "roll":      {"physical_axis": 0,       "key_left": "a",    "key_right": "d",    "deadzone": 15, "speed": 50, "pulse": 12, "inverted": False, "control_points": [[0.125, 0.2333], [0.25, 0.3789], [0.375, 0.5033], [0.5, 0.6156], [0.625, 0.7196], [0.75, 0.8176], [0.875, 0.9108]]},
        "thrust":    {"physical_axis": 1,       "key_left": "shift","key_right": "ctrl", "deadzone": 15, "speed": 80, "pulse": 40, "inverted": False, "control_points": [[0.125, 0.125], [0.25, 0.25], [0.375, 0.375], [0.5, 0.5], [0.625, 0.625], [0.75, 0.75], [0.875, 0.875]]},
        "strafe_lr": {"physical_axis": 0,       "key_left": "left", "key_right": "right", "deadzone": 15, "speed": 50, "pulse": 12, "inverted": False, "control_points": [[0.125, 0.2333], [0.25, 0.3789], [0.375, 0.5033], [0.5, 0.6156], [0.625, 0.7196], [0.75, 0.8176], [0.875, 0.9108]]},
        "strafe_ud": {"physical_axis": 5,       "key_left": "down", "key_right": "up",   "deadzone": 15, "speed": 50, "pulse": 12, "inverted": False, "control_points": [[0.125, 0.2333], [0.25, 0.3789], [0.375, 0.5033], [0.5, 0.6156], [0.625, 0.7196], [0.75, 0.8176], [0.875, 0.9108]]},
        "pedals":    {"physical_axis": NO_AXIS, "key_left": "q",    "key_right": "e",    "deadzone": 15, "speed": 50, "pulse": 20, "inverted": False},
    }
}

MOVEMENT_LABELS = {
    "yaw":       ("YAW",       "Turn left / right",       "Right stick twist left/right"),
    "pitch":     ("PITCH",     "Nose up / down",           "Right stick forward/back"),
    "roll":      ("ROLL",      "Roll / bank",              "Right stick twist or roll axis"),
    "thrust":    ("THRUST",    "Forward / backward",       "Throttle or left stick fwd/back"),
    "strafe_lr": ("STRAFE L/R","Slide left / right",       "Pedals — sideways translation"),
    "strafe_ud": ("STRAFE U/D","Slide up / down",          "Left stick twist — vertical translation"),
    "pedals":    ("PEDALS YAW","Rudder pedals — Yaw",      "Overrides yaw when pressed harder than stick"),
}

DEVICE_SLOTS = ["stick", "throttle", "pedals"]
DEVICE_LABELS = {
    "stick":    "Right Stick  (Pitch / Roll)",
    "throttle": "Left Stick / Throttle  (Thrust + Strafe U/D via twist)",
    "pedals":   "Rudder Pedals  (Yaw override + Strafe L/R)",
}

# ─────────────────────────────────────────────────────────────
#  PROFILE I/O
# ─────────────────────────────────────────────────────────────
def save_profile(p, theme=None):
    data = dict(p)
    if theme: data["_theme"] = theme  # informational — not used on load
    with open(PROFILES_DIR / f"{p['name']}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    LAST_PROFILE_FILE.write_text(p["name"], encoding="utf-8")

def load_profile(name):
    path = PROFILES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Profile '{name}' not found at {path}")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Profile '{name}' is corrupted (invalid JSON): {e}")
    ok, reason = validate_profile(data)
    if not ok:
        raise ValueError(f"Profile '{name}' has invalid data: {reason}")
    return data

def list_profiles():
    try:
        names = [p.stem for p in PROFILES_DIR.glob("*.json")
                 if not p.stem.startswith(".")]   # exclude hidden files
        return sorted(names)
    except Exception:
        return []

def profile_exists(name):
    return (PROFILES_DIR / f"{name}.json").exists()

def save_session_state(profile, theme, swatches):
    """Save complete app state with backup in case of crash during write."""
    state = {
        "profile":  profile,
        "theme":    theme,
        "swatches": swatches,
    }
    import json as _json
    # Write to temp file first, then rename — prevents corrupt saves
    tmp = SESSION_STATE_FILE.with_suffix(".tmp")
    bak = SESSION_STATE_FILE.with_suffix(".bak")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            _json.dump(state, f, indent=2)
        # Back up previous good save
        if SESSION_STATE_FILE.exists():
            import shutil as _shutil
            _shutil.copy2(SESSION_STATE_FILE, bak)
        # Atomic-ish replace
        tmp.replace(SESSION_STATE_FILE)
    except Exception as e:
        print(f"Session save warning: {e}")

def load_session_state():
    """Load last session state. Returns (profile, theme, swatches) or None."""
    try:
        if SESSION_STATE_FILE.exists():
            import json as _json
            with open(SESSION_STATE_FILE, encoding="utf-8") as f:
                s = _json.load(f)
            return migrate(s["profile"]), s.get("theme","Space"), s.get("swatches",{})
    except: pass
    return None, None, None

def get_last_profile_name():
    try:
        if LAST_PROFILE_FILE.exists():
            return LAST_PROFILE_FILE.read_text(encoding="utf-8").strip()
    except: pass
    return None

def validate_profile(p):
    """
    Validate a profile dict before applying it.
    Returns (True, "") if valid, (False, reason) if not.
    """
    if not isinstance(p, dict):
        return False, "Profile is not a dict"
    if "movements" not in p:
        return False, "Profile missing 'movements'"
    movements = p["movements"]
    required_moves = ["yaw","pitch","roll","thrust","strafe_lr","strafe_ud"]
    for mv in required_moves:
        if mv not in movements:
            continue  # missing movements get defaults, not an error
        m = movements[mv]
        if not isinstance(m, dict):
            return False, f"Movement '{mv}' is not a dict"
        # Clamp numeric fields to safe ranges
        m["deadzone"] = max(15, min(40,  int(m.get("deadzone", 15))))
        m["speed"]    = max(15, min(85,  int(m.get("speed",    50))))
        m["pulse"]    = max(8,  min(50,  int(m.get("pulse",    15))))
        # Validate control_points if present
        cp = m.get("control_points")
        if cp is not None:
            if not isinstance(cp, list) or len(cp) != 7:
                m["control_points"] = None  # reset to default
            else:
                for i, pt in enumerate(cp):
                    if not (isinstance(pt, (list,tuple)) and len(pt)==2):
                        m["control_points"] = None; break
                    x, y = float(pt[0]), float(pt[1])
                    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                        m["control_points"] = None; break
    return True, ""

def migrate(p):
    if "movements" in p:
        # Patch older saves missing the new strafe movements
        for mv in ["strafe_lr", "strafe_ud"]:
            if mv not in p["movements"]:
                p["movements"][mv] = copy.deepcopy(DEFAULT_PROFILE["movements"][mv])
        return p
    new = copy.deepcopy(DEFAULT_PROFILE)
    new["name"] = p.get("name", "Profile")
    new["devices"]["stick"]    = p.get("stick1_device_index", 0)
    new["devices"]["throttle"] = p.get("stick2_device_index", -1)
    new["devices"]["pedals"]   = p.get("stick3_device_index", -1)
    old_axes = p.get("axes", {})
    for mv in ["yaw","pitch","roll","thrust"]:
        cfg = old_axes.get(mv, {})
        ai  = cfg.get("axis", NO_AXIS)
        new["movements"][mv]["physical_axis"] = ai
        new["movements"][mv]["key_left"]  = cfg.get("key_neg", new["movements"][mv]["key_left"])
        new["movements"][mv]["key_right"] = cfg.get("key_pos", new["movements"][mv]["key_right"])
        new["movements"][mv]["deadzone"]  = cfg.get("deadzone", 5)
        new["movements"][mv]["speed"]     = cfg.get("max_speed", 50)
    return new

# ─────────────────────────────────────────────────────────────
#  SIGNAL PROCESSING
# ─────────────────────────────────────────────────────────────
def process_axis(raw, dz_pct, inverted, control_points=None, speed=50):
    """
    Returns a value -1..1 representing stick position after deadzone + curve.
    Speed scaling is NOT applied here — PWMAxis applies it via duty cycle.
    """
    if inverted: raw = -raw
    dz = dz_pct / 100.0
    if abs(raw) < dz: return 0.0
    sign = 1.0 if raw > 0 else -1.0
    norm = (abs(raw) - dz) / (1.0 - dz)
    if control_points:
        shaped = eval_custom_curve(norm, control_points)
    else:
        shaped = math.pow(norm, 1.8)   # default gentle expo, full range 0..1
    return sign * min(1.0, shaped)

def keypresses_per_sec(axis_value, speed):
    """How many key presses per second at a given axis value and speed setting."""
    if abs(axis_value) < 0.001: return 0.0
    mag  = abs(axis_value)
    duty = mag * (speed / 100.0)
    freq = 20.0  # fixed 20 Hz cycle
    return freq * duty

def eval_custom_curve(norm_axis, control_points):
    """
    Evaluate curve shape at normalised axis position (0..1 past deadzone).
    Returns 0..1 pure shape value — speed scaling happens separately in PWMAxis.
    Control point Y values are 0..1 fraction of full output.
    """
    anchors = [[0.0, 0.0]] + (control_points or []) + [[1.0, 1.0]]
    if norm_axis <= 0.0: return 0.0
    if norm_axis >= 1.0: return 1.0
    for i in range(len(anchors)-1):
        x0, y0 = anchors[i]; x1, y1 = anchors[i+1]
        if x0 <= norm_axis <= x1:
            if x1 == x0: return y0
            t = (norm_axis - x0) / (x1 - x0)
            return max(0.0, min(1.0, y0 + t*(y1-y0)))
    return 1.0

# ─────────────────────────────────────────────────────────────
#  PWM ENGINE
# ─────────────────────────────────────────────────────────────
class PWMAxis:
    def __init__(self, key_left, key_right, speed=50, pulse=30, key_callback=None):
        self.key_left  = resolve_key(key_left)
        self.key_right = resolve_key(key_right)
        self.speed     = max(1, min(100, speed))
        self.pulse     = max(1, min(100, pulse))  # minimum hold % per cycle (1-100)
        self.value     = 0.0
        self._kb       = KeyController()
        self._l_held   = self._r_held = False
        self._running  = False
        self._lock     = threading.Lock()
        self._key_callback = key_callback

    def start(self):
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self._running = False; self._release_all()

    def set_value(self, v):
        with self._lock: self.value = max(-1.0, min(1.0, v))

    def _release_all(self):
        for held, key in [(self._l_held,self.key_left),(self._r_held,self.key_right)]:
            if held and key:
                try: self._kb.release(key)
                except: pass
        self._l_held = self._r_held = False

    def _run(self):
        # 120Hz cycles = 8.3ms. Two cycles per 16.6ms game frame = consistent alignment.
        # At high deflection (>70%) we skip the release gap entirely — just hold continuously.
        # This eliminates the main source of jitter at speed.
        FREQ      = 120
        cycle     = 1.0 / FREQ
        smooth_v  = 0.0

        while self._running:
            with self._lock: raw_v = self.value

            if raw_v == 0.0:
                smooth_v = 0.0
            else:
                diff   = raw_v - smooth_v
                # Fast convergence below 30% (precision feel), slower above (smooth ramp)
                factor = 0.6 if abs(smooth_v) < 0.3 else 0.3
                smooth_v += diff * factor

            mag  = abs(smooth_v); sign = 1 if smooth_v >= 0 else -1
            act  = self.key_right if sign > 0 else self.key_left
            opp  = self.key_left  if sign > 0 else self.key_right

            if mag < 0.002 or not act:
                self._release_all()
                smooth_v = 0.0
                time.sleep(cycle)
                continue

            opp_held = self._l_held if sign > 0 else self._r_held
            if opp_held and opp:
                try: self._kb.release(opp)
                except: pass
                if sign > 0: self._l_held = False
                else:        self._r_held = False
                smooth_v = 0.0

            scaled   = mag * (max(15, self.speed) / 100.0)  # 15% speed floor
            min_duty = max(8, self.pulse) / 100.0  # 8% pulse floor
            duty     = max(min_duty, scaled)

            # Above 70% deflection: hold continuously — no release gap.
            # Eliminates jitter at speed where PWM granularity stops mattering.
            if duty >= 0.70:
                duty = 0.999

            hold_t    = cycle * min(duty, 0.999)
            release_t = cycle * (1.0 - min(duty, 0.999))

            act_held = self._r_held if sign > 0 else self._l_held
            if not act_held:
                try: self._kb.press(act)
                except: pass
                if sign > 0: self._r_held = True
                else:        self._l_held = True

            if self._key_callback:
                try: self._key_callback(act)
                except: pass

            time.sleep(hold_t)

            if duty < 0.999:
                try: self._kb.release(act)
                except: pass
                if sign > 0: self._r_held = False
                else:        self._l_held = False
                time.sleep(release_t)

# ─────────────────────────────────────────────────────────────
#  JOYSTICK READER
# ─────────────────────────────────────────────────────────────
class JoystickReader:
    """
    Reads joystick axes and auto-calibrates resting offsets.
    Some VKB axes (like twist) park at +1.0 or -1.0 at rest.
    We sample resting values on first read and subtract them,
    so a parked axis reads 0.0 when untouched.
    """
    def __init__(self):
        self.sticks = {}
        self._offsets = {}       # (device_idx, axis_idx) -> resting value to subtract
        self._rec_deadzone = {}  # (device_idx, axis_idx) -> recommended deadzone %
        self._calibrated = set()

    def rescan(self):
        self.sticks = {}
        self._offsets = {}
        self._rec_deadzone = {}
        self._calibrated = set()
        pygame.joystick.quit(); pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            try:
                j = pygame.joystick.Joystick(i); j.init(); self.sticks[i] = j
            except: pass

    def get_names(self): return {i: j.get_name() for i,j in self.sticks.items()}

    def _calibrate(self, idx, j):
        """Sample resting axis values and store recommended deadzone per axis."""
        import math as _m
        pygame.event.pump()
        n_axes = j.get_numaxes()
        samples = [[] for _ in range(n_axes)]
        for _ in range(30):
            pygame.event.pump()
            for a in range(n_axes):
                samples[a].append(j.get_axis(a))
            time.sleep(0.005)
        for a, vals in enumerate(samples):
            avg  = sum(vals) / len(vals)
            peak = max(abs(v) for v in vals)
            # Large offset: axis parks far from zero (twist axis etc)
            if abs(avg) > 0.5:
                self._offsets[(idx, a)] = avg
            # Recommended deadzone = peak resting value + 8% buffer, min 5%
            rec_dz = max(5, min(50, int(_m.ceil((peak + 0.08) * 100))))
            self._rec_deadzone[(idx, a)] = rec_dz
            if peak > 0.02:
                print(f"Calibrate device[{idx}] axis {a}: peak={peak:.3f} → recommended deadzone {rec_dz}%")
        self._calibrated.add(idx)

    def get_recommended_deadzone(self, device_idx, axis_idx):
        """Return recommended deadzone % for this axis based on resting drift."""
        return self._rec_deadzone.get((device_idx, axis_idx), 5)

    def read(self, idx):
        j = self.sticks.get(idx)
        if j is None: return []
        try:
            pygame.event.pump()
        except Exception:
            return []
        try:
            if idx not in self._calibrated:
                self._calibrate(idx, j)
            raw = [j.get_axis(a) for a in range(j.get_numaxes())]
            # Subtract resting offset and rescale to keep -1..1 range
            corrected = []
            for a, v in enumerate(raw):
                off = self._offsets.get((idx, a), 0.0)
                if off != 0.0:
                    if abs(off) > 0.5:
                        # Large offset (parked axis like twist at +1.0/-1.0)
                        # Remap full range: rest=0, opposite end=-1
                        corrected_v = (v - off) / (1.0 + abs(off)) * -1.0
                    else:
                        # Small offset (hardware drift like 0.13 at rest)
                        # Simple subtract and rescale to keep -1..1 range
                        corrected_v = (v - off) / (1.0 - abs(off))
                    corrected.append(max(-1.0, min(1.0, corrected_v)))
                else:
                    corrected.append(v)
            return corrected
        except: return []

# ─────────────────────────────────────────────────────────────
#  PWM WORKER
# ─────────────────────────────────────────────────────────────
class PWMWorker:
    def __init__(self, profile, key_callback=None):
        self.profile = profile; self.pwm = {}; self._running = False
        self.key_callback = key_callback

    def start(self):
        self._running = True
        for name in ["yaw","pitch","roll","thrust","strafe_lr","strafe_ud"]:
            mv = self.profile["movements"].get(name,{})
            p  = PWMAxis(mv.get("key_left",""),mv.get("key_right",""),
                         mv.get("speed",50), mv.get("pulse",30),
                         self.key_callback)
            p.start(); self.pwm[name] = p

    def stop(self):
        self._running = False
        for p in self.pwm.values(): p.stop()
        self.pwm.clear()

    def feed(self, name, v):
        if name in self.pwm:
            self.pwm[name].set_value(v)

    def sync(self):
        for name, pwm in self.pwm.items():
            mv = self.profile["movements"].get(name,{})
            pwm.key_left  = resolve_key(mv.get("key_left",""))
            pwm.key_right = resolve_key(mv.get("key_right",""))
            pwm.speed     = max(1,min(100,mv.get("speed",50)))
            pwm.pulse     = max(1,min(100,mv.get("pulse",30)))

    @property
    def active(self): return self._running

# ─────────────────────────────────────────────────────────────
#  SCROLL-WHEEL BLOCKER — prevents accidental slider scrolling
# ─────────────────────────────────────────────────────────────
class NoScrollSlider(QSlider):
    def wheelEvent(self, e): e.ignore()

class NoScrollCombo(QComboBox):
    def wheelEvent(self, e): e.ignore()

# ─────────────────────────────────────────────────────────────
#  KEY CAPTURE FIELD  — press any key to set it
# ─────────────────────────────────────────────────────────────
class KeyCaptureField(QLineEdit):
    """
    Click to focus, then press any key — including shift/ctrl/alt/space etc.
    The field shows the key name and emits textChanged like a normal QLineEdit.
    """
    # Map Qt key codes -> our string names
    SPECIAL = {
        Qt.Key.Key_Shift:     "shift",    Qt.Key.Key_Control:   "ctrl",
        Qt.Key.Key_Alt:       "alt",      Qt.Key.Key_Space:     "space",
        Qt.Key.Key_Tab:       "tab",      Qt.Key.Key_Return:    "enter",
        Qt.Key.Key_Enter:     "enter",    Qt.Key.Key_Escape:    "esc",
        Qt.Key.Key_Backspace: "backspace",Qt.Key.Key_Delete:    "delete",
        Qt.Key.Key_Home:      "home",     Qt.Key.Key_End:       "end",
        Qt.Key.Key_PageUp:    "page_up",  Qt.Key.Key_PageDown:  "page_down",
        Qt.Key.Key_Insert:    "insert",   Qt.Key.Key_CapsLock:  "caps_lock",
        Qt.Key.Key_Up:        "up",       Qt.Key.Key_Down:      "down",
        Qt.Key.Key_Left:      "left",     Qt.Key.Key_Right:     "right",
        Qt.Key.Key_F1:  "f1",  Qt.Key.Key_F2:  "f2",  Qt.Key.Key_F3:  "f3",
        Qt.Key.Key_F4:  "f4",  Qt.Key.Key_F5:  "f5",  Qt.Key.Key_F6:  "f6",
        Qt.Key.Key_F7:  "f7",  Qt.Key.Key_F8:  "f8",  Qt.Key.Key_F9:  "f9",
        Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._capturing = False
        self.setPlaceholderText("click then press a key")
        self.setReadOnly(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, e):
        self._capturing = True
        self.setStyleSheet(self.styleSheet() + "border-")
        self.setPlaceholderText("press a key now...")
        super().mousePressEvent(e)

    def focusOutEvent(self, e):
        self._capturing = False
        self.setPlaceholderText("click then press a key")
        super().focusOutEvent(e)

    def keyPressEvent(self, e):
        if not self._capturing:
            super().keyPressEvent(e); return
        key = e.key()
        # Look up special keys first
        if key in self.SPECIAL:
            name = self.SPECIAL[key]
        else:
            # For regular keys, use the text character
            text = e.text().strip().lower()
            if text and text.isprintable():
                name = text
            else:
                return  # ignore unknown keys
        self.setText(name)
        self._capturing = False
        self.clearFocus()

    def wheelEvent(self, e): e.ignore()


# ─────────────────────────────────────────────────────────────
#  KEY TEST DISPLAY  — scrolling view of keypress outputs
# ─────────────────────────────────────────────────────────────
class KeyTestDisplay(QWidget):
    """
    Horizontally scrolling tape showing every keypress.
    Newest events appear on the RIGHT and the tape scrolls left.
    The tape is conceptually infinite — we keep the last MAX_EVENTS
    and render only what fits in the widget width.
    """
    MAX_EVENTS = 600
    BLOCK_W    = 52
    GAP        = 5
    SLOT_W     = 57   # BLOCK_W + GAP

    def __init__(self):
        super().__init__()
        self.events = []   # list of (key_name, timestamp)
        self.setFixedHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def add_key(self, key_name):
        self.events.append((str(key_name), time.perf_counter()))
        if len(self.events) > self.MAX_EVENTS:
            self.events = self.events[-self.MAX_EVENTS:]
        self.update()

    def clear(self):
        self.events = []; self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mid = h // 2

        # Background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(_GC["bg"])); p.drawRect(0, 0, w, h)

        # Dot grid
        p.setPen(QPen(QColor(22, 14, 44), 1))
        for gx in range(0, w, 20):
            for gy in range(8, h-8, 20):
                p.drawPoint(gx, gy)

        # Timeline
        p.setPen(QPen(QColor(50, 35, 90), 1)); p.drawLine(0, mid, w, mid)
        p.setPen(QPen(QColor(40, 28, 76), 1))
        for x in range(0, w, 40):
            p.drawLine(x, mid-5, x, mid+5)

        if not self.events:
            p.setFont(QFont(MONO, 12)); p.setPen(QPen(QColor(60, 50, 100)))
            p.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter,
                       "key presses will appear here when START is active")
            p.setPen(QPen(QColor(80, 60, 140), 1)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(0, 0, w-1, h-1); return

        now = time.perf_counter()
        n   = len(self.events)
        slot = self.SLOT_W

        # The rightmost slot ends at w-4.
        # Slot i (0=newest, 1=second newest…) starts at:
        #   right_x = (w - 4) - i * slot
        # We draw from newest (right) to oldest (left), stopping when off-screen.
        block_h = 40; top = mid - block_h // 2

        for i in range(n):
            idx      = n - 1 - i          # index into self.events (newest = n-1)
            key_name, ts = self.events[idx]
            rx = (w - 4) - i * slot       # right edge of this block
            lx = rx - self.BLOCK_W
            if rx < 0: break              # fully off left edge

            age   = now - ts
            alpha = max(30, min(255, int(255 * max(0, 1.0 - age / 10.0))))

            # Block fill — brighter for recent
            bg = QColor(40, 20, 100, min(210, alpha))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(bg))
            p.drawRoundedRect(lx, top, self.BLOCK_W, block_h, 4, 4)

            # Yellow border, brighter for newest
            border_a = min(255, alpha + 60)
            p.setPen(QPen(QColor(240, 192, 48, border_a), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(lx, top, self.BLOCK_W, block_h, 4, 4)

            # Stem to timeline
            cx = lx + self.BLOCK_W // 2
            p.setPen(QPen(QColor(120, 90, 200, min(160, alpha)), 1))
            p.drawLine(cx, mid, cx, top)
            p.drawLine(cx, mid, cx, top + block_h)

            # Key label
            display = key_name if len(key_name) <= 5 else key_name[:4] + "…"
            p.setFont(QFont(MONO, 10, QFont.Weight.Bold))
            p.setPen(QPen(QColor(255, 255, 255, min(255, alpha))))
            p.drawText(lx, top, self.BLOCK_W, block_h,
                       Qt.AlignmentFlag.AlignCenter, display)

        # Outer border
        p.setPen(QPen(QColor(80, 60, 140), 1)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(0, 0, w-1, h-1)

    def wheelEvent(self, e): e.ignore()


# ─────────────────────────────────────────────────────────────
#  COLORS
# ─────────────────────────────────────────────────────────────
C_BG     = QColor(6,  4, 14)
C_CARD   = QColor(12, 9, 24)
C_BORDER = QColor(60, 40,130)
C_BORDER2= QColor(30, 20, 70)
C_WHITE  = QColor(220,215,255)
C_PURPLE = QColor(160, 90,240)
C_BLUE   = QColor(70, 150,255)
C_DIM    = QColor(60,  45,120)
C_GRID   = QColor(24,  18, 48)
C_GREEN  = QColor(50, 200,120)
C_RED    = QColor(220, 70, 70)
C_ACTIVE = QColor(100,220,100)
MONO     = "Courier New"

def bar_color(frac):
    frac = max(0.0,min(1.0,frac))
    if frac < 0.5:
        t=frac*2; return QColor(int(70+t*90),int(150-t*50),255)
    t=(frac-0.5)*2; return QColor(int(160+t*40),int(100+t*115),255)

# ─────────────────────────────────────────────────────────────
#  KEYPRESS CURVE WIDGET
# ─────────────────────────────────────────────────────────────
class KeypressCurveWidget(QWidget):
    """
    Interactive curve editor: drag control points to reshape the
    keypresses-per-second vs stick-angle curve.

    Control points live in normalised (axis_frac, kps_frac) space
    where axis_frac 0..1 = centre..full deflection
    and kps_frac 0..1 = 0..max_kps.

    Three fixed handles are shown (25%, 50%, 75% stick angle).
    The first point is pinned at the deadzone edge (output=0).
    The last point is pinned at full deflection (output=max_speed).
    """
    curve_changed = pyqtSignal(list)   # emits control_points list

    MAX_KPS = 20.0
    PAD_L, PAD_R, PAD_T, PAD_B = 52, 18, 16, 36
    HANDLE_R = 8   # handle radius px

    def __init__(self):
        super().__init__()
        self.speed    = 50
        self.deadzone = 5
        self.pulse    = 30
        self.live_raw = 0.0
        self.live_proc = 0.0
        # Control points: list of [axis_frac, kps_frac]
        # axis_frac: 0=deadzone edge .. 1=full deflection (normalised past deadzone)
        # kps_frac:  0=0 kps .. 1=max_kps
        self._points = self._default_points()
        self._drag_idx  = -1
        self._hover_idx = -1
        self.setFixedHeight(420)
        self.setMinimumWidth(320)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    # ── geometry helpers ─────────────────────────────────────
    def _geom(self):
        w, h = self.width(), self.height()
        gw = w - self.PAD_L - self.PAD_R
        gh = h - self.PAD_T - self.PAD_B
        return w, h, gw, gh

    def _pt_to_px(self, ax, ky):
        """Map control point (post-deadzone normalized) to pixel coords.
        ax is 0..1 in the space AFTER deadzone removal.
        raw_frac = dz + ax * (1 - dz)  maps it back to full raw range.
        """
        _, _, gw, gh = self._geom()
        dz = max(self.deadzone, 15) / 100.0
        raw_frac = dz + ax * (1.0 - dz)   # map back to raw stick fraction
        px = self.PAD_L + int(raw_frac * gw)
        py = self.PAD_T + gh - int(ky * gh)
        return px, py

    def _px_to_pt(self, px, py):
        """Pixel coords -> (post-deadzone ax, kps_frac), clamped."""
        _, _, gw, gh = self._geom()
        dz = max(self.deadzone, 15) / 100.0
        raw_frac = max(0.0, min(1.0, (px - self.PAD_L) / gw))
        # Convert raw fraction back to post-deadzone normalized
        if raw_frac <= dz:
            ax = 0.0
        else:
            ax = (raw_frac - dz) / (1.0 - dz)
        ax = max(0.0, min(1.0, ax))
        ky = max(0.0, min(1.0, (self.PAD_T + gh - py) / gh))
        return ax, ky

    CURVE_PRESETS = {
        "Gentle":     [(0.125,0.0199),(0.25,0.0841),(0.375,0.1913),(0.5,0.2973),(0.625,0.4031),(0.75,0.5199),(0.875,0.6894)],
        "Expo":       [(0.125,0.0702),(0.25,0.2378),(0.375,0.4030),(0.5,0.5547),(0.625,0.6955),(0.75,0.8176),(0.875,0.9285)],
        "Linear":     [(0.125,0.125), (0.25,0.25),  (0.375,0.375), (0.5,0.5),   (0.625,0.625), (0.75,0.75),  (0.875,0.875)],
        "Early":      [(0.125,0.2333),(0.25,0.3789),(0.375,0.5033),(0.5,0.6156),(0.625,0.7196),(0.75,0.8176),(0.875,0.9108)],
        "Aggressive": [(0.125,0.4040),(0.25,0.5743),(0.375,0.6984),(0.5,0.8000),(0.625,0.8731),(0.75,0.9330),(0.875,0.9760)],
    }
    # Default preset name
    DEFAULT_PRESET = "Expo"

    def _default_points(self):
        """Default to Early — gives more motion in the first 50% of travel."""
        return [list(p) for p in self.CURVE_PRESETS[self.DEFAULT_PRESET]]

    def load_preset(self, name):
        if name in self.CURVE_PRESETS:
            self._points = [list(p) for p in self.CURVE_PRESETS[name]]
            self.curve_changed.emit(self.get_control_points())
            self.update()

    def _kps_at(self, norm_axis):
        """
        Returns keypresses/sec at norm_axis (0..1 past deadzone).
        Y values in control points are pure shape 0..1.
        Speed scales the final output.
        """
        anchors = [[0.0, 0.0]] + self._points + [[1.0, 1.0]]
        if norm_axis <= 0.0: shape = 0.0
        elif norm_axis >= 1.0: shape = 1.0
        else:
            shape = 1.0
            for i in range(len(anchors)-1):
                x0, y0 = anchors[i]; x1, y1 = anchors[i+1]
                if x0 <= norm_axis <= x1:
                    if x1 == x0: shape = y0; break
                    t = (norm_axis - x0) / (x1 - x0)
                    shape = max(0.0, min(1.0, y0 + t*(y1-y0))); break
        return shape * (self.speed / 100.0) * self.MAX_KPS

    def _handle_at(self, px, py):
        """Return index of control point under (px,py), or -1."""
        for i, (ax, ky) in enumerate(self._points):
            hx, hy = self._pt_to_px(ax, ky)
            if math.hypot(px-hx, py-hy) <= self.HANDLE_R + 4:
                return i
        return -1

    # ── public API ───────────────────────────────────────────
    def set_params(self, speed, deadzone, pulse=None):
        self.speed    = speed
        self.deadzone = deadzone
        if pulse is not None: self.pulse = pulse
        self.update()

    def set_live(self, raw_val=0.0, proc_val=None):
        self.live_raw  = abs(raw_val)
        self.live_proc = abs(proc_val) if proc_val is not None else abs(raw_val)
        self.update()

    def get_control_points(self):
        return [list(p) for p in self._points]

    def set_control_points(self, pts):
        if pts: self._points = [list(p) for p in pts]
        self.update()

    def reset_curve(self):
        self._points = self._default_points()
        self.curve_changed.emit(self.get_control_points())
        self.update()

    # ── mouse events ─────────────────────────────────────────
    def wheelEvent(self, e): e.ignore()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            idx = self._handle_at(int(e.position().x()), int(e.position().y()))
            if idx >= 0:
                self._drag_idx = idx
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        px, py = int(e.position().x()), int(e.position().y())
        if self._drag_idx >= 0:
            ax, ky = self._px_to_pt(px, py)
            # Clamp X so points stay in order
            lo = self._points[self._drag_idx-1][0]+0.01 if self._drag_idx>0 else 0.02
            hi = self._points[self._drag_idx+1][0]-0.01 if self._drag_idx<len(self._points)-1 else 0.98
            ax = max(lo, min(hi, ax))
            self._points[self._drag_idx] = [ax, ky]
            self.curve_changed.emit(self.get_control_points())
            self.update()
        else:
            hi = self._handle_at(px, py)
            if hi != self._hover_idx:
                self._hover_idx = hi
                self.setCursor(Qt.CursorShape.OpenHandCursor if hi >= 0 else Qt.CursorShape.ArrowCursor)
                self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_idx = -1
            self.setCursor(Qt.CursorShape.OpenHandCursor if self._hover_idx >= 0 else Qt.CursorShape.ArrowCursor)

    def mouseDoubleClickEvent(self, e):
        # Double-click reset
        self.reset_curve()

    # ── paint ────────────────────────────────────────────────
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h, gw, gh = self._geom()
        dz = self.deadzone / 100.0

        # Background
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(_GC["bg"]))
        p.drawRect(0, 0, w, h)

        # Grid
        p.setPen(QPen(_GC["grid"], 1))
        for frac in [0.25, 0.5, 0.75, 1.0]:
            gy = self.PAD_T + gh - int(frac * gh)
            p.drawLine(self.PAD_L, gy, self.PAD_L+gw, gy)
            p.setFont(QFont(MONO, 9)); p.setPen(QPen(_GC["dim"]))
            kv = frac * self.MAX_KPS
            p.drawText(0, gy-8, self.PAD_L-4, 16,
                Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter, f"{kv:.0f}")
            p.setPen(QPen(_GC["grid"], 1))
        for frac in [0.25, 0.5, 0.75, 1.0]:
            gx = self.PAD_L + int(frac * gw)
            p.drawLine(gx, self.PAD_T, gx, self.PAD_T+gh)
            p.setFont(QFont(MONO, 9)); p.setPen(QPen(_GC["dim"]))
            p.drawText(gx-20, self.PAD_T+gh+2, 40, 14,
                Qt.AlignmentFlag.AlignHCenter, f"{frac:.0%}")
            p.setPen(QPen(_GC["grid"], 1))

        # Deadzone marker
        dz_x = self.PAD_L + int(dz * gw)
        p.setPen(QPen(_GC["dz"], 1, Qt.PenStyle.DashLine))
        p.drawLine(dz_x, self.PAD_T, dz_x, self.PAD_T+gh)
        p.setFont(QFont(MONO, 9)); p.setPen(QPen(_GC["dz"]))
        p.drawText(dz_x+3, self.PAD_T+2, 60, 14, Qt.AlignmentFlag.AlignLeft, "dead zone")

        # Curve (piecewise linear through control points)
        curve_path = QPainterPath()
        first = True
        for i in range(201):
            af = i / 200.0   # 0..1 = centre..full
            if af < dz:
                kps = 0.0
            else:
                norm = (af - dz) / (1.0 - dz)  # normalised past deadzone
                kps  = self._kps_at(norm)
            cx = self.PAD_L + int(af * gw)
            cy = self.PAD_T + gh - int(min(kps / self.MAX_KPS, 1.0) * gh)
            if first: curve_path.moveTo(cx, cy); first = False
            else:      curve_path.lineTo(cx, cy)

        grad = QLinearGradient(self.PAD_L, 0, self.PAD_L+gw, 0)
        grad.setColorAt(0, _GC["curve0"]); grad.setColorAt(1, _GC["curve1"])
        p.setPen(QPen(QBrush(grad), 2.5)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(curve_path)

        # Ghost reference curve (default expo)
        ghost = QPainterPath(); first = True
        for i in range(201):
            af = i / 200.0
            if af < dz: kps = 0.0
            else:
                norm = (af - dz) / (1.0 - dz)
                kps  = math.pow(norm, 1.8) * (self.speed/100.0) * self.MAX_KPS
            cx = self.PAD_L + int(af * gw)
            cy = self.PAD_T + gh - int(min(kps/self.MAX_KPS,1.0)*gh)
            if first: ghost.moveTo(cx,cy); first=False
            else: ghost.lineTo(cx,cy)
        # Full-speed reference line (green)
        p.setPen(QPen(_GC["maxspd"], 1, Qt.PenStyle.DashLine))
        max_y = self.PAD_T + gh - int((self.speed/100.0) * gh)
        p.drawLine(self.PAD_L, max_y, self.PAD_L+gw, max_y)
        p.setFont(QFont(MONO,9)); p.setPen(QPen(_GC["maxspd"]))
        p.drawText(self.PAD_L+4, max_y-14, 120, 12, Qt.AlignmentFlag.AlignLeft, f"max speed ({self.speed}%)")
        # Pulse floor line — the minimum kps output regardless of stick position.
        # At any stick deflection, duty = max(pulse/100, shaped_output * speed/100)
        # So minimum kps = (pulse/100) * MAX_KPS  (it acts as a minimum duty floor)
        pulse_frac = self.pulse / 100.0              # 0..1 fraction of max kps
        pulse_kps  = pulse_frac * self.MAX_KPS       # actual min kps value
        pulse_y    = self.PAD_T + gh - int(pulse_frac * gh)
        p.setPen(QPen(_GC["pulse"], 1, Qt.PenStyle.DashLine))
        p.drawLine(self.PAD_L, pulse_y, self.PAD_L+gw, pulse_y)
        p.setFont(QFont(MONO,9)); p.setPen(QPen(_GC["pulse"]))
        p.drawText(self.PAD_L+4, pulse_y+2, 220, 12, Qt.AlignmentFlag.AlignLeft,
                   f"min pulse ({self.pulse}% = {pulse_kps:.1f} kps floor)")
        p.setPen(QPen(_GC["ghost"], 1, Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(ghost)

        # Control point connectors (thin dashed line between anchors)
        anchors = [[0.0, 0.0]] + self._points + [[1.0, 1.0]]
        for i in range(len(anchors)-1):
            ax0,ky0 = anchors[i];   hx0,hy0 = self._pt_to_px(ax0,ky0)
            ax1,ky1 = anchors[i+1]; hx1,hy1 = self._pt_to_px(ax1,ky1)
            p.setPen(QPen(QColor(100,70,180,100),1,Qt.PenStyle.DotLine))
            p.drawLine(hx0,hy0,hx1,hy1)

        # Control point handles
        for i, (ax, ky) in enumerate(self._points):
            hx, hy = self._pt_to_px(ax, ky)
            is_hover = (i == self._hover_idx)
            is_drag  = (i == self._drag_idx)
            outer_r  = self.HANDLE_R + (3 if is_hover or is_drag else 0)
            # Glow
            glow = QColor(180,100,255, 80 if is_drag else 40)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(glow))
            p.drawEllipse(hx-outer_r-4, hy-outer_r-4, (outer_r+4)*2, (outer_r+4)*2)
            # Fill
            fill = _GC["handle_d"] if is_drag else (_GC["handle_h"] if is_hover else _GC["handle"])
            p.setBrush(QBrush(fill)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(hx-outer_r, hy-outer_r, outer_r*2, outer_r*2)
            # White dot centre
            p.setBrush(QBrush(Qt.GlobalColor.white))
            p.drawEllipse(hx-3, hy-3, 6, 6)
            # Tooltip label — ky is shape 0..1, scale by speed for display
            kps_here = ky * (self.speed / 100.0) * self.MAX_KPS
            p.setFont(QFont(MONO, 9, QFont.Weight.Bold)); p.setPen(QPen(_GC["label"]))
            label = f"{kps_here:.1f}/s"
            lx = hx+outer_r+3 if hx < self.PAD_L+gw-60 else hx-outer_r-50
            p.drawText(lx, hy-6, 60, 14, Qt.AlignmentFlag.AlignLeft, label)

        # Live dot — X from raw stick position, Y from curve function (matches drawn line)
        live_raw = abs(self.live_raw)
        if live_raw > 0.001:
            # Compute Y using the same function as the drawn curve
            if live_raw <= dz:
                kps_live = 0.0
            else:
                norm     = (live_raw - dz) / (1.0 - dz)
                kps_live = self._kps_at(norm)
            lx = self.PAD_L + int(live_raw * gw)
            ly = self.PAD_T + gh - int(min(kps_live / self.MAX_KPS, 1.0) * gh)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(100,255,150,60)))
            p.drawEllipse(lx-12,ly-12,24,24)
            p.setBrush(QBrush(_GC["live"])); p.drawEllipse(lx-5,ly-5,10,10)
            p.setFont(QFont(MONO,11,QFont.Weight.Bold)); p.setPen(QPen(_GC["live"]))
            p.drawText(lx+10, ly-14, 140, 16, Qt.AlignmentFlag.AlignLeft,
                       f"{kps_live:.1f} fires/sec")

        # Axis labels
        p.setFont(QFont(MONO,10)); p.setPen(QPen(_GC["label"]))
        p.drawText(self.PAD_L, self.PAD_T+gh+18, gw, 16,
            Qt.AlignmentFlag.AlignHCenter, "stick angle  →  (left = center,  right = full deflection)")
        p.setFont(QFont(MONO,9)); p.setPen(QPen(_GC["label"]))
        p.drawText(2, self.PAD_T, self.PAD_L-4, gh,
            Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop, "fires\n/sec")
        # Hint
        p.setFont(QFont(MONO,9)); p.setPen(QPen(_GC["label"]))
        p.drawText(self.PAD_L+4, self.PAD_T+2, gw-8, 14,
            Qt.AlignmentFlag.AlignRight, "drag handles to reshape  •  double-click to reset")

        # Border
        p.setPen(QPen(_GC["border"],1)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(self.PAD_L, self.PAD_T, gw, gh)

# ─────────────────────────────────────────────────────────────
#  LIVE BAR
# ─────────────────────────────────────────────────────────────
class LiveBar(QWidget):
    def __init__(self, label):
        super().__init__()
        self.label = label; self.value = 0.0; self.active = False
        self.setFixedHeight(52)

    def set_value(self, v, active=True):
        self.value = v; self.active = active; self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        lw=160; vw=80; bx=lw; bw=w-lw-vw; mid=bx+bw//2; by=8; bh=h-16
        p.setFont(QFont(MONO,18,QFont.Weight.Bold))
        p.setPen(QPen(QColor(100,255,150) if self.active and abs(self.value)>0.01 else QColor(200,190,255)))
        p.drawText(0,0,lw,h,Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,self.label)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(C_BG)); p.drawRect(bx,by,bw,bh)
        p.setPen(QPen(C_GRID,1)); p.drawLine(mid,by,mid,by+bh)
        if abs(self.value)>0.005:
            fw=int(abs(self.value)*bw/2); fx=(mid-fw) if self.value>0 else mid
            c=bar_color(abs(self.value))
            if not self.active: c.setAlpha(80)
            p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen); p.drawRect(fx,by,fw,bh)
        p.setPen(QPen(C_BORDER2,1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRect(bx,by,bw,bh)
        p.setFont(QFont(MONO,18)); p.setPen(QPen(QColor(200,190,255) if not self.active else QColor(255,255,255)))
        p.drawText(bx+bw+6,0,vw-6,h,Qt.AlignmentFlag.AlignVCenter,f"{self.value:+.2f}")

# ─────────────────────────────────────────────────────────────
#  DETECTOR WIDGET
# ─────────────────────────────────────────────────────────────
class DetectorWidget(QWidget):
    picked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.values=[]; self.selected=-1; self.loudest=-1
        self.setFixedHeight(90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def update_values(self, vals):
        if vals: self.loudest=max(range(len(vals)),key=lambda i:abs(vals[i]))
        self.values=vals; self.update()

    def wheelEvent(self, e): e.ignore()

    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height()
        n=max(len(self.values),1); gap=6
        bw=max(10,(w-gap*(n+1))//n)
        lh=22; bh=h-lh-4
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(C_BG)); p.drawRect(0,0,w,h)
        for i,val in enumerate(self.values):
            x=gap+i*(bw+gap)
            p.setBrush(QBrush(QColor(16,10,32))); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x,2,bw,bh,3,3)
            if abs(val)>0.01:
                fh=int(abs(val)*bh); fy=bh-fh+2
                c=bar_color(abs(val)); c.setAlpha(220)
                p.setBrush(QBrush(c)); p.drawRect(x,fy,bw,fh)
            if i==self.selected:   bc=C_GREEN; bthick=3
            elif i==self.loudest and abs(self.values[i])>0.1: bc=C_WHITE; bthick=2
            else: bc=C_BORDER2; bthick=1
            p.setPen(QPen(bc,bthick)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(x,2,bw,bh,3,3)
            p.setFont(QFont(MONO,12,QFont.Weight.Bold))
            p.setPen(QPen(C_GREEN if i==self.selected else (C_WHITE if i==self.loudest and abs(self.values[i])>0.1 else C_DIM)))
            p.drawText(x,bh+4,bw,lh,Qt.AlignmentFlag.AlignHCenter,str(i))
        p.setPen(QPen(C_BORDER2,1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRect(0,0,w-1,h-1)

    def mousePressEvent(self,e):
        n=max(len(self.values),1); gap=6
        bw=max(10,(self.width()-gap*(n+1))//n); x=e.position().x()
        for i in range(len(self.values)):
            bx=gap+i*(bw+gap)
            if bx<=x<=bx+bw:
                self.selected=i; self.picked.emit(i); self.update(); return

# ─────────────────────────────────────────────────────────────
#  MOVEMENT CARD
# ─────────────────────────────────────────────────────────────
class MovementCard(QWidget):
    changed = pyqtSignal()

    def __init__(self, mv_name, mv_cfg, device_label=""):
        super().__init__()
        self.mv_name=mv_name; self.cfg=dict(mv_cfg); self.device_label=device_label
        label_data=MOVEMENT_LABELS.get(mv_name,(mv_name.upper(),"",""))
        self.short_label,self.action_label,self.description=label_data
        self.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 rgba(255,255,255,14),stop:0.12 rgba(255,255,255,4),stop:0.88 rgba(0,0,20,8),stop:1 rgba(0,0,40,22));border:1px solid rgba(200,180,255,80);border-top:1px solid rgba(255,255,255,50);border-radius:10px;")
        self._build()

    def _build(self):
        outer=QVBoxLayout(self); outer.setContentsMargins(24,18,24,18); outer.setSpacing(14)

        # Header
        hdr=QHBoxLayout()
        name_lbl=QLabel(self.short_label)
        name_lbl.setStyleSheet("font-size:26px;font-weight:bold;letter-spacing:3px")
        action_lbl=QLabel(f"  —  {self.action_label}")
        action_lbl.setStyleSheet("font-size:20px")
        desc_lbl=QLabel(self.description)
        desc_lbl.setStyleSheet("font-size:16px;font-style:italic")

        hdr.addWidget(name_lbl); hdr.addWidget(action_lbl); hdr.addStretch()
        hdr.addWidget(desc_lbl)
        outer.addLayout(hdr)
        outer.addWidget(self._hline())

        # Step 1 — axis
        outer.addWidget(self._step_label("STEP 1",
            "Which physical axis controls this movement?  "
            "Click DETECT, move the axis on your stick, click the bar that lights up."))
        ai_row=QHBoxLayout(); ai_row.setSpacing(14)
        self._axis_display=QLabel(self._axis_text())
        self._axis_display.setStyleSheet(
            "background:rgba(8,4,20,200);border:1px solid rgba(200,180,255,100);"
            "border-top:1px solid rgba(255,255,255,40);border-radius:6px;"
            "color:#ffffff;font-size:24px;font-weight:bold;font-family:Courier New;"
            "padding:10px 20px;min-width:280px;")
        ai_row.addWidget(self._axis_display)
        detect_btn=QPushButton("DETECT  →  1) Click here  2) Move your axis  3) Click the bar that lights up")
        detect_btn.setStyleSheet(
            "background:rgba(255,200,40,15);border:1px solid rgba(255,200,40,120);"
            "border-top:1px solid rgba(255,255,255,30);border-radius:6px;"
            "font-family:Courier New;font-size:18px;padding:10px 20px;")
        detect_btn.clicked.connect(self._on_detect_click)
        ai_row.addWidget(detect_btn,stretch=1)
        not_used_btn=QPushButton("NOT  USED")
        not_used_btn.setFixedWidth(140)
        not_used_btn.setStyleSheet(
            "background:rgba(200,40,40,20);border:1px solid rgba(200,60,60,140);"
            "border-radius:6px;font-family:Courier New;font-size:18px;padding:10px;")
        not_used_btn.setToolTip("Disable this movement completely")
        not_used_btn.clicked.connect(self._mark_unused)
        ai_row.addWidget(not_used_btn)
        outer.addLayout(ai_row)
        self._detector=DetectorWidget(); self._detector.setVisible(False)
        self._detector.picked.connect(self._axis_picked)
        outer.addWidget(self._detector)
        outer.addWidget(self._hline())

        # Step 2+3 combined — left=keys+sliders, right=graph
        outer.addWidget(self._step_label("STEP 2 + 3",
            "Set the key for each direction (click a field, press a key). "
            "Tune feel with sliders. Drag curve handles to shape the response."))
        feel_outer=QHBoxLayout(); feel_outer.setSpacing(28)

        # ── Left column: keys + sliders + invert ──────────────
        left_col=QVBoxLayout(); left_col.setSpacing(14)

        # Keys (compact, stacked)
        keys_lbl=QLabel("KEYS")
        keys_lbl.setStyleSheet("font-size:18px;font-weight:bold;letter-spacing:3px")
        left_col.addWidget(keys_lbl)

        def key_field_compact(direction, val, tip):
            row=QHBoxLayout(); row.setSpacing(8)
            lbl=QLabel(direction); lbl.setFixedWidth(200)
            lbl.setStyleSheet("font-size:16px")
            edit=KeyCaptureField(val); edit.setFixedHeight(46)
            edit.setStyleSheet(
                "background:rgba(8,4,20,200);border:1px solid rgba(200,180,255,100);"
                "border-top:1px solid rgba(255,255,255,30);border-radius:6px;"
                "padding:6px 12px;color:#ffffff;font-size:26px;font-weight:bold;font-family:Courier New;")
            edit.setToolTip(tip)
            row.addWidget(lbl); row.addWidget(edit,stretch=1)
            return edit,row

        # Movement-specific key direction labels
        _key_labels = {
            "yaw":       ("← TURN LEFT",       "→ TURN RIGHT"),
            "pitch":     ("← NOSE UP",          "→ NOSE DOWN"),
            "roll":      ("← ROLL LEFT",        "→ ROLL RIGHT"),
            "thrust":    ("← BACKWARD",         "→ FORWARD"),
            "strafe_lr": ("← STRAFE LEFT",      "→ STRAFE RIGHT"),
            "strafe_ud": ("← STRAFE DOWN",      "→ STRAFE UP"),
            "pedals":    ("← LEFT PEDAL",       "→ RIGHT PEDAL"),
        }
        _lbl_neg, _lbl_pos = _key_labels.get(self.mv_name, ("← NEGATIVE", "→ POSITIVE"))
        self.key_left,left_row=key_field_compact(_lbl_neg, self.cfg.get("key_left",""),
            "Key pressed when axis moves in the negative direction")
        self.key_right,right_row=key_field_compact(_lbl_pos, self.cfg.get("key_right",""),
            "Key pressed when axis moves in the positive direction")
        left_col.addLayout(left_row); left_col.addLayout(right_row)

        clr_row=QHBoxLayout()
        clr_btn=QPushButton("CLEAR KEYS"); clr_btn.setFixedHeight(40)
        clr_btn.setStyleSheet("background:rgba(200,40,40,20);border:1px solid rgba(200,60,60,140);border-radius:6px;font-size:17px;font-weight:bold")
        clr_btn.clicked.connect(lambda:(self.key_left.setText(""),self.key_right.setText("")))
        clr_row.addWidget(clr_btn); clr_row.addStretch()
        left_col.addLayout(clr_row)

        left_col.addWidget(self._hline())

        # Sliders
        def sl_row(label,tip,lo,hi,val,fmt):
            col=QVBoxLayout(); col.setSpacing(4)
            lbl=QLabel(label); lbl.setStyleSheet("font-size:15px;font-weight:bold")
            sl=NoScrollSlider(Qt.Orientation.Horizontal)
            sl.setRange(lo,hi); sl.setValue(val); sl.setFixedHeight(36); sl.setToolTip(tip)
            vl=QLabel(fmt(val)); vl.setStyleSheet("font-size:16px;font-weight:bold;min-width:160px")
            sl.valueChanged.connect(lambda v:vl.setText(fmt(v)))
            r=QHBoxLayout(); r.addWidget(sl,stretch=1); r.addWidget(vl)
            col.addWidget(lbl); col.addLayout(r)
            return sl,col

        self.dz_sl,dz_col=sl_row("DEAD ZONE",
            "How far to move before responding.\n"
            "Hard minimum: 15% (hardware drift compensation).\n"
            "Increase if axis drifts at rest.",
            15, 40, max(15, min(40, self.cfg.get("deadzone",15))),
            lambda v: f"{'min' if v<=15 else 'small' if v<20 else 'medium' if v<30 else 'large'} ({v}%)")
        self.spd_sl,spd_col=sl_row("THRUSTER FIRE RATE",
            "Keypresses per second = how many times the thruster fires.\n"
            "Low = fires rarely = slow build-up.  High = fires rapidly = fast acceleration.\n"
            "Functional range 15-85%. Above 85% the key holds continuously.",
            15, 85, max(15, min(85, self.cfg.get("speed",50))),
            lambda v: f"{'slow' if v<30 else 'medium' if v<55 else 'fast' if v<75 else 'max'} ({v}%)")
        self.pls_sl,pls_col=sl_row("THRUSTER BURN TIME",
            "How long the key is held = how long each thruster firing lasts.\n"
            "Short = brief burst, easy to stop.  Long = sustained burn, builds momentum.\n"
            "Functional range 8-50%. Below 8% the game may not register the firing.",
            8, 50, max(8, min(50, self.cfg.get("pulse",15))),
            lambda v: f"{'brief' if v<=15 else 'medium' if v<=30 else 'long'} burn ({v}%)")
        left_col.addLayout(dz_col); left_col.addLayout(spd_col); left_col.addLayout(pls_col)

        inv_row=QHBoxLayout(); inv_row.setSpacing(12)
        inv_lbl=QLabel("DIRECTION:"); inv_lbl.setStyleSheet("font-size:15px;font-weight:bold")
        self.inv_btn=QPushButton("NORMAL")
        self.inv_btn.setCheckable(True); self.inv_btn.setChecked(self.cfg.get("inverted",False))
        self.inv_btn.setText("INVERTED" if self.cfg.get("inverted",False) else "NORMAL")
        self.inv_btn.setFixedHeight(46); self.inv_btn.setMinimumWidth(160)
        self.inv_btn.clicked.connect(lambda:self.inv_btn.setText("INVERTED" if self.inv_btn.isChecked() else "NORMAL"))
        inv_row.addWidget(inv_lbl); inv_row.addWidget(self.inv_btn); inv_row.addStretch()
        left_col.addLayout(inv_row)
        left_col.addStretch()
        feel_outer.addLayout(left_col,stretch=2)

        # ── Right column: curve graph with preset buttons ────────────────
        curve_col=QVBoxLayout(); curve_col.setSpacing(4)
        curve_lbl=QLabel("THRUSTER FIRES / SEC  vs  STICK ANGLE")
        curve_lbl.setStyleSheet("font-size:12px;font-weight:bold;letter-spacing:2px")

        self._curve=KeypressCurveWidget()
        self._curve.set_params(self.cfg.get("speed",50),self.cfg.get("deadzone",5),self.cfg.get("pulse",30))
        init_pts = self.cfg.get("control_points", None)
        if init_pts:
            self._curve.set_control_points(init_pts)

        # Preset buttons
        preset_row=QHBoxLayout(); preset_row.setSpacing(6)
        preset_lbl=QLabel("CURVE:")
        preset_lbl.setStyleSheet("font-size:11px;font-weight:bold;")
        preset_row.addWidget(preset_lbl)
        for pname in KeypressCurveWidget.CURVE_PRESETS:
            pb=QPushButton(pname); pb.setFixedHeight(28); pb.setMinimumWidth(80)
            pb.setStyleSheet("font-size:11px;font-weight:bold;min-height:28px;padding:0 8px;border-radius:4px;")
            def _load(checked, n=pname):
                self._curve.load_preset(n)
                self.changed.emit()
            pb.clicked.connect(_load)
            preset_row.addWidget(pb)
        preset_row.addStretch()

        curve_col.addWidget(curve_lbl)
        curve_col.addLayout(preset_row)
        curve_col.addWidget(self._curve,stretch=1)
        feel_outer.addLayout(curve_col,stretch=3)
        outer.addLayout(feel_outer)

        # Wire signals
        for w in [self.key_left,self.key_right]:
            w.textChanged.connect(lambda _:self.changed.emit())
        self.dz_sl.valueChanged.connect(self._on_feel_changed)
        self.spd_sl.valueChanged.connect(self._on_feel_changed)
        self.pls_sl.valueChanged.connect(self._on_feel_changed)   # pulse also updates graph
        self.inv_btn.clicked.connect(lambda _:self.changed.emit())
        self._curve.curve_changed.connect(lambda _: self.changed.emit())

    def _on_feel_changed(self):
        pts = self._curve.get_control_points()
        self._curve.set_params(self.spd_sl.value(), self.dz_sl.value(), self.pls_sl.value())
        self._curve.set_control_points(pts)
        self.changed.emit()

    def _axis_text(self):
        ai=self.cfg.get("physical_axis",NO_AXIS)
        return "Not used" if ai==NO_AXIS else f"Axis {ai}  (on {self.device_label})"

    def _step_label(self,step,text):
        w=QWidget(); l=QHBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(10)
        s=QLabel(step); s.setStyleSheet("font-size:13px;font-weight:bold;background:#1a0840;border-radius:4px;padding:3px 8px;")
        t=QLabel(text); t.setStyleSheet("color:#7050a0;font-size:15px;")
        l.addWidget(s); l.addWidget(t); l.addStretch()
        return w

    def _hline(self):
        f=QFrame(); f.setFrameShape(QFrame.Shape.HLine); f.setStyleSheet("max-height:1px"); return f

    def _on_detect_click(self):
        self._detector.setVisible(not self._detector.isVisible())

    def _axis_picked(self,idx):
        self.cfg["physical_axis"]=idx
        self._axis_display.setText(self._axis_text())
        self._detector.setVisible(False)
        self.changed.emit()

    def _mark_unused(self):
        self.cfg["physical_axis"]=NO_AXIS
        self._axis_display.setText("Not used")
        self.changed.emit()

    def feed_detector(self,vals):
        if self._detector.isVisible(): self._detector.update_values(vals)

    def feed_live(self, raw_val, proc_val):
        self._curve.set_live(raw_val, proc_val)

    def get_config(self):
        return {
            "physical_axis": self.cfg.get("physical_axis",NO_AXIS),
            "key_left":  self.key_left.text().strip(),
            "key_right": self.key_right.text().strip(),
            "deadzone":  self.dz_sl.value(),
            "speed":     self.spd_sl.value(),
            "pulse":     self.pls_sl.value(),
            "inverted":  self.inv_btn.isChecked(),
            "control_points": self._curve.get_control_points(),
        }

    def apply_config(self,cfg):
        # Block all signals during load so intermediate states don't overwrite curve points
        for w in [self.dz_sl, self.spd_sl, self.pls_sl, self.inv_btn,
                  self.key_left, self.key_right]:
            w.blockSignals(True)

        self.cfg = dict(cfg)
        self._axis_display.setText(self._axis_text())
        self.key_left.setText(cfg.get("key_left",""))
        self.key_right.setText(cfg.get("key_right",""))
        self.dz_sl.setValue(cfg.get("deadzone",5))
        self.spd_sl.setValue(cfg.get("speed",50))
        self.pls_sl.setValue(cfg.get("pulse",30))
        self.inv_btn.setChecked(cfg.get("inverted",False))
        self.inv_btn.setText("INVERTED" if cfg.get("inverted",False) else "NORMAL")

        # Apply curve params and points after all sliders are set
        self._curve.set_params(cfg.get("speed",50), cfg.get("deadzone",5), cfg.get("pulse",30))
        pts = cfg.get("control_points", None)
        if pts:
            self._curve.set_control_points(pts)
        else:
            self._curve.reset_curve()

        for w in [self.dz_sl, self.spd_sl, self.pls_sl, self.inv_btn,
                  self.key_left, self.key_right]:
            w.blockSignals(False)

# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────
def hdivider():
    f=QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("max-height:1px;margin:8px 0"); return f

def section_heading(text):
    l=QLabel(text); l.setStyleSheet("font-size:18px;font-weight:bold;letter-spacing:6px;padding:14px 0 4px 2px")
    return l

def hint_footer(text):
    w=QLabel(text)
    w.setStyleSheet("font-size:13px;font-style:italic;padding:2px 4px 8px 4px")
    w.setWordWrap(True)
    return w

def gap(px=16):
    f=QFrame(); f.setFixedHeight(px); return f

# ─────────────────────────────────────────────────────────────
#  SIMPLE 3-COLOR THEME SYSTEM
#  Each theme has 4 preset swatches for: background, text, buttons
#  User can cycle each independently with toggle buttons
# ─────────────────────────────────────────────────────────────

THEME_PRESETS = {
    "Space": {
        "bg":   ["#100820", "#1a0e32", "#241644", "#0a0518"],
        "text": ["#e8e0ff", "#ffffff", "#c0b0ff", "#f0c030"],
        "btn":  ["#1e1040", "#2a1860", "#120828", "#302060"],
        "graph":[
            dict(bg=(6,4,14),    grid=(24,18,48),  curve0=(70,150,255),  curve1=(160,90,240), live=(50,200,120),  dz=(200,80,80),   maxspd=(60,160,60),  pulse=(240,192,48), handle=(120,70,200),  label=(80,60,140)),
            dict(bg=(4,8,4),     grid=(20,40,20),  curve0=(80,220,80),   curve1=(180,255,80), live=(255,220,50),  dz=(220,60,60),   maxspd=(100,255,100),pulse=(180,220,80), handle=(60,180,60),   label=(60,120,60)),
            dict(bg=(12,4,4),    grid=(40,18,18),  curve0=(255,100,80),  curve1=(255,180,60), live=(80,220,255),  dz=(80,200,80),   maxspd=(255,160,50), pulse=(255,100,80), handle=(220,80,60),   label=(140,60,60)),
            dict(bg=(2,8,16),    grid=(10,30,60),  curve0=(100,220,255), curve1=(80,160,255), live=(255,180,60),  dz=(220,80,80),   maxspd=(80,200,255), pulse=(80,160,255), handle=(60,160,220),  label=(60,100,160)),
        ],
    },
    "Midnight": {
        "bg":   ["#000000", "#0a0a0a", "#111111", "#050505"],
        "text": ["#ffffff", "#f0c030", "#e0e0e0", "#c0c0c0"],
        "btn":  ["#1a1a1a", "#252525", "#303030", "#0f0f0f"],
        "graph":[
            dict(bg=(0,0,0),     grid=(50,50,50),  curve0=(240,192,48),  curve1=(255,220,80), live=(80,200,80),   dz=(200,60,60),   maxspd=(80,200,80),  pulse=(240,192,48), handle=(200,160,40),  label=(140,140,140)),
            dict(bg=(0,0,0),     grid=(40,40,80),  curve0=(100,160,255), curve1=(160,120,255),live=(100,255,100), dz=(220,80,80),   maxspd=(120,200,80), pulse=(100,160,255),handle=(80,120,220),  label=(120,120,200)),
            dict(bg=(0,0,0),     grid=(80,40,40),  curve0=(255,80,80),   curve1=(255,160,80), live=(80,255,200),  dz=(80,200,80),   maxspd=(255,120,80), pulse=(255,80,80),  handle=(220,60,60),   label=(180,100,100)),
            dict(bg=(4,4,4),     grid=(60,60,60),  curve0=(200,200,200), curve1=(255,255,255),live=(180,255,100), dz=(255,100,100), maxspd=(200,255,200),pulse=(220,220,100),handle=(180,180,180), label=(160,160,160)),
        ],
    },
    "Rainbow": {
        "bg":   ["#0a0818","#140a24","#0a1420","#18080a","#0a1808","#141008","#08100a","#180a14","#100808","#080a18"],
        "text": ["#ffffff","#ff9090","#ffcc80","#ffff80","#90ff90","#80ffff","#90a0ff","#e080ff","#ff80c0","#c0c0c0"],
        "btn":  ["#400010","#403000","#004020","#003040","#200040","#400040","#402000","#004040","#300030","#003000"],
        "graph":[
            dict(bg=(6,4,14),    grid=(24,18,48),  curve0=(70,150,255),  curve1=(160,90,240), live=(50,200,120),  dz=(200,80,80),   maxspd=(60,160,60),  pulse=(240,192,48), handle=(120,70,200),  label=(80,60,140)),
            dict(bg=(4,8,4),     grid=(20,40,20),  curve0=(80,220,80),   curve1=(180,255,80), live=(255,220,50),  dz=(220,60,60),   maxspd=(100,255,100),pulse=(180,220,80), handle=(60,180,60),   label=(60,120,60)),
            dict(bg=(12,4,4),    grid=(40,18,18),  curve0=(255,100,80),  curve1=(255,180,60), live=(80,220,255),  dz=(80,200,80),   maxspd=(255,160,50), pulse=(255,100,80), handle=(220,80,60),   label=(140,60,60)),
            dict(bg=(2,8,16),    grid=(10,30,60),  curve0=(100,220,255), curve1=(80,160,255), live=(255,180,60),  dz=(220,80,80),   maxspd=(80,200,255), pulse=(80,160,255), handle=(60,160,220),  label=(60,100,160)),
            dict(bg=(8,0,8),     grid=(40,0,60),   curve0=(255,80,255),  curve1=(200,80,255), live=(80,255,200),  dz=(200,200,80),  maxspd=(200,80,255), pulse=(255,80,200), handle=(180,60,200),  label=(140,60,160)),
            dict(bg=(0,8,8),     grid=(0,40,50),   curve0=(80,255,220),  curve1=(80,200,255), live=(255,180,80),  dz=(200,80,80),   maxspd=(80,255,200), pulse=(80,220,220), handle=(60,200,180),  label=(60,140,140)),
            dict(bg=(12,8,0),    grid=(50,30,0),   curve0=(255,200,50),  curve1=(255,150,50), live=(80,200,255),  dz=(200,80,200),  maxspd=(255,180,50), pulse=(255,200,50), handle=(200,160,40),  label=(140,100,40)),
            dict(bg=(0,4,0),     grid=(0,40,20),   curve0=(80,255,80),   curve1=(180,255,80), live=(255,200,80),  dz=(255,80,80),   maxspd=(80,255,100), pulse=(80,220,80),  handle=(60,200,60),   label=(60,140,60)),
            dict(bg=(8,0,4),     grid=(40,0,20),   curve0=(255,60,100),  curve1=(255,100,160),live=(80,255,180),  dz=(80,200,80),   maxspd=(255,80,120), pulse=(255,60,100), handle=(200,40,80),   label=(160,60,80)),
            dict(bg=(4,4,0),     grid=(40,40,0),   curve0=(220,220,80),  curve1=(255,255,100),live=(80,200,255),  dz=(200,80,200),  maxspd=(200,220,80), pulse=(220,220,80), handle=(180,180,60),  label=(140,130,60)),
        ],
    },
    "Spring": {
        "bg":   ["#0d1a0d", "#162612", "#1e3318", "#0a120a"],
        "text": ["#c8f0a0", "#ffffff", "#90e060", "#f0e8a0"],
        "btn":  ["#1a3d10", "#254f18", "#0f2a08", "#2e5a1c"],
        "graph":[
            dict(bg=(10,24,8),   grid=(30,70,20),  curve0=(100,220,60),  curve1=(180,255,80), live=(255,220,50),  dz=(220,80,80),   maxspd=(80,200,60),  pulse=(200,255,80), handle=(80,180,40),   label=(60,140,30)),
            dict(bg=(8,20,14),   grid=(20,60,40),  curve0=(80,200,140),  curve1=(120,255,160),live=(255,200,60),  dz=(200,60,60),   maxspd=(60,200,120), pulse=(80,220,140), handle=(60,160,100),  label=(40,120,80)),
            dict(bg=(18,18,6),   grid=(60,60,20),  curve0=(220,220,80),  curve1=(255,255,100),live=(80,220,160),  dz=(200,80,200),  maxspd=(200,200,60), pulse=(220,220,80), handle=(180,180,40),  label=(140,130,40)),
            dict(bg=(12,8,18),   grid=(40,20,60),  curve0=(180,100,255), curve1=(220,160,255),live=(100,255,150), dz=(220,80,80),   maxspd=(120,80,220), pulse=(180,100,255),handle=(140,80,200),  label=(100,60,160)),
        ],
    },
    "Summer": {
        "bg":   ["#1a0e00", "#261500", "#331c00", "#120a00"],
        "text": ["#ffe0a0", "#ffffff", "#ffc040", "#80e8ff"],
        "btn":  ["#4a2800", "#5e3200", "#361e00", "#6a3c00"],
        "graph":[
            dict(bg=(24,14,0),   grid=(80,50,10),  curve0=(255,180,40),  curve1=(255,220,80), live=(80,220,255),  dz=(200,60,60),   maxspd=(255,160,40), pulse=(255,200,60), handle=(220,140,30),  label=(160,100,20)),
            dict(bg=(20,4,4),    grid=(70,20,20),  curve0=(255,80,60),   curve1=(255,140,80), live=(80,200,255),  dz=(80,200,80),   maxspd=(255,80,60),  pulse=(255,120,60), handle=(200,60,40),   label=(160,60,40)),
            dict(bg=(4,18,22),   grid=(20,60,80),  curve0=(80,200,255),  curve1=(120,220,255),live=(255,180,50),  dz=(200,80,80),   maxspd=(60,180,255), pulse=(80,210,255), handle=(50,160,210),  label=(40,120,160)),
            dict(bg=(22,16,0),   grid=(80,60,0),   curve0=(255,220,0),   curve1=(255,240,80), live=(80,255,180),  dz=(220,60,60),   maxspd=(220,200,0),  pulse=(255,220,40), handle=(200,180,0),   label=(160,140,0)),
        ],
    },
    "Autumn": {
        "bg":   ["#1a0800", "#261200", "#331800", "#120500"],
        "text": ["#ff9040", "#ffffff", "#ffc060", "#ffe0a0"],
        "btn":  ["#4a1800", "#6a2400", "#361000", "#5a1c00"],
        "graph":[
            dict(bg=(22,8,0),    grid=(80,30,0),   curve0=(255,100,20),  curve1=(255,160,40), live=(80,200,255),  dz=(180,180,40),  maxspd=(255,120,20), pulse=(255,140,40), handle=(220,80,10),   label=(160,60,10)),
            dict(bg=(18,12,0),   grid=(70,45,0),   curve0=(220,140,0),   curve1=(255,180,40), live=(80,220,180),  dz=(200,60,60),   maxspd=(200,140,0),  pulse=(220,160,30), handle=(180,110,0),   label=(140,90,0)),
            dict(bg=(14,6,8),    grid=(50,25,30),  curve0=(200,60,40),   curve1=(240,100,60), live=(80,200,255),  dz=(80,180,80),   maxspd=(200,80,40),  pulse=(220,80,60),  handle=(170,50,30),   label=(130,40,20)),
            dict(bg=(8,8,4),     grid=(40,40,15),  curve0=(180,180,60),  curve1=(220,200,80), live=(255,120,40),  dz=(200,60,60),   maxspd=(180,160,60), pulse=(200,190,70), handle=(150,140,40),  label=(120,110,30)),
        ],
    },
    "Winter": {
        "bg":   ["#040e18", "#081422", "#0c1a2c", "#020810"],
        "text": ["#c0e8ff", "#ffffff", "#80c8f0", "#e0f4ff"],
        "btn":  ["#0c2a44", "#10365a", "#081e34", "#143860"],
        "graph":[
            dict(bg=(4,12,22),   grid=(20,50,90),  curve0=(80,180,255),  curve1=(140,220,255),live=(200,240,255), dz=(200,80,80),   maxspd=(100,200,255),pulse=(80,180,255), handle=(60,150,220),  label=(50,110,180)),
            dict(bg=(8,8,16),    grid=(30,30,60),  curve0=(160,160,255), curve1=(200,200,255),live=(80,255,200),  dz=(220,80,80),   maxspd=(140,140,255),pulse=(160,160,255),handle=(120,120,220), label=(80,80,180)),
            dict(bg=(2,14,14),   grid=(10,50,50),  curve0=(80,220,220),  curve1=(120,255,240),live=(255,220,80),  dz=(200,80,80),   maxspd=(80,200,200), pulse=(80,220,220), handle=(60,180,180),  label=(40,140,140)),
            dict(bg=(14,10,20),  grid=(50,35,70),  curve0=(200,140,255), curve1=(220,180,255),live=(80,255,220),  dz=(220,80,80),   maxspd=(180,120,255),pulse=(200,140,255),handle=(160,100,220), label=(120,80,180)),
        ],
    },
    "Christmas": {
        "bg":   ["#0a0f00", "#0f1800", "#050a00", "#141e00"],
        "text": ["#e8f0d0", "#ffffff", "#c0e880", "#ff6060"],
        "btn":  ["#8b0000", "#a30000", "#660000", "#c00000"],
        "graph":[
            dict(bg=(10,4,4),    grid=(60,15,15),  curve0=(220,40,40),   curve1=(255,80,80),  live=(80,200,80),   dz=(80,180,80),   maxspd=(220,40,40),  pulse=(255,200,60), handle=(180,30,30),   label=(140,20,20)),
            dict(bg=(4,12,4),    grid=(15,60,15),  curve0=(60,180,60),   curve1=(80,220,80),  live=(255,60,60),   dz=(200,60,60),   maxspd=(60,200,60),  pulse=(80,220,80),  handle=(40,150,40),   label=(30,110,30)),
            dict(bg=(12,10,2),   grid=(60,50,10),  curve0=(255,215,0),   curve1=(255,235,80), live=(255,60,60),   dz=(200,60,60),   maxspd=(220,180,0),  pulse=(255,215,40), handle=(200,170,0),   label=(160,130,0)),
            dict(bg=(2,6,14),    grid=(10,25,60),  curve0=(150,200,255), curve1=(200,225,255),live=(255,60,60),   dz=(200,60,60),   maxspd=(120,180,255),pulse=(150,200,255),handle=(100,160,220), label=(70,120,180)),
        ],
    },
    "Halloween": {
        "bg":   ["#0e0500", "#160800", "#0a0300", "#1c0a00"],
        "text": ["#ff8c00", "#ffffff", "#ff6000", "#c890ff"],
        "btn":  ["#3d1a00", "#521f00", "#2a1200", "#6b2d00"],
        "graph":[
            dict(bg=(16,6,0),    grid=(80,30,0),   curve0=(255,100,0),   curve1=(255,140,30), live=(180,80,255),  dz=(80,180,80),   maxspd=(255,100,0),  pulse=(255,130,20), handle=(220,80,0),    label=(160,60,0)),
            dict(bg=(6,0,10),    grid=(30,0,50),   curve0=(160,0,220),   curve1=(200,80,255), live=(255,120,0),   dz=(80,180,80),   maxspd=(140,0,200),  pulse=(160,0,220),  handle=(120,0,180),   label=(90,0,140)),
            dict(bg=(4,8,4),     grid=(20,40,20),  curve0=(80,200,80),   curve1=(120,240,80), live=(255,100,0),   dz=(200,80,200),  maxspd=(80,180,80),  pulse=(100,220,80), handle=(60,160,60),   label=(40,120,40)),
            dict(bg=(14,12,0),   grid=(70,60,0),   curve0=(220,200,0),   curve1=(255,230,40), live=(180,80,255),  dz=(200,80,200),  maxspd=(200,180,0),  pulse=(220,200,20), handle=(180,160,0),   label=(140,120,0)),
        ],
    },
}

# Current swatch indices [bg_idx, text_idx, btn_idx, graph_idx] per theme
THEME_SWATCH = {t: [0, 0, 0, 0] for t in THEME_PRESETS}

CURRENT_THEME = "Space"

# Per-theme graph colors updated at runtime by _apply_theme
GRAPH_COLORS = {
    "Space":    dict(bg=QColor(6,4,14),    grid=QColor(24,18,48),   dim=QColor(60,45,120),
                     curve0=QColor(70,150,255),  curve1=QColor(160,90,240),
                     ghost=QColor(80,80,140,60),  handle=QColor(120,70,200),
                     handle_h=QColor(160,100,220),handle_d=QColor(200,130,255),
                     live=QColor(50,200,120),      dz=QColor(200,80,80,140),
                     maxspd=QColor(60,160,60,80), pulse=QColor(240,192,48,80),
                     border=QColor(30,20,70),      label=QColor(60,45,120)),
    "Midnight": dict(bg=QColor(0,0,0),      grid=QColor(50,50,50),   dim=QColor(140,140,140),
                     curve0=QColor(240,192,48),    curve1=QColor(255,220,100),
                     ghost=QColor(100,100,100,80), handle=QColor(200,160,40),
                     handle_h=QColor(240,200,60),  handle_d=QColor(255,230,80),
                     live=QColor(80,200,80),        dz=QColor(200,60,60,160),
                     maxspd=QColor(80,200,80,120),  pulse=QColor(240,192,48,120),
                     border=QColor(60,60,60),       label=QColor(140,140,140)),
}
_GC = GRAPH_COLORS["Space"]  # active graph colors, updated by _apply_theme

def tc(dark_color, light_color="#000000"):
    """Return light_color (default black) on light themes, dark_color on dark themes."""
    if CURRENT_THEME in ("Xbox", "Pink"):
        return light_color
    return dark_color


# ─────────────────────────────────────────────────────────────
#  STYLESHEET GENERATOR
# ─────────────────────────────────────────────────────────────
def build_stylesheet(theme=None, swatches=None):
    """Build a complete stylesheet from 3 colors: bg, text, btn."""
    t  = theme    or CURRENT_THEME
    sw = swatches or THEME_SWATCH[t]
    p  = THEME_PRESETS[t]
    bg   = p["bg"]  [sw[0]]
    text = p["text"][sw[1]]
    btn  = p["btn"] [sw[2]]

    # Derive supporting colors from the 3 base colors
    card_bg      = _lighten(bg, 0.08)
    border       = _lighten(bg, 0.25)
    input_bg     = _darken(bg, 0.1)
    groupbox_bg  = "rgba(255,255,255,5)"
    scroll_bg    = _lighten(bg, 0.05)
    accent_line  = btn
    groove       = _darken(bg, 0.3)

    btn_hover   = _lighten(btn, 0.2)
    btn_border  = _lighten(btn, 0.3)

    m = "Courier New"
    return f"""
QMainWindow,QWidget{{background:{bg};color:{text};font-family:'{m}',monospace;font-size:15px;}}
QWidget#header_bar{{background:{bg};}}
QScrollArea{{border:none;background:transparent;}}
QScrollBar:vertical{{background:#08031a;width:18px;border:none;border-radius:9px;}}
QScrollBar::handle:vertical{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #f0c030,stop:1 #b08010);border-radius:7px;min-height:36px;margin:3px;}}
QScrollBar::handle:vertical:hover{{background:#ffe060;}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
QScrollBar:horizontal{{background:#08031a;height:18px;border:none;border-radius:9px;}}
QScrollBar::handle:horizontal{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #f0c030,stop:1 #b08010);border-radius:7px;min-width:36px;margin:3px;}}
QScrollBar::handle:horizontal:hover{{background:#ffe060;}}
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;}}
QGroupBox{{border:1px solid {border};border-radius:10px;margin-top:18px;padding:20px 16px 16px 16px;background:{groupbox_bg};}}
QGroupBox::title{{subcontrol-origin:margin;left:16px;padding:0 8px;color:{text};font-size:16px;letter-spacing:3px;font-weight:bold;}}
QSlider::groove:horizontal{{height:6px;background:{groove};border-radius:3px;}}
QSlider::handle:horizontal{{background:{btn};width:20px;height:20px;margin:-7px 0;border-radius:10px;border:2px solid {btn_hover};}}
QSlider::handle:horizontal:hover{{background:{btn_hover};}}
QSlider::sub-page:horizontal{{background:{btn};border-radius:3px;}}
QLabel{{color:{text};font-size:15px;}}
QGroupBox{{border:1px solid {border};border-radius:10px;margin-top:18px;padding:20px 16px 16px 16px;background:{groupbox_bg};}}
QGroupBox::title{{subcontrol-origin:margin;left:16px;padding:0 8px;color:{text};font-size:16px;letter-spacing:3px;font-weight:bold;}}
QPushButton{{background:{btn};border:1px solid {btn_border};border-radius:6px;padding:6px 16px;color:{text};font-family:'{m}';font-size:15px;font-weight:bold;min-height:40px;}}
QPushButton:hover{{background:{btn_hover};border-color:{text};color:{text};}}
QPushButton:checked{{background:{btn_hover};border-color:{text};color:{text};}}
QPushButton#run_btn{{font-size:22px;font-weight:bold;padding:6px 32px;letter-spacing:4px;}}
QPushButton#run_btn[active="false"]{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 rgba(40,200,80,180),stop:1 rgba(10,80,20,200));border:2px solid #30e060;border-top:2px solid #30e060;color:#ffffff;}}
QPushButton#run_btn[active="false"]:hover{{background:rgba(60,220,100,200);border-color:#80ffaa;}}
QPushButton#run_btn[active="true"]{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 rgba(220,50,50,180),stop:1 rgba(100,10,10,200));border:2px solid #e03030;border-top:2px solid #e03030;color:#ffffff;}}
QPushButton#run_btn[active="true"]:hover{{background:rgba(255,80,80,200);border-color:#ff8080;}}
QComboBox{{background:{input_bg};border:1px solid {border};border-radius:6px;padding:6px 12px;color:{text};font-family:'{m}';font-size:15px;min-height:42px;}}
QComboBox:hover{{border-color:{btn_hover};}}
QComboBox::drop-down{{border:none;width:22px;}}
QComboBox QAbstractItemView{{background:{input_bg};color:{text};selection-background-color:{btn};font-size:15px;border:1px solid {border};}}
QLineEdit{{background:{input_bg};border:1px solid {border};border-radius:6px;padding:6px 10px;color:{text};font-family:'{m}';font-size:15px;font-weight:bold;min-height:42px;}}
QLineEdit:focus{{border-color:{btn_hover};}}
QFrame[frameShape="4"],QFrame[frameShape="5"]{{color:{border};max-height:1px;}}
QToolTip{{background:{input_bg};color:{text};border:1px solid {btn};font-size:14px;padding:8px;}}
"""

def _hex_to_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)

def _rgb_to_hex(r,g,b):
    return f"#{max(0,min(255,int(r))):02x}{max(0,min(255,int(g))):02x}{max(0,min(255,int(b))):02x}"

def _lighten(h, amt):
    try:
        r,g,b = _hex_to_rgb(h)
        return _rgb_to_hex(r+amt*255, g+amt*255, b+amt*255)
    except: return h

def _darken(h, amt):
    try:
        r,g,b = _hex_to_rgb(h)
        return _rgb_to_hex(r-amt*255, g-amt*255, b-amt*255)
    except: return h

def _blend(h1, h2, t):
    try:
        r1,g1,b1 = _hex_to_rgb(h1); r2,g2,b2 = _hex_to_rgb(h2)
        return _rgb_to_hex(r1+t*(r2-r1), g1+t*(g2-g1), b1+t*(b2-b1))
    except: return h1

STYLE = build_stylesheet()


# ─────────────────────────────────────────────────────────────
#  TUTORIAL WIZARD
# ─────────────────────────────────────────────────────────────
class TutorialWizard(QDialog):
    """
    Step-by-step interactive tutorial for first-time users.
    Can be launched from the welcome dialog or the TUTORIAL button.
    """
    STEPS = [
        {
            "title": "WELCOME  TO  STARBASE  HOTAS  BRIDGE",
            "icon":  "🚀",
            "body": (
                "This app connects your flight sticks to Starbase by converting "
                "analog stick movements into timed keyboard presses.\n\n"
                "It takes about 5 minutes to set up. This tutorial walks you "
                "through every step.\n\n"
                "You can close this at any time and reopen it with the "
                "TUTORIAL button in the top bar."
            ),
            "hint": None,
        },
        {
            "title": "STEP 0  —  CONNECT  YOUR  DEVICES",
            "icon":  "🎮",
            "body": (
                "Plug in all your HOTAS devices before starting.\n\n"
                "The app needs to know which physical device is which:\n\n"
                "  •  RIGHT STICK  →  Pitch / Roll\n"
                "  •  LEFT STICK / THROTTLE  →  Thrust + Strafe U/D\n"
                "  •  RUDDER PEDALS  →  Strafe L/R\n\n"
                "Use the device dropdowns in STEP 0 to assign them, "
                "then click SCAN FOR DEVICES if your sticks don't appear."
            ),
            "hint": "💡  VKB users: your devices load automatically with the VKB Default profile.",
        },
        {
            "title": "STEP 1  —  ASSIGN  AXES",
            "icon":  "📡",
            "body": (
                "Each movement (Yaw, Pitch, Roll, etc.) needs to know "
                "which physical axis on your stick controls it.\n\n"
                "To assign an axis:\n\n"
                "  1.  Open a movement card (e.g. PITCH)\n"
                "  2.  Click the DETECT button\n"
                "  3.  Move the physical axis on your stick\n"
                "  4.  The bar that lights up is your axis — click it\n"
                "  5.  The axis is now assigned\n\n"
                "If a movement has no axis (e.g. you don't have pedals), "
                "click NOT USED to disable it."
            ),
            "hint": "💡  VKB users: axes are pre-assigned in the VKB Default profile.",
        },
        {
            "title": "STEP 2  —  SET  KEYBOARD  KEYS",
            "icon":  "⌨️",
            "body": (
                "Each movement needs two keys — one for each direction.\n\n"
                "To set a key:\n\n"
                "  1.  Click the key field (e.g. ← TURN LEFT)\n"
                "  2.  Press the key on your keyboard\n"
                "  3.  The key name appears automatically\n\n"
                "Default Starbase bindings are pre-loaded:\n\n"
                "  Yaw       →  Q / E\n"
                "  Pitch     →  W / S\n"
                "  Roll      →  A / D\n"
                "  Thrust    →  Shift / Ctrl\n"
                "  Strafe    →  Arrow keys\n\n"
                "Change any key by clicking the field and pressing a new key."
            ),
            "hint": "💡  Special keys work too: Shift, Ctrl, Alt, F1–F12, arrows.",
        },
        {
            "title": "STEP 3  —  TUNE  THE  FEEL",
            "icon":  "📈",
            "body": (
                "Three sliders control how each movement feels:\n\n"
                "  DEAD ZONE\n"
                "  How far you move before it responds.\n"
                "  Increase if the axis drifts on its own.\n\n"
                "  MAXIMUM SPEED\n"
                "  How fast the ship moves at full deflection.\n"
                "  Lower = gentler. Higher = more aggressive.\n\n"
                "  PULSE LENGTH\n"
                "  Minimum key hold time per cycle.\n"
                "  Low = light taps. High = heavy committed holds.\n\n"
                "The CURVE GRAPH shows keypresses/sec vs stick angle. "
                "Drag the 7 handles to reshape the response."
            ),
            "hint": "💡  Double-click the graph to reset the curve to the default shape.",
        },
        {
            "title": "THE  KEY  OUTPUT  TEST",
            "icon":  "📊",
            "body": (
                "The KEY OUTPUT TEST strip at the bottom of the page "
                "shows a live stream of every key press the app sends to the game.\n\n"
                "To use it:\n\n"
                "  1.  Click START (green button, top right)\n"
                "  2.  Move your sticks\n"
                "  3.  Watch the blocks scroll left — each block is one key press\n\n"
                "Faster blocks = more key presses per second = faster ship movement.\n\n"
                "Use this to verify your setup is working before launching Starbase. "
                "If you move a stick and see blocks appear, the app is working."
            ),
            "hint": "💡  Click CLEAR to wipe the test strip and start fresh.",
        },
        {
            "title": "SAVING  YOUR  SETUP",
            "icon":  "💾",
            "body": (
                "Your settings autosave continuously — you don't need to "
                "manually save for them to persist between sessions.\n\n"
                "To create named profiles (for different ships or playstyles):\n\n"
                "  SAVE     →  Save to current profile name\n"
                "             (asks before overwriting)\n\n"
                "  SAVE AS  →  Save with a new name\n\n"
                "  LOAD     →  Switch to a different profile\n\n"
                "  NEW      →  Create a blank or VKB-defaults profile\n\n"
                f"All profiles are saved to:\n"
                f"  Documents\\StarbaseHOTAS\\"
            ),
            "hint": "💡  The app reopens in exactly the state you left it.",
        },
        {
            "title": "READY  TO  FLY",
            "icon":  "✅",
            "body": (
                "You're all set. Here's the quick launch checklist:\n\n"
                "  ☐  Plug in your HOTAS devices\n"
                "  ☐  Launch Starbase HOTAS Bridge\n"
                "  ☐  Click START  (green button)\n"
                "  ☐  Launch Starbase\n"
                "  ☐  Fly\n\n"
                "The app must be running in the background while you play. "
                "It sends keypresses directly to whatever window is active, "
                "so Starbase just sees keyboard input.\n\n"
                "Come back and adjust curves anytime — changes apply live "
                "without restarting."
            ),
            "hint": "💡  Alt+Tab back to this app to tweak settings mid-flight.",
        },
    ]

    def __init__(self, parent=None, start_step=0):
        super().__init__(parent)
        self.setWindowTitle("Starbase HOTAS Bridge — Tutorial")
        self.setMinimumSize(640, 520)
        self.setMaximumSize(700, 580)
        self.setStyleSheet(
            "QDialog { background: #0c0820; color: #e8e0ff; font-family: Courier New; }"
            "QLabel  { color: #e8e0ff; }"
            "QPushButton { background: #1e1040; border: 1px solid #6040a0; border-radius: 6px;"
            "              color: #e8e0ff; font-family: Courier New; font-size: 14px;"
            "              font-weight: bold; min-height: 40px; padding: 6px 20px; }"
            "QPushButton:hover { background: #2a1860; border-color: #f0c030; color: #f0c030; }"
            "QPushButton#next_btn { background: #1a3a10; border: 2px solid #40c040; color: #ffffff; font-size: 16px; }"
            "QPushButton#next_btn:hover { background: #254f15; border-color: #60e060; }"
            "QPushButton#done_btn { background: #1a3a10; border: 2px solid #40c040; color: #ffffff; font-size: 16px; }"
            "QPushButton#done_btn:hover { background: #254f15; border-color: #60e060; }"
        )
        self._step = start_step
        self._build()
        self._update_step()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(0)

        # Progress dots
        self._dot_row = QHBoxLayout()
        self._dot_row.setSpacing(8)
        self._dots = []
        for i in range(len(self.STEPS)):
            dot = QLabel("●")
            dot.setFixedWidth(22)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._dots.append(dot)
            self._dot_row.addWidget(dot)
        self._dot_row.addStretch()
        layout.addLayout(self._dot_row)
        layout.addSpacing(16)

        # Icon
        self._icon_lbl = QLabel()
        self._icon_lbl.setStyleSheet("font-size:40px;")
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_lbl)
        layout.addSpacing(10)

        # Title
        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(
            "color:#f0c030;font-size:17px;font-weight:bold;letter-spacing:2px;")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setWordWrap(True)
        layout.addWidget(self._title_lbl)
        layout.addSpacing(16)

        # Body
        self._body_lbl = QLabel()
        self._body_lbl.setStyleSheet("font-size:15px;line-height:160%")
        self._body_lbl.setWordWrap(True)
        self._body_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._body_lbl.setMinimumHeight(200)
        layout.addWidget(self._body_lbl, stretch=1)
        layout.addSpacing(12)

        # Hint
        self._hint_lbl = QLabel()
        self._hint_lbl.setStyleSheet(
            "color:#80c0ff;font-size:14px;font-style:italic;"
            "background:rgba(40,80,160,40);border-radius:6px;padding:8px 12px;")
        self._hint_lbl.setWordWrap(True)
        self._hint_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._hint_lbl)
        layout.addSpacing(20)

        # Navigation buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        self._prev_btn = QPushButton("← BACK")
        self._prev_btn.setFixedHeight(44)
        self._prev_btn.clicked.connect(self._prev)
        btn_row.addWidget(self._prev_btn)

        btn_row.addStretch()

        # Step counter
        self._step_lbl = QLabel()
        self._step_lbl.setStyleSheet("font-size:13px")
        self._step_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.addWidget(self._step_lbl)

        btn_row.addStretch()

        self._next_btn = QPushButton("NEXT →")
        self._next_btn.setObjectName("next_btn")
        self._next_btn.setFixedHeight(44); self._next_btn.setMinimumWidth(140)
        self._next_btn.clicked.connect(self._next)

        self._done_btn = QPushButton("LET'S FLY  🚀")
        self._done_btn.setObjectName("done_btn")
        self._done_btn.setFixedHeight(44); self._done_btn.setMinimumWidth(180)
        self._done_btn.clicked.connect(self.accept)

        btn_row.addWidget(self._next_btn)
        btn_row.addWidget(self._done_btn)
        layout.addLayout(btn_row)

    def _update_step(self):
        s = self.STEPS[self._step]
        n = len(self.STEPS)
        last = self._step == n - 1

        self._icon_lbl.setText(s["icon"])
        self._title_lbl.setText(s["title"])
        self._body_lbl.setText(s["body"])

        if s["hint"]:
            self._hint_lbl.setText(s["hint"])
            self._hint_lbl.setVisible(True)
        else:
            self._hint_lbl.setVisible(False)

        self._step_lbl.setText(f"{self._step + 1}  /  {n}")
        self._prev_btn.setVisible(self._step > 0)
        self._next_btn.setVisible(not last)
        self._done_btn.setVisible(last)

        # Update progress dots
        for i, dot in enumerate(self._dots):
            if i < self._step:
                dot.setStyleSheet("color:#40c040;font-size:14px;")   # done
            elif i == self._step:
                dot.setStyleSheet("color:#f0c030;font-size:18px;")   # current
            else:
                dot.setStyleSheet("color:#302050;font-size:14px;")   # future

    def _next(self):
        if self._step < len(self.STEPS) - 1:
            self._step += 1
            self._update_step()

    def _prev(self):
        if self._step > 0:
            self._step -= 1
            self._update_step()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Right: self._next()
        elif e.key() == Qt.Key.Key_Left: self._prev()
        elif e.key() == Qt.Key.Key_Return and self._step == len(self.STEPS)-1: self.accept()
        else: super().keyPressEvent(e)


# ─────────────────────────────────────────────────────────────
#  COLLAPSIBLE SECTION
# ─────────────────────────────────────────────────────────────
class CollapsibleSection(QWidget):
    """A clearly-outlined clickable header that shows/hides its content widget."""
    def __init__(self, title, content_widget, expanded=True):
        super().__init__()
        self._expanded = expanded
        self._content  = content_widget
        self._title    = title
        lay = QVBoxLayout(self); lay.setSpacing(0); lay.setContentsMargins(0,4,0,4)

        # Outer container with visible border so it reads as a collapsible unit
        outer = QWidget()
        outer.setStyleSheet(
            "QWidget#collapseOuter{"
            "border:2px solid rgba(180,160,255,90);"
            "border-radius:8px;"
            "background:rgba(255,255,255,3);}")
        outer.setObjectName("collapseOuter")
        outer_lay = QVBoxLayout(outer); outer_lay.setSpacing(0); outer_lay.setContentsMargins(0,0,0,0)

        self._header = QPushButton()
        self._header.setCheckable(True); self._header.setChecked(expanded)
        self._header.setFixedHeight(44)
        self._header.setStyleSheet(
            "QPushButton{"
            "text-align:left;padding:0 18px;"
            "font-size:16px;font-weight:bold;letter-spacing:4px;"
            "border:none;border-radius:6px 6px 0 0;"
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 rgba(180,160,255,35),stop:1 rgba(120,100,200,20));}"
            "QPushButton:hover{"
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 rgba(240,192,48,50),stop:1 rgba(180,140,30,25));}"
            "QPushButton:!checked{"
            "border-radius:6px;"
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 rgba(180,160,255,20),stop:1 rgba(100,80,160,10));}")
        self._set_header(title, expanded)
        self._header.clicked.connect(self._toggle)

        # Divider line between header and content
        self._divider = QFrame()
        self._divider.setFrameShape(QFrame.Shape.HLine)
        self._divider.setStyleSheet("color:rgba(180,160,255,40);max-height:1px;margin:0;")
        self._divider.setVisible(expanded)

        outer_lay.addWidget(self._header)
        outer_lay.addWidget(self._divider)
        outer_lay.addWidget(content_widget)
        content_widget.setVisible(expanded)

        lay.addWidget(outer)

    def _set_header(self, title, expanded):
        arrow = "  ▼  " if expanded else "  ▶  "
        self._header.setText(f"{arrow}{title}")

    def _toggle(self, checked):
        self._expanded = checked
        self._content.setVisible(checked)
        self._divider.setVisible(checked)
        self._set_header(self._title, checked)
        self._header.setChecked(checked)


# ─────────────────────────────────────────────────────────────
#  SPACE BACKGROUND  — star sparkle + subtle texture for Space theme
# ─────────────────────────────────────────────────────────────
import random as _random

class SpaceBgWidget(QWidget):
    """Page background with procedural star sparkle when Space theme is active."""
    def __init__(self):
        super().__init__()
        # Generate fixed star positions once
        _rng = _random.Random(42)
        self._stars = [(int(_rng.random()*3840), int(_rng.random()*4000),
                        _rng.random()) for _ in range(320)]
        self._dots  = [(int(_rng.random()*3840), int(_rng.random()*4000))
                       for _ in range(600)]

    def paintEvent(self, e):
        super().paintEvent(e)
        if CURRENT_THEME != "Space": return
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Carbon-fiber micro grid (very subtle)
        p.setPen(QPen(QColor(255,255,255,5), 1))
        step = 18
        for x in range(0, w, step):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            p.drawLine(0, y, w, y)

        # Star sparkles
        for sx, sy, brightness in self._stars:
            if sx > w or sy > h: continue
            alpha = int(60 + brightness * 160)
            size  = 1.0 + brightness * 1.8
            c = QColor(255, 255, 255, alpha)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(c))
            p.drawEllipse(int(sx - size/2), int(sy - size/2), int(size), int(size))
            # Cross sparkle on brighter stars
            if brightness > 0.7:
                p.setPen(QPen(QColor(255,255,255,alpha//3), 1))
                r = int(size * 2.5)
                p.drawLine(sx-r, sy, sx+r, sy)
                p.drawLine(sx, sy-r, sx, sy+r)

        # Subtle dot-matrix texture
        p.setPen(QPen(QColor(255,255,255,6), 1))
        for dx, dy in self._dots:
            if dx > w or dy > h: continue
            p.drawPoint(dx, dy)

        p.end()


# ─────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STARBASE HOTAS BRIDGE")
        self.setFixedWidth(WIN_W)
        self.setMinimumHeight(600)
        self.resize(WIN_W, WIN_H)
        self._first_launch     = False  # must be initialised BEFORE _load_startup_profile
        self._startup_theme    = None   # restored from session if available
        self._startup_swatches = None
        self._reader = JoystickReader()
        self._worker = None
        self._cards  = {}
        self._live_bars = {}
        self._key_test = None
        self._key_queue = []
        self._turtle_mode = False     # is turtle mode active?
        self._base_movements = None   # normal movements saved while turtle is on
        self.profile = self._load_startup_profile()  # may set _first_launch = True
        self._fc=0; self._ft=time.perf_counter()
        self._build_ui()
        # Restore theme and swatches from last session
        if self._startup_theme:
            global CURRENT_THEME
            CURRENT_THEME = self._startup_theme
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentText(self._startup_theme)
            self.theme_combo.blockSignals(False)
        if self._startup_swatches:
            for t, sw in self._startup_swatches.items():
                if t in THEME_SWATCH:
                    # Pad to 4 elements if loaded from older session (only had 3)
                    padded = list(sw) + [0] * (4 - len(sw))
                    THEME_SWATCH[t] = padded[:4]
        self._theme_container.setStyleSheet(build_stylesheet())
        _bg = THEME_PRESETS[CURRENT_THEME]["bg"][THEME_SWATCH[CURRENT_THEME][0]]
        self.setStyleSheet(f"QMainWindow{{background:{_bg}}}")
        try:
            _r=int(_bg[1:3],16);_g=int(_bg[3:5],16);_b=int(_bg[5:7],16)
            _hr,_hg,_hb=max(0,int(_r*.70)),max(0,int(_g*.70)),max(0,int(_b*.70))
            _br,_bg2,_bb=min(255,int(_r*1.3)),min(255,int(_g*1.3)),min(255,int(_b*1.3))
            _hcss=(f"background:#{_hr:02x}{_hg:02x}{_hb:02x};"
                   f"border-bottom:1px solid #{_br:02x}{_bg2:02x}{_bb:02x};")
        except: _hcss="background:#0a0520;border-bottom:1px solid #2a1060;"
        if hasattr(self, "_title_strip") and hasattr(self, "_prof_bar"):
            self._update_header_color(_bg)
        self._refresh_swatch_buttons()
        self._refresh_profiles()
        # Init turtle toggle list before banners are visible
        if not hasattr(self, "_turtle_toggles"):
            self._turtle_toggles = []
        self._select_profile_in_bar(self.profile.get("name",""))
        self._poll_timer=QTimer()
        self._poll_timer.setInterval(16)
        self._poll_timer.timeout.connect(self._poll)
        QTimer.singleShot(300,self._initial_scan)
        QTimer.singleShot(600,self._maybe_show_welcome)

    def _load_startup_profile(self):
        # On first launch as .exe, copy bundled profiles to user data dir
        if getattr(_sys, 'frozen', False):
            import shutil
            bundled = Path(_sys._MEIPASS) / "hotas_profiles"
            if bundled.exists():
                for f in bundled.glob("*.json"):
                    dest = PROFILES_DIR / f.name
                    if not dest.exists():
                        shutil.copy2(f, dest)
        # Try autosave session state first — restores exact last state
        profile, theme, swatches = load_session_state()
        if profile is not None:
            self._startup_theme   = theme
            self._startup_swatches = swatches
            return profile
        # Fall back to last named profile
        last = get_last_profile_name()
        if last:
            try: return migrate(load_profile(last))
            except: pass
        # Fall back to first profile found
        profiles = list_profiles()
        if profiles:
            try: return migrate(load_profile(profiles[0]))
            except: pass
        # No profiles at all — first launch.
        self._first_launch = True
        return copy.deepcopy(BLANK_PROFILE)

    def _build_ui(self):
        # Main window layout: profile bar at top, scroll area below
        central=QWidget(); self.setCentralWidget(central)
        central.setStyleSheet("background:transparent;")
        main_layout=QVBoxLayout(central); main_layout.setSpacing(0); main_layout.setContentsMargins(0,0,0,0)

        # ═══ TITLE STRIP (top, separate from controls) ════════
        title_strip=QWidget()
        title_strip.setFixedHeight(52)
        title_strip.setObjectName("header_bar")
        self._title_strip = title_strip
        tsl=QHBoxLayout(title_strip); tsl.setContentsMargins(20,6,20,6); tsl.setSpacing(10)

        title_lbl=QLabel("STARBASE  HOTAS  BRIDGE")
        title_lbl.setStyleSheet("color:#ffffff;font-size:18px;font-weight:bold;letter-spacing:6px;")
        tsl.addWidget(title_lbl)
        tsl.addSpacing(20)

        # Theme selector
        theme_lbl=QLabel("THEME:")
        theme_lbl.setStyleSheet("font-size:12px;font-weight:bold;letter-spacing:2px")
        tsl.addWidget(theme_lbl)
        self.theme_combo=NoScrollCombo(); self.theme_combo.setFixedHeight(30); self.theme_combo.setMinimumWidth(120)
        self.theme_combo.setStyleSheet("font-size:13px;min-height:30px;")
        for t in THEME_PRESETS: self.theme_combo.addItem(t)
        self.theme_combo.setCurrentText(CURRENT_THEME)
        self.theme_combo.currentTextChanged.connect(self._apply_theme)
        tsl.addWidget(self.theme_combo)

        tsl.addSpacing(16)

        # 4 swatch toggle buttons: BG, TEXT, BTN, GRAPH
        self._swatch_btns = []
        swatch_defs = [
            ("BG",    "Cycle background color through preset shades"),
            ("TEXT",  "Cycle text color through preset shades"),
            ("BTN",   "Cycle button color through preset shades"),
            ("GRAPH", "Cycle graph color scheme through preset palettes"),
        ]
        for i, (label, tip) in enumerate(swatch_defs):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:11px;font-weight:bold")
            tsl.addWidget(lbl)
            btn = QPushButton("●")
            btn.setFixedHeight(30); btn.setFixedWidth(70)
            btn.setToolTip(tip)
            idx_capture = i
            btn.clicked.connect(lambda _, i=idx_capture: self._cycle_swatch(i))
            self._swatch_btns.append(btn)
            tsl.addWidget(btn)

        tsl.addStretch()
        self.help_btn = QPushButton("? INSTRUCTIONS")
        self.help_btn.setCheckable(True)
        self.help_btn.setFixedHeight(30)
        self.help_btn.setStyleSheet(
            "QPushButton{font-size:13px;font-weight:bold;padding:0 14px;"
            "background:#ffffff;border:2px solid #ffffff;"
            "border-radius:4px;color:#000000;}"
            "QPushButton:checked{background:#f0c030;border-color:#f0c030;color:#000000;}"
            "QPushButton:hover{background:#f0c030;border-color:#f0c030;color:#000000;}")
        self.help_btn.clicked.connect(self._toggle_help)
        tsl.addWidget(self.help_btn)
        tsl.addSpacing(12)
        self.poll_lbl=QLabel("")
        self.poll_lbl.setStyleSheet("font-size:12px")
        tsl.addWidget(self.poll_lbl)
        main_layout.addWidget(title_strip)

        # ═══ INSTRUCTIONS PANEL (collapsible) ══════════════════
        self._help_panel = self._build_help_panel()
        self._help_panel.setVisible(False)
        main_layout.addWidget(self._help_panel)

        # ═══ PROFILE / CONTROL BAR ═════════════════════════════
        prof_bar=QWidget()
        prof_bar.setObjectName("header_bar")
        self._prof_bar = prof_bar
        prof_bar.setFixedHeight(80)
        pbl=QHBoxLayout(prof_bar); pbl.setContentsMargins(16,12,20,12); pbl.setSpacing(6)

        def bar_col(label_text, widget, min_w=None):
            col=QVBoxLayout(); col.setSpacing(2)
            lbl=QLabel(label_text)
            lbl.setStyleSheet("color:#f0c030;font-size:10px;font-weight:bold;letter-spacing:3px;")
            col.addWidget(lbl)
            if min_w: widget.setMinimumWidth(min_w)
            col.addWidget(widget)
            return col

        self.profile_combo=NoScrollCombo()
        self.profile_combo.setFixedHeight(40)
        self.profile_combo.setStyleSheet("font-size:17px;font-weight:bold")
        pbl.addLayout(bar_col("PROFILE", self.profile_combo, 150))
        pbl.addSpacing(4)

        for txt,slot,tip in [
            ("SAVE",   self._save_profile,  "Save (asks before overwriting)"),
            ("SAVE AS",self._save_as,       "Save with a new name"),
            ("LOAD",   self._load_sel,      "Load selected profile"),
            ("NEW",    self._new_prof,      "Create blank profile"),
            ("DELETE", self._del_prof,      "Delete selected profile"),
        ]:
            btn=QPushButton(txt); btn.setFixedHeight(40); btn.setMinimumWidth(78)
            btn.setToolTip(tip); btn.clicked.connect(slot)
            pbl.addWidget(btn)
            pbl.addSpacing(2)

        pbl.addStretch()

        self.status_lbl=QLabel("NOT RUNNING")
        self.status_lbl.setStyleSheet("color:#ff6060;font-size:18px;letter-spacing:3px;font-weight:bold;min-width:180px;")
        pbl.addLayout(bar_col("STATUS", self.status_lbl))
        pbl.addSpacing(16)

        # Run button sits directly in the bar layout — bar margins provide all-side padding
        self.run_btn=QPushButton("START"); self.run_btn.setObjectName("run_btn")
        self.run_btn.setFixedHeight(56); self.run_btn.setFixedWidth(220)
        self.run_btn.setProperty("active","false"); self.run_btn.clicked.connect(self._toggle)
        pbl.addWidget(self.run_btn)
        pbl.addSpacing(10)
        self.turtle_btn=QPushButton("🐢 NORMAL")
        self.turtle_btn.setCheckable(True)
        self.turtle_btn.setFixedHeight(56); self.turtle_btn.setMinimumWidth(140)
        self.turtle_btn.setStyleSheet(
            "QPushButton{font-size:15px;font-weight:bold;padding:0 12px;border-radius:6px;"
            "background:#0a0520;border:2px solid #2a1060;color:#a090d0;}"
            "QPushButton:checked{background:#0a2510;border:2px solid #30c040;color:#60ff80;}"
            "QPushButton:hover{border-color:#f0c030;color:#f0c030;}")
        self.turtle_btn.clicked.connect(self._toggle_turtle)
        pbl.addWidget(self.turtle_btn)
        main_layout.addWidget(prof_bar)

        # ═══ SCROLLABLE CONTENT — wrapped in themed container ══
        self._theme_container=QWidget()
        self._theme_container.setObjectName("theme_container")
        tcl=QVBoxLayout(self._theme_container); tcl.setSpacing(0); tcl.setContentsMargins(0,0,0,0)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tcl.addWidget(scroll)
        main_layout.addWidget(self._theme_container)

        page=SpaceBgWidget(); scroll.setWidget(page)
        root=QVBoxLayout(page); root.setSpacing(0); root.setContentsMargins(30,22,30,50)

        # ═══ DEVICES ══════════════════════════════
        _s0_ctr = QWidget()
        _s0_lay = QVBoxLayout(_s0_ctr); _s0_lay.setSpacing(0); _s0_lay.setContentsMargins(0,6,0,6)
        # Starbase tip box
        tip_box = QWidget()
        tip_box.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 rgba(40,30,0,200),stop:0.5 rgba(60,45,0,200),stop:1 rgba(40,30,0,200));"
            "border:2px solid #f0c030;border-radius:8px;")
        tip_lay = QHBoxLayout(tip_box); tip_lay.setContentsMargins(18,12,18,12); tip_lay.setSpacing(14)
        tip_icon = QLabel("⚠️")
        tip_icon.setStyleSheet("font-size:22px;background:transparent;border:none;")
        tip_lay.addWidget(tip_icon)
        tip_text = QLabel(
            "<b>IMPORTANT STARBASE SETTING:</b>  "
            "Go to <b>Settings → Controls → Key Hold Detection</b> "
            "and set it to <b>0.0</b> or <b>0.1</b> seconds (default is 0.6). "
            "At 0.6s the game buffers rapid keypresses and movement feels jerky. "
            "Setting to 0.0–0.1 makes PWM input smooth and responsive.")
        tip_text.setStyleSheet("font-size:14px;background:transparent;border:none;")
        tip_text.setWordWrap(True)
        tip_lay.addWidget(tip_text, stretch=1)
        _s0_lay.addWidget(tip_box)
        _s0_lay.addWidget(gap(8))
        _s0_lay.addWidget(section_heading("STEP  0  —  CONNECT  YOUR  DEVICES"))
        _s0_lay.addWidget(gap(8))
        dev_grp=QGroupBox("Tell the app which physical device is which")
        dev_l=QVBoxLayout(dev_grp); dev_l.setSpacing(12); dev_l.setContentsMargins(18,22,18,16)
        self.dev_combos={}
        for slot in DEVICE_SLOTS:
            row=QHBoxLayout(); row.setSpacing(14)
            lbl=QLabel(DEVICE_LABELS[slot]); lbl.setMinimumWidth(420); lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size:20px;font-weight:bold")
            combo=NoScrollCombo(); combo.setFixedHeight(46)
            self.dev_combos[slot]=combo
            row.addWidget(lbl); row.addWidget(combo,stretch=1)
            dev_l.addLayout(row)
        scan_row=QHBoxLayout()
        scan_btn=QPushButton("SCAN  FOR  DEVICES"); scan_btn.setFixedHeight(46); scan_btn.setMinimumWidth(240)
        scan_btn.setToolTip("Click this if your sticks don't appear in the dropdowns above.\nPlug them in first, then scan.")
        scan_btn.clicked.connect(self._scan_devices)
        scan_row.addWidget(scan_btn); scan_row.addStretch()
        dev_l.addLayout(scan_row)
        _s0_lay.addWidget(dev_grp)
        _s0_lay.addWidget(gap(14)); root.addWidget(hdivider()); root.addWidget(gap(14))

        # ═══ MOVEMENT CARDS ═══════════════════════
        root.addWidget(CollapsibleSection("STEP 0  —  CONNECT YOUR DEVICES", _s0_ctr))
        _s13_ctr = QWidget()
        _s13_lay = QVBoxLayout(_s13_ctr); _s13_lay.setSpacing(0); _s13_lay.setContentsMargins(0,6,0,6)
        # ═══ TURTLE MODE BANNER (top) ══════════════════════
        self._turtle_banner_top = self._build_turtle_banner()
        _s13_lay.addWidget(self._turtle_banner_top)

        _s13_lay.addWidget(section_heading("STEP  1-3  —  CONFIGURE  EACH  MOVEMENT"))
        _s13_lay.addWidget(gap(8))
        hint=QLabel("For each movement:  ① Pick which axis controls it  ② Set keyboard keys  ③ Tune the feel")
        hint.setStyleSheet("color:#a098c8;font-size:18px;padding:4px 0 12px 4px;")
        _s13_lay.addWidget(hint)
        _s13_lay.addWidget(hint_footer(
            "Each card below controls one axis of movement. Start with STEP 1: click DETECT, "
            "physically move that axis on your stick, click the bar that lights up, then press DETECT to confirm. "
            "Then set your keys in STEP 2 and tune the feel with the sliders and curve graph in STEP 3."))

        slot_map={"yaw":"stick","pitch":"stick","roll":"stick","thrust":"throttle","strafe_lr":"pedals","strafe_ud":"throttle","pedals":"pedals"}
        for mv_name in ["yaw","pitch","roll","thrust","strafe_lr","strafe_ud"]:
            mv_cfg=self.profile["movements"].get(mv_name,{})
            slot=slot_map[mv_name]; dev_lbl=DEVICE_LABELS[slot]
            card=MovementCard(mv_name,mv_cfg,dev_lbl)
            card.changed.connect(self._on_changed)
            self._cards[mv_name]=card
            mv_label = MOVEMENT_LABELS.get(mv_name,("","",""))
            mv_title = f"{mv_label[0]}  \u2014  {mv_label[1]}"
            mv_sec = CollapsibleSection(mv_title, card, expanded=True)
            _s13_lay.addWidget(mv_sec); _s13_lay.addWidget(gap(4))

        root.addWidget(CollapsibleSection("STEP 1-3  —  CONFIGURE MOVEMENTS", _s13_ctr))
        _lm_ctr = QWidget()
        _lm_lay = QVBoxLayout(_lm_ctr); _lm_lay.setSpacing(0); _lm_lay.setContentsMargins(0,6,0,6)
        _lm_lay.addWidget(hdivider()); root.addWidget(gap(14))

        # ═══ LIVE MONITOR ══════════════════════════
        _lm_lay.addWidget(section_heading("LIVE  MONITOR"))
        _lm_lay.addWidget(gap(8))
        mon_grp=QGroupBox("What the app is currently reading from your sticks — press START first")
        mon_l=QVBoxLayout(mon_grp); mon_l.setSpacing(6); mon_l.setContentsMargins(18,22,18,16)
        for mv in ["yaw","pitch","roll","thrust","strafe_lr","strafe_ud"]:
            lbl_data=MOVEMENT_LABELS[mv]
            bar=LiveBar(lbl_data[0])   # just the short name, no cut-off description
            self._live_bars[mv]=bar; mon_l.addWidget(bar)
        _lm_lay.addWidget(mon_grp)
        root.addWidget(CollapsibleSection("LIVE MONITOR", _lm_ctr))

        # ═══ FEEL DISCLAIMER ══════════════════════════════════
        feel_box = QWidget()
        feel_box.setStyleSheet(
            "background:rgba(20,20,40,180);"
            "border:1px solid rgba(180,160,255,50);border-radius:8px;")
        feel_lay = QHBoxLayout(feel_box)
        feel_lay.setContentsMargins(18,12,18,12); feel_lay.setSpacing(14)
        feel_icon = QLabel("🚀")
        feel_icon.setStyleSheet("font-size:22px;background:transparent;border:none;")
        feel_lay.addWidget(feel_icon)
        feel_text = QLabel(
            "<b>About the feel:</b>  Each stick movement fires the ship thrusters in pulses. "
            "and zero latency is not achievable — nor should you expect it. "
            "Think of it like landing on the Moon with a real spacecraft: "
            "the ship needs momentum to get moving and momentum to stop, "
            "Each keypress is a real thruster firing: "
            "<b>Fire Rate</b> = how often the thruster fires.  <b>Burn Time</b> = how long each firing lasts.  Tune both to work <i>with</i> the ship physics.")
        feel_text.setStyleSheet("font-size:13px;background:transparent;border:none;")
        feel_text.setWordWrap(True)
        feel_lay.addWidget(feel_text, stretch=1)
        root.addWidget(feel_box)
        root.addWidget(gap(14)); root.addWidget(hdivider()); root.addWidget(gap(14))

        # ═══ KEY OUTPUT TEST ═══════════════════════
        root.addWidget(section_heading("KEY  OUTPUT  TEST"))
        root.addWidget(gap(8))
        test_grp=QGroupBox("Live stream of key presses sent to the game — press START then move your sticks")
        test_l=QVBoxLayout(test_grp); test_l.setSpacing(8); test_l.setContentsMargins(14,20,14,14)
        self._key_test=KeyTestDisplay()
        test_l.addWidget(self._key_test)
        clr_test_btn=QPushButton("CLEAR"); clr_test_btn.setFixedHeight(34); clr_test_btn.setFixedWidth(100)
        clr_test_btn.clicked.connect(lambda: self._key_test.clear())
        br=QHBoxLayout(); br.addStretch(); br.addWidget(clr_test_btn)
        test_l.addLayout(br)
        root.addWidget(test_grp)
        root.addWidget(gap(14)); root.addWidget(hdivider()); root.addWidget(gap(14))

        # ═══ TURTLE MODE BANNER (bottom) ══════════════════
        self._turtle_banner_bot = self._build_turtle_banner()
        root.addWidget(self._turtle_banner_bot)
        root.addWidget(gap(14)); root.addWidget(hdivider()); root.addWidget(gap(14))

        # ═══ SAVE LOCATION ════════════════════════
        root.addWidget(section_heading("SAVE  LOCATION"))
        root.addWidget(gap(8))
        save_grp=QGroupBox("All profiles and settings are saved here")
        save_l=QVBoxLayout(save_grp); save_l.setContentsMargins(18,22,18,16)
        path_lbl=QLabel(str(PROFILES_DIR))
        path_lbl.setStyleSheet("font-size:16px;font-family:Courier New;padding:8px;")
        path_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_lbl.setToolTip("Click and drag to select, then Ctrl+C to copy")
        save_l.addWidget(path_lbl)
        open_btn=QPushButton("OPEN  FOLDER")
        open_btn.setFixedHeight(38); open_btn.setMinimumWidth(160)
        open_btn.setToolTip("Open the save folder in Windows Explorer")
        open_btn.clicked.connect(lambda: __import__('os').startfile(str(PROFILES_DIR)))
        br=QHBoxLayout(); br.addWidget(open_btn); br.addStretch()
        save_l.addLayout(br)
        root.addWidget(save_grp)
        root.addWidget(gap(40))

    # ── First-launch welcome ─────────────────────────────────
    def _maybe_show_welcome(self):
        if not self._first_launch: return
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
        dlg = QDialog(self)
        dlg.setWindowTitle("Welcome to Starbase HOTAS Bridge")
        dlg.setMinimumWidth(560)
        dlg.setStyleSheet(self.styleSheet())
        lay = QVBoxLayout(dlg); lay.setSpacing(18); lay.setContentsMargins(30,24,30,24)

        title = QLabel("WELCOME")
        title.setStyleSheet("color:#ffffff;font-size:26px;font-weight:bold;letter-spacing:4px;")
        lay.addWidget(title)

        msg = QLabel(
            "No saved profiles were found.\n\n"
            "Do you have a VKB dual-stick setup?\n"
            "  (Gladiator EVO R + Gladiator EVO L + T-Rudder pedals)\n\n"
            "If yes, load the pre-tuned VKB Default profile.\n"
            "If no, start with a blank setup and use the DETECT\n"
            "button in each movement card to map your own axes."
        )
        msg.setStyleSheet("font-size:16px;line-height:160%")
        msg.setWordWrap(True)
        lay.addWidget(msg)

        btn_row = QHBoxLayout(); btn_row.setSpacing(12)

        vkb_btn = QPushButton("LOAD  VKB  DEFAULT  PROFILE")
        vkb_btn.setFixedHeight(50)
        vkb_btn.setStyleSheet(
            "background:rgba(40,200,80,120);border:2px solid #40e060;"
            "border-radius:6px;color:#ffffff;font-size:16px;font-weight:bold;")

        blank_btn = QPushButton("START  BLANK  —  I HAVE  OTHER  HARDWARE")
        blank_btn.setFixedHeight(50)

        def _apply_profile(p):
            """Load a profile into the UI exactly as _load_sel does."""
            save_profile(p)
            self.profile = p
            self._populate_devices()          # restore device dropdowns
            for mv, card in self._cards.items():
                card.apply_config(p["movements"].get(mv,
                    BLANK_PROFILE["movements"].get(mv, {})))
            LAST_PROFILE_FILE.write_text(p["name"], encoding="utf-8")
            self._refresh_profiles()
            self._select_profile_in_bar(p["name"])
            dlg.accept()

        def load_vkb():
            _apply_profile(copy.deepcopy(DEFAULT_PROFILE))

        def start_blank():
            _apply_profile(copy.deepcopy(BLANK_PROFILE))

        vkb_btn.clicked.connect(load_vkb)
        blank_btn.clicked.connect(start_blank)
        btn_row.addWidget(vkb_btn); btn_row.addWidget(blank_btn)
        lay.addLayout(btn_row)
        dlg.exec()

    # ── Theme ────────────────────────────────────────────────
    def _apply_theme(self, theme_name=None):
        global CURRENT_THEME, _GC
        if theme_name and theme_name in THEME_PRESETS:
            CURRENT_THEME = theme_name
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentText(theme_name)
            self.theme_combo.blockSignals(False)
        # Apply graph color swatch
        sw = THEME_SWATCH[CURRENT_THEME]
        graph_idx = sw[3] if len(sw) > 3 else 0
        # Ensure sw always has 4 elements going forward
        if len(sw) < 4: sw += [0] * (4 - len(sw))
        graph_presets = THEME_PRESETS[CURRENT_THEME].get("graph")
        if graph_presets and graph_idx < len(graph_presets):
            gp = graph_presets[graph_idx]
            def gc(k, a=255):
                r,g,b = gp[k]
                return QColor(max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)), a)
            def gc_light(k, pct):
                r,g,b = gp[k]
                f = pct/100.0
                return QColor(min(255,int(r+f*(255-r))), min(255,int(g+f*(255-g))), min(255,int(b+f*(255-b))))
            _GC = dict(
                bg=gc("bg"), grid=gc("grid"), dim=gc("label"),
                curve0=gc("curve0"), curve1=gc("curve1"),
                ghost=gc("curve0",60), handle=gc("handle"),
                handle_h=gc_light("handle", 30),
                handle_d=gc_light("handle", 60),
                live=gc("live"), dz=gc("dz",140),
                maxspd=gc("maxspd",120), pulse=gc("pulse",100),
                border=gc("grid"), label=gc("label"),
            )
        else:
            _GC = GRAPH_COLORS.get(CURRENT_THEME, GRAPH_COLORS["Space"])
        # Apply theme only to the scrollable content area, NOT the header
        self._theme_container.setStyleSheet(build_stylesheet())
        # Update swatch button labels to reflect current selections
        self._refresh_swatch_buttons()
        for w in self._theme_container.findChildren(QWidget):
            w.update()
        # Force repaint of custom-drawn widgets inside theme container
        self._theme_container.update()
        # Update header color to match theme BG
        p2 = THEME_PRESETS[CURRENT_THEME]
        sw2 = THEME_SWATCH[CURRENT_THEME]
        self._update_header_color(p2["bg"][sw2[0]])
        # Persist theme change to session
        try: save_session_state(self.profile, CURRENT_THEME, dict(THEME_SWATCH))
        except: pass

    def _cycle_swatch(self, idx):
        """Cycle swatch index (0=bg,1=text,2=btn,3=graph)."""
        sw = THEME_SWATCH[CURRENT_THEME]
        # Ensure 4 elements exist
        while len(sw) < 4: sw.append(0)
        presets = THEME_PRESETS[CURRENT_THEME]
        if idx == 3:
            n = len(presets.get("graph", [None]))
        else:
            n = len(presets[["bg","text","btn"][idx]])
        sw[idx] = (sw[idx] + 1) % max(1, n)
        self._apply_theme()

    def _refresh_swatch_buttons(self):
        if not hasattr(self, '_swatch_btns'): return
        p  = THEME_PRESETS[CURRENT_THEME]
        sw = THEME_SWATCH[CURRENT_THEME]
        for i, btn in enumerate(self._swatch_btns):
            if i == 3:
                # Graph swatch — show preview as a small colored circle
                gp = p.get("graph")
                gi = sw[3] if len(sw) > 3 else 0
                if gp and gi < len(gp):
                    r,g,b = gp[gi]["curve0"]
                    color = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    color = "#4060a0"
            else:
                color = p[["bg","text","btn"][i]][sw[i]]
            is_dark = _hex_to_rgb(color)[0] < 128 if color.startswith('#') and len(color)==7 else True
            txt_col = "#ffffff" if is_dark else "#000000"
            btn.setStyleSheet(
                f"background:{color};color:{txt_col};border:2px solid rgba(255,255,255,120);"
                f"border-radius:4px;font-size:11px;font-weight:bold;min-height:24px;padding:0 8px;"
            )


    # ── Device scan ──────────────────────────────────────────

    def _update_header_color(self, bg_hex):
        """Set header bars using QPalette — bypasses stylesheet cascade entirely."""
        try:
            r=int(bg_hex[1:3],16); g=int(bg_hex[3:5],16); b=int(bg_hex[5:7],16)
            hr=max(0,int(r*.65)); hg=max(0,int(g*.65)); hb=max(0,int(b*.65))
            color = QColor(hr, hg, hb)
        except:
            color = QColor(8, 3, 24)
        from PyQt6.QtGui import QPalette
        for bar in [getattr(self,"_title_strip",None), getattr(self,"_prof_bar",None)]:
            if bar:
                bar.setStyleSheet("")          # clear any stylesheet
                pal = bar.palette()
                pal.setColor(QPalette.ColorRole.Window, color)
                bar.setPalette(pal)
                bar.setAutoFillBackground(True)
                bar.update()

    # ── Instructions panel ───────────────────────────────────
    def _build_help_panel(self):
        """Full collapsible instructions panel shown below the title bar."""
        panel = QWidget()
        panel.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #0c0828,stop:1 #080520);"
            "border-bottom:2px solid #f0c030;")
        lay = QVBoxLayout(panel); lay.setContentsMargins(32,20,32,20); lay.setSpacing(16)

        header = QLabel("HOW TO USE STARBASE HOTAS BRIDGE")
        header.setStyleSheet("color:#f0c030;font-size:18px;font-weight:bold;letter-spacing:4px;")
        lay.addWidget(header)

        sections = [
            ("QUICK START",
             "1. Plug in your sticks.\n"
             "2. In Starbase: Settings → Controls → Key Hold Detection → set to 0.0 or 0.1\n"
             "   (default 0.6 causes jerky movement with PWM input)\n"
             "3. Use the STEP 0 dropdowns to assign Right Stick, Left Stick/Throttle, Pedals.\n"
             "4. Click SCAN FOR DEVICES if they don't appear.\n"
             "5. Click START (green button, top right).\n"
             "6. Launch Starbase. Move your sticks — the ship responds."),

            ("THE FEEL — WHAT TO EXPECT",
             "Control through this bridge is not artificially snappy \n"
             "and zero latency is not the goal.\n\n"
             "Think of it like landing on the Moon with a real spacecraft:\n"
             "the ship needs momentum to get moving, and momentum to stop.\n"
             "Starbase uses a thruster pulse system — each keypress fires\n"
             "a real thruster burst that builds velocity over time.\n\n"
             "Tune your curves and pulse lengths to work with the physics.\n"
             "Gentle inputs for fine control, full deflection for committed burns."),

            ("STEP 1 — ASSIGN AXES",
             "Each movement card controls one direction of flight (Yaw, Pitch, Roll, Thrust, Strafe).\n"
             "To assign an axis:\n"
             "  ①  Click the DETECT button in the card\n"
             "  ②  Move the physical axis on your stick (push forward, twist, etc.)\n"
             "  ③  A bar will light up — click it\n"
             "  ④  The axis is now assigned\n"
             "If a movement has no axis (e.g. no pedals), click NOT USED."),

            ("STEP 2 — SET KEYS",
             "Click any key field (the box showing a letter) then press the key you want.\n"
             "Works with: letters, Shift, Ctrl, Alt, F1-F12, arrow keys, and more.\n"
             "The left field fires when the axis goes negative (left/down/back).\n"
             "The right field fires when the axis goes positive (right/up/forward)."),

            ("STEP 3 — TUNE THE FEEL",
             "DEAD ZONE — How far to move before thrusters respond.\n\n"
             "THRUSTER FIRE RATE — Keypresses/sec = how often the thruster fires.\n"
             "  Low = slow speed build-up.  High = rapid acceleration.\n\n"
             "THRUSTER BURN TIME — Key hold duration = how long each firing lasts.\n"
             "  Short = brief burst, easy to stop.  Long = sustained burn.\n\n"
             "CURVE GRAPH — Shows thruster fires/sec vs stick angle.\n"
             "  Higher handles = more thrust at that stick angle.\n"
             "  Double-click to reset. Use preset buttons for common shapes."),

            ("TURTLE MODE",
             "Turtle mode lets you swap to a slower, more precise profile instantly.\n"
             "Click CONFIGURE TURTLE PROFILE to set it up, then toggle with the \U0001f422 button.\n"
             "Changes made while in turtle mode are saved to the turtle profile automatically."),

            ("PROFILES & SAVING",
             "The app autosaves continuously — your settings are never lost.\n"
             "SAVE — Save to the current profile name (asks before overwriting).\n"
             "SAVE AS — Save with a new name.\n"
             "LOAD — Switch to a different profile.\n"
             "NEW — Create a blank or VKB-default profile.\n"
             "All saves go to: Documents\\StarbaseHOTAS\\"),

            ("KEY OUTPUT TEST",
             "The strip at the bottom shows every keypress being sent to the game.\n"
             "Press START, then move a stick — blocks should scroll across.\n"
             "More blocks = more keypresses per second = faster movement.\n"
             "Test in Notepad first: focus Notepad, press START, move a stick — letters should appear."),
        ]

        cols = QHBoxLayout(); cols.setSpacing(32)
        col1 = QVBoxLayout(); col1.setSpacing(14)
        col2 = QVBoxLayout(); col2.setSpacing(14)

        for i, (title, body) in enumerate(sections):
            col = col1 if i < 4 else col2
            blk = QWidget()
            blk.setStyleSheet("background:rgba(255,255,255,5);border-radius:6px;border:1px solid rgba(180,160,255,30);")
            blk_l = QVBoxLayout(blk); blk_l.setContentsMargins(14,10,14,10); blk_l.setSpacing(4)
            t = QLabel(title)
            t.setStyleSheet("color:#f0c030;font-size:13px;font-weight:bold;letter-spacing:2px;background:transparent;border:none;")
            b = QLabel(body)
            b.setStyleSheet("color:#c0b8e8;font-size:13px;line-height:150%;background:transparent;border:none;")
            b.setWordWrap(True)
            blk_l.addWidget(t); blk_l.addWidget(b)
            col.addWidget(blk)

        col1.addStretch(); col2.addStretch()
        cols.addLayout(col1, stretch=1); cols.addLayout(col2, stretch=1)
        lay.addLayout(cols)

        close_btn = QPushButton("CLOSE  INSTRUCTIONS")
        close_btn.setFixedHeight(36); close_btn.setMinimumWidth(200)
        close_btn.setStyleSheet(
            "QPushButton{font-size:13px;font-weight:bold;background:rgba(40,20,80,180);"
            "border:1px solid rgba(180,140,255,120);border-radius:4px;color:#c0a0ff;}"
            "QPushButton:hover{border-color:#f0c030;color:#f0c030;}")
        close_btn.clicked.connect(lambda: self._toggle_help(False))
        row = QHBoxLayout(); row.addStretch(); row.addWidget(close_btn)
        lay.addLayout(row)
        return panel

    def _toggle_help(self, force=None):
        if force is None:
            visible = not self._help_panel.isVisible()
        else:
            visible = bool(force)
        self._help_panel.setVisible(visible)
        self.help_btn.setChecked(visible)
        self.help_btn.setText("x CLOSE" if visible else "? INSTRUCTIONS")

    # ── Turtle mode ──────────────────────────────────────────
    def _build_turtle_banner(self):
        w = QWidget()
        w.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 rgba(0,40,10,180),stop:0.5 rgba(0,60,15,180),stop:1 rgba(0,40,10,180));"
            "border:2px solid #1a6030;border-radius:10px;")
        lay = QHBoxLayout(w); lay.setContentsMargins(20,14,20,14); lay.setSpacing(16)
        icon = QLabel("🐢")
        icon.setStyleSheet("font-size:28px;background:transparent;border:none;")
        lay.addWidget(icon)
        txt_col = QVBoxLayout(); txt_col.setSpacing(2)
        title = QLabel("TURTLE  MODE")
        title.setStyleSheet("font-size:16px;font-weight:bold;letter-spacing:4px;"
                            "color:#60ff80;background:transparent;border:none;")
        desc = QLabel("Swap to a precision profile for fine maneuvers. Toggles live.")
        desc.setStyleSheet("font-size:13px;color:#90d0a0;background:transparent;border:none;")
        txt_col.addWidget(title); txt_col.addWidget(desc)
        lay.addLayout(txt_col, stretch=1)
        cfg_btn = QPushButton("CONFIGURE  TURTLE  PROFILE")
        cfg_btn.setFixedHeight(42); cfg_btn.setMinimumWidth(230)
        cfg_btn.setStyleSheet(
            "QPushButton{font-size:13px;font-weight:bold;background:#0a2010;"
            "border:1px solid #30a050;border-radius:6px;color:#60ff80;padding:0 14px;}"
            "QPushButton:hover{background:#0f3018;border-color:#80ff80;}")
        cfg_btn.clicked.connect(self._configure_turtle)
        lay.addWidget(cfg_btn)
        tog = QPushButton("🐢  NORMAL")
        tog.setCheckable(True); tog.setChecked(self._turtle_mode)
        tog.setFixedHeight(42); tog.setMinimumWidth(150)
        tog.setStyleSheet(
            "QPushButton{font-size:14px;font-weight:bold;background:#0a0520;"
            "border:2px solid #2a1060;border-radius:6px;color:#a090d0;padding:0 14px;}"
            "QPushButton:checked{background:#0a2510;border:2px solid #30c040;color:#60ff80;}"
            "QPushButton:hover{border-color:#f0c030;color:#f0c030;}")
        tog.clicked.connect(self._toggle_turtle)
        lay.addWidget(tog)
        if not hasattr(self, "_turtle_toggles"):
            self._turtle_toggles = []
        self._turtle_toggles.append(tog)
        return w

    def _sync_turtle_buttons(self):
        label = "🐢  TURTLE" if self._turtle_mode else "🐢  NORMAL"
        for btn in getattr(self, "_turtle_toggles", []):
            btn.blockSignals(True)
            btn.setChecked(self._turtle_mode); btn.setText(label)
            btn.blockSignals(False)
        if hasattr(self, "turtle_btn"):
            self.turtle_btn.blockSignals(True)
            self.turtle_btn.setChecked(self._turtle_mode)
            self.turtle_btn.setText(label)
            self.turtle_btn.blockSignals(False)

    def _toggle_turtle(self, checked=None):
        if checked is None:
            self._turtle_mode = not self._turtle_mode
        else:
            self._turtle_mode = bool(checked)
        tp = self.profile.get("turtle_profile")
        if self._turtle_mode:
            if not tp:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Turtle Mode",
                    "No turtle profile configured yet.\n\n"
                    "Click CONFIGURE TURTLE PROFILE to set one up,\n"
                    "then toggle again.")
                self._turtle_mode = False
                self._sync_turtle_buttons(); return
            self._base_movements = copy.deepcopy(self.profile["movements"])
            self._apply_movements(tp["movements"])
        else:
            if self._base_movements:
                self._apply_movements(self._base_movements)
                self._base_movements = None
        self._sync_turtle_buttons()
        if self._worker and self._worker.active:
            self._worker.sync()

    def _apply_movements(self, movements):
        self.profile["movements"] = copy.deepcopy(movements)
        self._populate_devices()
        for mv, card in self._cards.items():
            if mv in movements:
                card.apply_config(movements[mv])
        if self._worker and self._worker.active:
            self._worker.sync()

    def _configure_turtle(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox
        dlg = QDialog(self); dlg.setWindowTitle("Configure Turtle Profile")
        dlg.setMinimumWidth(520)
        lay = QVBoxLayout(dlg); lay.setSpacing(14); lay.setContentsMargins(24,20,24,20)
        ttl = QLabel("🐢  TURTLE  MODE  PROFILE")
        ttl.setStyleSheet("font-size:18px;font-weight:bold;color:#60ff80;letter-spacing:3px;")
        lay.addWidget(ttl)
        desc = QLabel(
            "The turtle profile is a full second set of settings:\n"
            "curves, speeds, pulses, and axes.\n\n"
            "Choose how to set it up:")
        desc.setStyleSheet("font-size:15px;")
        lay.addWidget(desc)
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        copy_btn = QPushButton("COPY  CURRENT  SETTINGS")
        copy_btn.setFixedHeight(44)
        copy_btn.setToolTip("Start with a copy of your current profile")
        load_btn = QPushButton("LOAD  FROM  SAVED  PROFILE")
        load_btn.setFixedHeight(44)
        load_btn.setToolTip("Use a previously saved profile as the turtle profile")
        tp = self.profile.get("turtle_profile")
        status = QLabel("" if not tp else
                        f"Turtle profile set ({len(tp.get('movements',{}))} movements).")
        status.setStyleSheet("font-size:14px;color:#f0c030;")
        def copy_current():
            self.profile["turtle_profile"] = {
                "movements": copy.deepcopy(self.profile["movements"]),
                "devices":   copy.deepcopy(self.profile["devices"]),
            }
            status.setText("Copied. Switch to turtle mode and adjust sliders for precision.")
            try: save_session_state(self.profile, CURRENT_THEME, dict(THEME_SWATCH))
            except: pass
        def load_from():
            profiles = list_profiles()
            if not profiles: status.setText("No saved profiles found."); return
            from PyQt6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getItem(dlg, "Load Profile",
                "Select profile to use as turtle profile:", profiles, 0, False)
            if ok and name:
                try:
                    p = migrate(load_profile(name))
                    self.profile["turtle_profile"] = {
                        "movements": copy.deepcopy(p["movements"]),
                        "devices":   copy.deepcopy(p.get("devices", self.profile["devices"])),
                    }
                    status.setText(f"Turtle profile loaded from: {name}")
                    try: save_session_state(self.profile, CURRENT_THEME, dict(THEME_SWATCH))
                    except: pass
                except Exception as e:
                    status.setText(f"Error: {e}")
        copy_btn.clicked.connect(copy_current)
        load_btn.clicked.connect(load_from)
        btn_row.addWidget(copy_btn); btn_row.addWidget(load_btn)
        lay.addLayout(btn_row); lay.addWidget(status)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bb.rejected.connect(dlg.accept); lay.addWidget(bb)
        dlg.exec()

    def _initial_scan(self):
        self._reader.rescan(); self._populate_devices(); self._poll_timer.start()

    def _scan_devices(self):
        self._reader.rescan(); self._populate_devices()

    def _populate_devices(self):
        names=self._reader.get_names()
        saved=self.profile.get("devices",{})
        for slot,combo in self.dev_combos.items():
            saved_idx=saved.get(slot,-1)
            include_none=(slot!="stick")
            combo.blockSignals(True); combo.clear()
            if include_none: combo.addItem("— Not connected / not used —",-1)
            best=-1; found=False
            for i,name in names.items():
                is_vjoy="vjoy" in name.lower() or "virtual" in name.lower()
                tag="  [vJoy — skip]" if is_vjoy else "  ✓"
                combo.addItem(f"[{i}]  {name}{tag}",i)
                if not is_vjoy and not found: best=i; found=True
            if include_none:
                restore=saved_idx if saved_idx in names else -1
            else:
                restore=saved_idx if saved_idx in names else (best if best>=0 else 0)
            for ci in range(combo.count()):
                if combo.itemData(ci)==restore: combo.setCurrentIndex(ci); break
            combo.blockSignals(False)

    # ── Poll ─────────────────────────────────────────────────
    def _poll(self):
        idx_stick   =self.dev_combos["stick"].currentData()    or 0
        idx_throttle=self.dev_combos["throttle"].currentData()
        idx_pedals  =self.dev_combos["pedals"].currentData()
        if idx_throttle is None: idx_throttle=-1
        if idx_pedals   is None: idx_pedals  =-1

        axes_stick   =self._reader.read(idx_stick)
        axes_throttle=self._reader.read(idx_throttle) if idx_throttle>=0 and idx_throttle!=idx_stick else []
        axes_pedals  =self._reader.read(idx_pedals)   if idx_pedals>=0 else []

        slot_map={"yaw":"stick","pitch":"stick","roll":"stick","thrust":"throttle","strafe_lr":"pedals","strafe_ud":"throttle","pedals":"pedals"}
        src_map ={"stick":axes_stick,"throttle":axes_throttle,"pedals":axes_pedals}

        for mv_name,card in self._cards.items():
            card.feed_detector(src_map.get(slot_map[mv_name],[]))

        used_axes={}
        results={}
        for mv_name in ["yaw","pitch","roll","thrust","strafe_lr","strafe_ud"]:
            mv=self.profile["movements"].get(mv_name,{})
            ai=mv.get("physical_axis",NO_AXIS)
            src=src_map.get(slot_map[mv_name],[])
            src_id={"stick":idx_stick,"throttle":idx_throttle,"pedals":idx_pedals}[slot_map[mv_name]]

            if ai==NO_AXIS or ai>=len(src):
                raw=proc=0.0
            else:
                key=(src_id,ai)
                if key in used_axes:
                    raw=proc=0.0
                else:
                    used_axes[key]=mv_name
                    raw=src[ai]
                    card     = self._cards.get(mv_name)
                    dz_val   = card.dz_sl.value() if card else mv.get("deadzone",5)
                    inv_val  = card.inv_btn.isChecked() if card else mv.get("inverted",False)
                    cp_val   = card.get_config().get("control_points") if card else mv.get("control_points")
                    # Auto-correct deadzone: if resting drift exceeds current setting, bump it up
                    rec_dz = self._reader.get_recommended_deadzone(src_id, ai)
                    if rec_dz > dz_val:
                        dz_val = rec_dz
                        if card:
                            card.dz_sl.blockSignals(True)
                            card.dz_sl.setValue(rec_dz)
                            card.dz_sl.blockSignals(False)
                    proc=process_axis(raw, dz_val, inv_val, cp_val)

            # Pedal override for yaw
            if mv_name=="yaw" and len(axes_pedals)>0:
                pv=self.profile["movements"].get("pedals",{})
                pai=pv.get("physical_axis",NO_AXIS)
                if pai!=NO_AXIS and pai<len(axes_pedals):
                    pp=process_axis(axes_pedals[pai],pv.get("deadzone",5),pv.get("inverted",False),
                                    pv.get("control_points",None))
                    if abs(pp)>abs(proc): proc=pp

            if self._worker and self._worker.active:
                self._worker.feed(mv_name,proc)
            results[mv_name]=(raw,proc)

        for mv_name,bar in self._live_bars.items():
            rv,pv=results.get(mv_name,(0,0))
            assigned=self.profile["movements"].get(mv_name,{}).get("physical_axis",NO_AXIS)!=NO_AXIS
            bar.set_value(pv,active=assigned)

        # Feed live value to curve graphs
        for mv_name,card in self._cards.items():
            rv,pv=results.get(mv_name,(0,0))
            card.feed_live(rv, pv)

        # Drain key event queue into test display (main thread, safe to call Qt)
        if self._key_test and self._key_queue:
            # Splice out all pending events atomically (GIL protects list ops)
            n = len(self._key_queue)
            events = self._key_queue[:n]
            del self._key_queue[:n]
            for k in events:
                self._key_test.add_key(k)

        self._fc+=1; now=time.perf_counter()
        if now-self._ft>=1.0:
            self.poll_lbl.setText(f"{self._fc} Hz"); self._fc=0; self._ft=now

    # ── Toggle ───────────────────────────────────────────────
    def _toggle(self):
        if self._worker and self._worker.active:
            self._worker.stop(); self._worker=None
            self.run_btn.setText("START"); self.run_btn.setProperty("active","false")
            self.status_lbl.setText("NOT RUNNING")
            self.status_lbl.setStyleSheet("color:#ff6060;font-size:18px;letter-spacing:3px;font-weight:bold;min-width:180px;")
        else:
            self._collect()
            self._check_conflicts()
            key_q = self._key_queue
            def _cb(k):
                try:
                    s = str(k)
                    # pynput Key enum: "<Key.shift: 65505>" → "shift"
                    if s.startswith("<Key."):
                        name = s.split(".")[1].split(":")[0]
                    elif s.startswith("'") and len(s) == 3:
                        name = s[1]   # single char like 'a'
                    elif len(s) == 1:
                        name = s
                    else:
                        name = s.strip("<>").replace("Key.","")
                    key_q.append(name)
                except: pass
            cb = _cb
            self._worker=PWMWorker(self.profile, key_callback=cb); self._worker.start()
            idx=self.dev_combos["stick"].currentData() or 0
            name=self._reader.get_names().get(idx,"Unknown")
            self.run_btn.setText("STOP"); self.run_btn.setProperty("active","true")
            self.status_lbl.setText(f"RUNNING  —  {name[:26]}")
            self.status_lbl.setStyleSheet("color:#40ff80;font-size:18px;letter-spacing:2px;font-weight:bold;")
        self.run_btn.style().unpolish(self.run_btn); self.run_btn.style().polish(self.run_btn)

    def _on_changed(self): self._collect()

    def _collect(self):
        for slot,combo in self.dev_combos.items():
            idx=combo.currentData()
            if idx is not None: self.profile["devices"][slot]=idx
        for mv_name,card in self._cards.items():
            self.profile["movements"][mv_name]=card.get_config()
        if self._worker and self._worker.active: self._worker.sync()
        # If turtle mode is active, save edits back into the turtle profile
        if self._turtle_mode and self.profile.get("turtle_profile"):
            self.profile["turtle_profile"]["movements"] = copy.deepcopy(self.profile["movements"])
        # Autosave session state continuously
        try: save_session_state(self.profile, CURRENT_THEME, dict(THEME_SWATCH))
        except: pass

    def _check_conflicts(self):
        seen={}; conflicts=[]
        slot_map={"yaw":"stick","pitch":"stick","roll":"stick","thrust":"throttle","strafe_lr":"pedals","strafe_ud":"throttle","pedals":"pedals"}
        for mv_name,mv in self.profile["movements"].items():
            ai=mv.get("physical_axis",NO_AXIS)
            if ai==NO_AXIS: continue
            slot=slot_map.get(mv_name,"stick"); key=(slot,ai)
            if key in seen:
                conflicts.append(f"{seen[key].upper()} and {mv_name.upper()} both use axis {ai} on {slot}")
            else: seen[key]=mv_name
        if conflicts:
            lines=["WARNING: Two movements share the same physical axis!",""] + conflicts + [
                "","They will both fire at the same time.",
                "Set one to NOT USED or assign a different axis."]
            QMessageBox.warning(self,"Axis Conflict",chr(10).join(lines))

    # ── Profile management ───────────────────────────────────
    def _refresh_profiles(self):
        self.profile_combo.blockSignals(True); self.profile_combo.clear()
        for n in list_profiles(): self.profile_combo.addItem(n)
        self.profile_combo.blockSignals(False)

    def _select_profile_in_bar(self,name):
        idx=self.profile_combo.findText(name)
        if idx>=0: self.profile_combo.setCurrentIndex(idx)

    def _save_profile(self):
        """Save — asks before overwriting, like a video game."""
        self._collect()
        name=self.profile.get("name","Profile")
        if profile_exists(name):
            reply=QMessageBox.question(self,"Save Profile",
                f"Overwrite '{name}'?",
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if reply!=QMessageBox.StandardButton.Yes: return
        save_profile(self.profile)
        self._refresh_profiles(); self._select_profile_in_bar(name)

    def _save_as(self):
        """Save As — always prompts for a name."""
        self._collect()
        name,ok=QInputDialog.getText(self,"Save As","Enter profile name:",
                                     text=self.profile.get("name","Profile"))
        if not ok or not name.strip(): return
        name=name.strip()
        if profile_exists(name):
            reply=QMessageBox.question(self,"Overwrite?",
                f"'{name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if reply!=QMessageBox.StandardButton.Yes: return
        self.profile["name"]=name
        save_profile(self.profile)
        self._refresh_profiles(); self._select_profile_in_bar(name)

    def _load_sel(self):
        name=self.profile_combo.currentText()
        if not name: return
        try:
            self.profile=migrate(load_profile(name))
            self._populate_devices()
            for mv,card in self._cards.items():
                card.apply_config(self.profile["movements"].get(mv,DEFAULT_PROFILE["movements"].get(mv,{})))
            LAST_PROFILE_FILE.write_text(name,encoding="utf-8")
            try: save_session_state(self.profile, CURRENT_THEME, dict(THEME_SWATCH))
            except: pass
        except Exception as ex:
            QMessageBox.warning(self,"Load Failed",str(ex))

    def _new_prof(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
        # Ask: VKB defaults or blank?
        dlg = QDialog(self); dlg.setWindowTitle("New Profile"); dlg.setMinimumWidth(460)
        dlg.setStyleSheet(self.styleSheet())
        lay = QVBoxLayout(dlg); lay.setSpacing(14); lay.setContentsMargins(24,20,24,20)
        lay.addWidget(QLabel("Start from:"))
        row = QHBoxLayout()
        vkb = QPushButton("VKB DEFAULT  SETTINGS"); vkb.setFixedHeight(46)
        blank = QPushButton("BLANK  (all unassigned)"); blank.setFixedHeight(46)
        chosen = [None]
        def pick(v): chosen[0]=v; dlg.accept()
        vkb.clicked.connect(lambda: pick("vkb"))
        blank.clicked.connect(lambda: pick("blank"))
        row.addWidget(vkb); row.addWidget(blank); lay.addLayout(row)
        dlg.exec()
        if not chosen[0]: return

        name,ok=QInputDialog.getText(self,"New Profile","Profile name:",
            text="VKB Default" if chosen[0]=="vkb" else "My Setup")
        if not ok or not name.strip(): return
        name=name.strip()
        if profile_exists(name):
            QMessageBox.warning(self,"Already Exists",f"'{name}' already exists. Use Save As.")
            return
        template = copy.deepcopy(DEFAULT_PROFILE if chosen[0]=="vkb" else BLANK_PROFILE)
        template["name"] = name
        self.profile = template
        save_profile(self.profile)
        for mv,card in self._cards.items():
            card.apply_config(self.profile["movements"].get(mv,
                BLANK_PROFILE["movements"].get(mv,{})))
        self._refresh_profiles(); self._select_profile_in_bar(name)

    def _del_prof(self):
        name=self.profile_combo.currentText()
        if not name: return
        if QMessageBox.question(self,"Delete Profile",f"Delete '{name}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No
        )==QMessageBox.StandardButton.Yes:
            p=PROFILES_DIR/f"{name}.json"
            if p.exists(): p.unlink()
            if LAST_PROFILE_FILE.exists() and LAST_PROFILE_FILE.read_text().strip()==name:
                LAST_PROFILE_FILE.unlink()
            self._refresh_profiles()

    def closeEvent(self,e):
        self._poll_timer.stop()
        if self._worker: self._worker.stop()
        # Save profile and full session state on close
        self._collect()
        try: save_profile(self.profile)
        except: pass
        try: save_session_state(self.profile, CURRENT_THEME, dict(THEME_SWATCH))
        except: pass
        pygame.quit(); e.accept()

if __name__=="__main__":
    app=QApplication(sys.argv)
    app.setStyle("Fusion")
    win=MainWindow()
    win.show()
    sys.exit(app.exec())
