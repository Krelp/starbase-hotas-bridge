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
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPainterPath

pygame.init()
pygame.joystick.init()

WIN_W, WIN_H = 1580, 880
MONO = "Courier New"
NO_AXIS = 99
import sys as _sys

def _get_data_dir():
    """Always use Documents/StarbaseHOTAS — consistent for both script and exe."""
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
        "yaw":       {"physical_axis": NO_AXIS, "key_left": "q",    "key_right": "e",    "deadzone": 10, "speed": 40, "pulse": 20, "inverted": False},
        "pitch":     {"physical_axis": NO_AXIS, "key_left": "w",    "key_right": "s",    "deadzone": 10, "speed": 40, "pulse": 20, "inverted": False},
        "roll":      {"physical_axis": NO_AXIS, "key_left": "a",    "key_right": "d",    "deadzone": 10, "speed": 40, "pulse": 20, "inverted": False},
        "thrust":    {"physical_axis": NO_AXIS, "key_left": "shift","key_right": "ctrl", "deadzone": 10, "speed": 60, "pulse": 40, "inverted": False},
        "strafe_lr": {"physical_axis": NO_AXIS, "key_left": "left", "key_right": "right", "deadzone": 10, "speed": 40, "pulse": 20, "inverted": False},
        "strafe_ud": {"physical_axis": NO_AXIS, "key_left": "down", "key_right": "up",   "deadzone": 10, "speed": 40, "pulse": 20, "inverted": False},
        "pedals":    {"physical_axis": NO_AXIS, "key_left": "q",    "key_right": "e",    "deadzone": 10, "speed": 40, "pulse": 20, "inverted": False},
    }
}

DEFAULT_PROFILE = {
    "name": "VKB Default",
    "devices": {
        "stick":    0,   # VKBsim Gladiator EVO R SEM
        "throttle": 2,   # VKBsim Gladiator EVO L
        "pedals":   1,   # VKBSim T-Rudder
    },
    "movements": {
        "yaw":       {"physical_axis": 5,       "key_left": "q",    "key_right": "e",    "deadzone": 5, "speed": 60, "pulse": 10, "inverted": True,  "control_points": [[0.11435832274459974, 0.13858695652173914], [0.25667090216010163, 0.23097826086956522], [0.3646759847522236, 0.29891304347826086], [0.49047013977128334, 0.3804347826086957], [0.6315120711562897, 0.4891304347826087], [0.75, 0.5958], [0.875, 0.7863]]},
        "pitch":     {"physical_axis": 1,       "key_left": "w",    "key_right": "s",    "deadzone": 5, "speed": 60, "pulse": 20, "inverted": False, "control_points": [[0.13087674714104194, 0.20923913043478262], [0.2312579415501906, 0.2798913043478261], [0.37229987293519695, 0.35054347826086957], [0.5006353240152478, 0.46467391304347827], [0.6327827191867853, 0.5706521739130435], [0.7573062261753494, 0.6929347826086957], [0.8805590851334181, 0.8478260869565217]]},
        "roll":      {"physical_axis": 0,       "key_left": "a",    "key_right": "d",    "deadzone": 5, "speed": 60, "pulse": 20, "inverted": False, "control_points": [[0.1156289707750953, 0.20380434782608695], [0.23506988564167725, 0.29891304347826086], [0.34942820838627703, 0.3804347826086957], [0.49047013977128334, 0.4673913043478261], [0.6099110546378653, 0.5788043478260869], [0.7382465057179162, 0.7065217391304348], [0.8703939008894537, 0.8396739130434783]]},
        "thrust":    {"physical_axis": 1,       "key_left": "shift","key_right": "ctrl", "deadzone": 5, "speed": 80, "pulse": 50, "inverted": False, "control_points": [[0.13214739517153748, 0.15489130434782608], [0.241423125794155, 0.20923913043478262], [0.36721728081321475, 0.27717391304347827], [0.5006353240152478, 0.37228260869565216], [0.6149936467598475, 0.48097826086956524], [0.75, 0.5958], [0.875, 0.7863]]},
        "strafe_lr": {"physical_axis": 0,       "key_left": "left", "key_right": "right", "deadzone": 5, "speed": 60, "pulse": 20, "inverted": False, "control_points": [[0.12706480304955528, 0.20108695652173914], [0.24777636594663277, 0.2907608695652174], [0.38373570520965694, 0.41304347826086957], [0.5069885641677255, 0.5434782608695652], [0.6264294790343075, 0.6684782608695652], [0.7534942820838628, 0.8097826086956522], [0.8703939008894537, 0.907608695652174]]},
        "strafe_ud": {"physical_axis": 5,       "key_left": "down", "key_right": "up",   "deadzone": 5, "speed": 60, "pulse": 20, "inverted": False, "control_points": [[0.1207115628970775, 0.16304347826086957], [0.23506988564167725, 0.25271739130434784], [0.37229987293519695, 0.3451086956521739], [0.5095298602287166, 0.4483695652173913], [0.627700127064803, 0.5733695652173914], [0.7407878017789072, 0.7364130434782609], [0.8614993646759848, 0.8940217391304348]]},
        "pedals":    {"physical_axis": NO_AXIS, "key_left": "q",    "key_right": "e",    "deadzone": 5, "speed": 50, "pulse": 30, "inverted": False},
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
    with open(PROFILES_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)

def list_profiles():
    names = [p.stem for p in PROFILES_DIR.glob("*.json")]
    return sorted(names)

def profile_exists(name):
    return (PROFILES_DIR / f"{name}.json").exists()

def save_session_state(profile, theme, swatches):
    """Save complete app state so it can be restored on next launch."""
    state = {
        "profile": profile,
        "theme":   theme,
        "swatches": swatches,
    }
    with open(SESSION_STATE_FILE, "w", encoding="utf-8") as f:
        import json as _json
        _json.dump(state, f, indent=2)

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
        cycle = 1.0 / 20
        while self._running:
            with self._lock: v = self.value
            mag  = abs(v); sign = 1 if v >= 0 else -1
            act  = self.key_right if sign > 0 else self.key_left
            opp  = self.key_left  if sign > 0 else self.key_right
            if mag < 0.01 or not act:
                self._release_all(); time.sleep(cycle); continue
            opp_held = self._l_held if sign > 0 else self._r_held
            if opp_held and opp:
                try: self._kb.release(opp)
                except: pass
                if sign > 0: self._l_held = False
                else:        self._r_held = False
            # duty = axis-scaled speed, but never less than min_pulse when active
            # pulse sets the minimum hold time so even gentle inputs feel solid
            scaled    = mag * (self.speed / 100.0)
            min_duty  = self.pulse / 100.0
            duty      = max(min_duty, scaled)
            hold_t    = cycle * min(duty, 0.99)
            release_t = cycle * (1.0 - min(duty, 0.99))
            act_held  = self._r_held if sign > 0 else self._l_held
            if not act_held:
                try: self._kb.press(act)
                except: pass
                if sign > 0: self._r_held = True
                else:        self._l_held = True
            # Always report every active cycle to test display
            if self._key_callback:
                try: self._key_callback(act)
                except: pass
            time.sleep(hold_t)
            if duty < 0.99:
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
        self._offsets = {}    # (device_idx, axis_idx) -> resting value
        self._calibrated = set()  # set of device indices already calibrated

    def rescan(self):
        self.sticks = {}
        self._offsets = {}
        self._calibrated = set()
        pygame.joystick.quit(); pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            try:
                j = pygame.joystick.Joystick(i); j.init(); self.sticks[i] = j
            except: pass

    def get_names(self): return {i: j.get_name() for i,j in self.sticks.items()}

    def _calibrate(self, idx, j):
        """Sample current axis values as the resting baseline."""
        pygame.event.pump()
        try:
            for a in range(j.get_numaxes()):
                val = j.get_axis(a)
                # Only offset axes that rest far from zero (parked sliders/twist axes)
                # Normal stick axes should rest near 0 — don't offset those
                if abs(val) > 0.5:
                    self._offsets[(idx, a)] = val
        except: pass
        self._calibrated.add(idx)

    def read(self, idx):
        j = self.sticks.get(idx)
        if j is None: return []
        pygame.event.pump()
        try:
            if idx not in self._calibrated:
                self._calibrate(idx, j)
            raw = [j.get_axis(a) for a in range(j.get_numaxes())]
            # Subtract resting offset and rescale to keep -1..1 range
            corrected = []
            for a, v in enumerate(raw):
                off = self._offsets.get((idx, a), 0.0)
                if off != 0.0:
                    # Map from [off, sign(off)*1] -> [0, 1] then to [-1, 1]
                    # Axis parks at off (+1 or -1), moves toward -sign(off)
                    # Corrected: 0 at rest, -1 at opposite end
                    corrected_v = (v - off) / (1.0 + abs(off)) * -1.0
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
        self.key_callback = key_callback  # called with key_name when a key is pressed

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
        if name in self.pwm: self.pwm[name].set_value(v)

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
        self.live_val = 0.0
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
        """Normalised point -> pixel coords inside graph area."""
        _, _, gw, gh = self._geom()
        px = self.PAD_L + int(ax * gw)
        py = self.PAD_T + gh - int(ky * gh)
        return px, py

    def _px_to_pt(self, px, py):
        """Pixel coords -> normalised (axis_frac, kps_frac), clamped."""
        _, _, gw, gh = self._geom()
        ax = max(0.0, min(1.0, (px - self.PAD_L) / gw))
        ky = max(0.0, min(1.0, (self.PAD_T + gh - py) / gh))
        return ax, ky

    def _default_points(self):
        """7 control points at evenly spaced stick positions, default expo shape."""
        pts = []
        for ax in [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]:
            y = math.pow(ax, 1.8)   # pure shape 0..1, no speed scaling
            pts.append([ax, round(y, 4)])
        return pts

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

    def set_live(self, val):
        self.live_val = val; self.update()

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
        # Pulse floor line (yellow) — key is held at least this long every cycle
        pulse_kps = (self.pulse / 100.0) * self.MAX_KPS
        pulse_y   = self.PAD_T + gh - int((self.pulse / 100.0) * gh)
        p.setPen(QPen(_GC["pulse"], 1, Qt.PenStyle.DashLine))
        p.drawLine(self.PAD_L, pulse_y, self.PAD_L+gw, pulse_y)
        p.setFont(QFont(MONO,9)); p.setPen(QPen(_GC["pulse"]))
        p.drawText(self.PAD_L+4, pulse_y+2, 160, 12, Qt.AlignmentFlag.AlignLeft, f"pulse floor ({self.pulse}%  =  {pulse_kps:.1f}/s min)")
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

        # Live dot
        live = abs(self.live_val)
        if live > 0.001:
            if live < dz:
                kps_live = 0.0
            else:
                norm = (live - dz) / (1.0 - dz)
                kps_live = self._kps_at(norm)
            lx = self.PAD_L + int(live * gw)
            ly = self.PAD_T + gh - int(min(kps_live/self.MAX_KPS,1.0)*gh)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(100,255,150,60)))
            p.drawEllipse(lx-12,ly-12,24,24)
            p.setBrush(QBrush(_GC["live"])); p.drawEllipse(lx-5,ly-5,10,10)
            p.setFont(QFont(MONO,11,QFont.Weight.Bold)); p.setPen(QPen(_GC["live"]))
            p.drawText(lx+10, ly-14, 140, 16, Qt.AlignmentFlag.AlignLeft,
                       f"{kps_live:.1f} presses/sec")

        # Axis labels
        p.setFont(QFont(MONO,10)); p.setPen(QPen(_GC["label"]))
        p.drawText(self.PAD_L, self.PAD_T+gh+18, gw, 16,
            Qt.AlignmentFlag.AlignHCenter, "stick angle  →  (left = center,  right = full deflection)")
        p.setFont(QFont(MONO,9)); p.setPen(QPen(_GC["label"]))
        p.drawText(2, self.PAD_T, self.PAD_L-4, gh,
            Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop, "key\npress\n/sec")
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
        name_lbl.setStyleSheet("color:#ffffff;font-size:26px;font-weight:bold;letter-spacing:3px;")
        action_lbl=QLabel(f"  —  {self.action_label}")
        action_lbl.setStyleSheet("color:#c0b8e8;font-size:20px;")
        desc_lbl=QLabel(self.description)
        desc_lbl.setStyleSheet("color:#f0c030;font-size:16px;font-style:italic;")
        hdr.addWidget(name_lbl); hdr.addWidget(action_lbl); hdr.addStretch(); hdr.addWidget(desc_lbl)
        outer.addLayout(hdr)
        outer.addWidget(self._hline())

        # Step 1 — axis
        outer.addWidget(self._step_label("STEP 1","Which physical axis controls this movement?"))
        ai_row=QHBoxLayout(); ai_row.setSpacing(14)
        self._axis_display=QLabel(self._axis_text())
        self._axis_display.setStyleSheet(
            "background:rgba(8,4,20,200);border:1px solid rgba(200,180,255,100);"
            "border-top:1px solid rgba(255,255,255,40);border-radius:6px;"
            "color:#ffffff;font-size:24px;font-weight:bold;font-family:Courier New;"
            "padding:10px 20px;min-width:280px;")
        ai_row.addWidget(self._axis_display)
        detect_btn=QPushButton("DETECT  →  Move the axis then click its bar and press this")
        detect_btn.setStyleSheet(
            "background:rgba(255,200,40,15);border:1px solid rgba(255,200,40,120);"
            "border-top:1px solid rgba(255,255,255,30);border-radius:6px;"
            "color:#f0c030;font-family:Courier New;font-size:18px;padding:10px 20px;")
        detect_btn.clicked.connect(self._on_detect_click)
        ai_row.addWidget(detect_btn,stretch=1)
        not_used_btn=QPushButton("NOT  USED")
        not_used_btn.setFixedWidth(140)
        not_used_btn.setStyleSheet(
            "background:rgba(200,40,40,20);border:1px solid rgba(200,60,60,140);"
            "border-radius:6px;color:#ff8080;font-family:Courier New;font-size:18px;padding:10px;")
        not_used_btn.setToolTip("Disable this movement completely")
        not_used_btn.clicked.connect(self._mark_unused)
        ai_row.addWidget(not_used_btn)
        outer.addLayout(ai_row)
        self._detector=DetectorWidget(); self._detector.setVisible(False)
        self._detector.picked.connect(self._axis_picked)
        outer.addWidget(self._detector)
        outer.addWidget(self._hline())

        # Step 2+3 combined — left=keys+sliders, right=graph
        outer.addWidget(self._step_label("STEP 2 + 3","Keys and feel — side by side with the curve"))
        feel_outer=QHBoxLayout(); feel_outer.setSpacing(28)

        # ── Left column: keys + sliders + invert ──────────────
        left_col=QVBoxLayout(); left_col.setSpacing(14)

        # Keys (compact, stacked)
        keys_lbl=QLabel("KEYS")
        keys_lbl.setStyleSheet("color:#f0c030;font-size:18px;font-weight:bold;letter-spacing:3px;")
        left_col.addWidget(keys_lbl)

        def key_field_compact(direction, val, tip):
            row=QHBoxLayout(); row.setSpacing(8)
            lbl=QLabel(direction); lbl.setFixedWidth(200)
            lbl.setStyleSheet("color:#a098c8;font-size:16px;")
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
        clr_btn.setStyleSheet("background:rgba(200,40,40,20);border:1px solid rgba(200,60,60,140);border-radius:6px;color:#ff8080;font-size:17px;font-weight:bold;")
        clr_btn.clicked.connect(lambda:(self.key_left.setText(""),self.key_right.setText("")))
        clr_row.addWidget(clr_btn); clr_row.addStretch()
        left_col.addLayout(clr_row)

        left_col.addWidget(self._hline())

        # Sliders
        def sl_row(label,tip,lo,hi,val,fmt):
            col=QVBoxLayout(); col.setSpacing(4)
            lbl=QLabel(label); lbl.setStyleSheet("color:#6040a0;font-size:15px;font-weight:bold;")
            sl=NoScrollSlider(Qt.Orientation.Horizontal)
            sl.setRange(lo,hi); sl.setValue(val); sl.setFixedHeight(36); sl.setToolTip(tip)
            vl=QLabel(fmt(val)); vl.setStyleSheet("color:#b090e0;font-size:16px;font-weight:bold;min-width:160px;")
            sl.valueChanged.connect(lambda v:vl.setText(fmt(v)))
            r=QHBoxLayout(); r.addWidget(sl,stretch=1); r.addWidget(vl)
            col.addWidget(lbl); col.addLayout(r)
            return sl,col

        self.dz_sl,dz_col=sl_row("DEAD ZONE",
            "How far you move before it responds.\nIncrease if the stick drifts on its own.",
            0,50,self.cfg.get("deadzone",5),
            lambda v:f"{'none' if v==0 else 'tiny' if v<8 else 'small' if v<15 else 'medium' if v<30 else 'large'} ({v}%)")
        self.spd_sl,spd_col=sl_row("MAXIMUM SPEED",
            "How fast at full deflection.\nLower = gentler.  Higher = more aggressive.",
            1,100,self.cfg.get("speed",50),
            lambda v:f"{'very gentle' if v<20 else 'gentle' if v<40 else 'medium' if v<65 else 'fast'} ({v}%)")
        self.pls_sl,pls_col=sl_row("PULSE LENGTH",
            "Minimum time the key is held each cycle, regardless of stick position.\n"
            "Low = short taps — light, responsive, easy to stop.\n"
            "High = long holds — heavier, more momentum, harder to stop.\n"
            "Combines with Maximum Speed to shape the feel.",
            1,99,self.cfg.get("pulse",30),
            lambda v:f"{'tap' if v<15 else 'short' if v<35 else 'medium' if v<60 else 'long' if v<85 else 'full hold'} ({v}%)")
        left_col.addLayout(dz_col); left_col.addLayout(spd_col); left_col.addLayout(pls_col)

        inv_row=QHBoxLayout(); inv_row.setSpacing(12)
        inv_lbl=QLabel("DIRECTION:"); inv_lbl.setStyleSheet("color:#6040a0;font-size:15px;font-weight:bold;")
        self.inv_btn=QPushButton("NORMAL")
        self.inv_btn.setCheckable(True); self.inv_btn.setChecked(self.cfg.get("inverted",False))
        self.inv_btn.setText("INVERTED" if self.cfg.get("inverted",False) else "NORMAL")
        self.inv_btn.setFixedHeight(46); self.inv_btn.setMinimumWidth(160)
        self.inv_btn.clicked.connect(lambda:self.inv_btn.setText("INVERTED" if self.inv_btn.isChecked() else "NORMAL"))
        inv_row.addWidget(inv_lbl); inv_row.addWidget(self.inv_btn); inv_row.addStretch()
        left_col.addLayout(inv_row)
        left_col.addStretch()
        feel_outer.addLayout(left_col,stretch=2)

        # ── Right column: curve graph (square) ────────────────
        curve_col=QVBoxLayout(); curve_col.setSpacing(4)
        curve_lbl=QLabel("KEYPRESSES / SEC  vs  STICK ANGLE  —  drag handles to reshape,  double-click to reset")
        curve_lbl.setStyleSheet("color:#f0c030;font-size:12px;font-weight:bold;letter-spacing:2px;")
        self._curve=KeypressCurveWidget()
        self._curve.set_params(self.cfg.get("speed",50),self.cfg.get("deadzone",5),self.cfg.get("pulse",30))
        # Apply saved control points if present (must happen after set_params)
        init_pts = self.cfg.get("control_points", None)
        if init_pts:
            self._curve.set_control_points(init_pts)
        curve_col.addWidget(curve_lbl)
        curve_col.addWidget(self._curve,stretch=1)
        feel_outer.addLayout(curve_col,stretch=3)
        outer.addLayout(feel_outer)

        # Wire signals
        for w in [self.key_left,self.key_right]:
            w.textChanged.connect(lambda _:self.changed.emit())
        self.dz_sl.valueChanged.connect(self._on_feel_changed)
        self.spd_sl.valueChanged.connect(self._on_feel_changed)
        self.pls_sl.valueChanged.connect(lambda _: self.changed.emit())
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
        f=QFrame(); f.setFrameShape(QFrame.Shape.HLine); f.setStyleSheet("color:rgba(200,180,255,40);max-height:1px;"); return f

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

    def feed_live(self,val):
        self._curve.set_live(val)

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
    f.setStyleSheet("color:rgba(240,192,48,60);max-height:1px;margin:8px 0;"); return f

def section_heading(text):
    l=QLabel(text); l.setStyleSheet("color:#f0c030;font-size:18px;font-weight:bold;letter-spacing:6px;padding:14px 0 4px 2px;")
    return l

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
    },
    "Midnight": {
        "bg":   ["#000000", "#0a0a0a", "#111111", "#050505"],
        "text": ["#ffffff", "#f0c030", "#e0e0e0", "#c0c0c0"],
        "btn":  ["#1a1a1a", "#252525", "#303030", "#0f0f0f"],
    },
}

# Current swatch indices [bg_idx, text_idx, btn_idx] per theme
THEME_SWATCH = {t: [0, 0, 0] for t in THEME_PRESETS}

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
QScrollArea{{border:none;background:transparent;}}
QScrollBar:vertical{{background:{scroll_bg};width:16px;border:1px solid {accent_line};border-radius:8px;}}
QScrollBar::handle:vertical{{background:{btn};border-radius:6px;min-height:28px;margin:2px;}}
QScrollBar::handle:vertical:hover{{background:{btn_hover};}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
QScrollBar:horizontal{{background:{scroll_bg};height:16px;border:1px solid {accent_line};border-radius:8px;}}
QScrollBar::handle:horizontal{{background:{btn};border-radius:6px;min-width:28px;margin:2px;}}
QScrollBar::handle:horizontal:hover{{background:{btn_hover};}}
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;}}
QGroupBox{{border:1px solid {border};border-radius:10px;margin-top:18px;padding:20px 16px 16px 16px;background:{groupbox_bg};}}
QGroupBox::title{{subcontrol-origin:margin;left:16px;padding:0 8px;color:{text};font-size:16px;letter-spacing:3px;font-weight:bold;}}
QSlider::groove:horizontal{{height:6px;background:{groove};border-radius:3px;}}
QSlider::handle:horizontal{{background:{btn};width:20px;height:20px;margin:-7px 0;border-radius:10px;border:2px solid {btn_hover};}}
QSlider::handle:horizontal:hover{{background:{btn_hover};}}
QSlider::sub-page:horizontal{{background:{btn};border-radius:3px;}}
QLabel{{color:{text};font-size:15px;}}
QPushButton{{background:{btn};border:1px solid {btn_border};border-radius:6px;padding:6px 16px;color:{text};font-family:'{m}';font-size:15px;font-weight:bold;min-height:40px;}}
QPushButton:hover{{background:{btn_hover};border-color:{text};}}
QPushButton:checked{{background:{btn_hover};border-color:{text};}}
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
        self.setFixedSize(WIN_W,WIN_H)
        self._first_launch     = False  # must be initialised BEFORE _load_startup_profile
        self._startup_theme    = None   # restored from session if available
        self._startup_swatches = None
        self._reader = JoystickReader()
        self._worker = None
        self._cards  = {}
        self._live_bars = {}
        self._key_test = None
        self._key_queue = []
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
                    THEME_SWATCH[t] = sw
        self._theme_container.setStyleSheet(build_stylesheet())
        self._refresh_swatch_buttons()
        self._refresh_profiles()
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
        central.setStyleSheet("background:#080418;")
        main_layout=QVBoxLayout(central); main_layout.setSpacing(0); main_layout.setContentsMargins(0,0,0,0)

        # ═══ TITLE STRIP (top, separate from controls) ════════
        title_strip=QWidget()
        title_strip.setFixedHeight(52)
        title_strip.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #080420,stop:0.4 #0c0630,stop:0.6 #0c0630,stop:1 #080420);"
            "border-bottom:2px solid #1a0a50;")
        tsl=QHBoxLayout(title_strip); tsl.setContentsMargins(20,6,20,6); tsl.setSpacing(10)

        title_lbl=QLabel("STARBASE  HOTAS  BRIDGE")
        title_lbl.setStyleSheet("color:#ffffff !important;font-size:18px;font-weight:bold;letter-spacing:6px;")
        tsl.addWidget(title_lbl)
        tsl.addSpacing(20)

        # Theme selector
        theme_lbl=QLabel("THEME:")
        theme_lbl.setStyleSheet("color:#c0b0ff;font-size:12px;font-weight:bold;letter-spacing:2px;")
        tsl.addWidget(theme_lbl)
        self.theme_combo=NoScrollCombo(); self.theme_combo.setFixedHeight(30); self.theme_combo.setMinimumWidth(120)
        self.theme_combo.setStyleSheet("font-size:13px;min-height:30px;")
        for t in THEME_PRESETS: self.theme_combo.addItem(t)
        self.theme_combo.setCurrentText(CURRENT_THEME)
        self.theme_combo.currentTextChanged.connect(self._apply_theme)
        tsl.addWidget(self.theme_combo)

        tsl.addSpacing(16)

        # 3 swatch toggle buttons
        self._swatch_btns = []
        for i, label in enumerate(["BG", "TEXT", "BTN"]):
            lbl = QLabel(label)
            lbl.setStyleSheet("color:#9090c0;font-size:11px;font-weight:bold;")
            tsl.addWidget(lbl)
            btn = QPushButton("●")
            btn.setFixedHeight(30); btn.setFixedWidth(70)
            btn.setToolTip(f"Click to cycle {label} color through 4 preset shades")
            idx_capture = i
            btn.clicked.connect(lambda _, i=idx_capture: self._cycle_swatch(i))
            self._swatch_btns.append(btn)
            tsl.addWidget(btn)

        tsl.addStretch()
        self.poll_lbl=QLabel("")
        self.poll_lbl.setStyleSheet("color:rgba(180,160,255,120);font-size:12px;")
        tsl.addWidget(self.poll_lbl)
        main_layout.addWidget(title_strip)

        # ═══ PROFILE / CONTROL BAR ═════════════════════════════
        prof_bar=QWidget()
        prof_bar.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #0e0828,stop:1 #080618);"
            "border-bottom:1px solid #3a1a70;")
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
        self.profile_combo.setStyleSheet("font-size:17px;font-weight:bold;color:#d0a0ff;")
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
        root.addWidget(section_heading("STEP  0  —  CONNECT  YOUR  DEVICES"))
        root.addWidget(gap(8))
        dev_grp=QGroupBox("Tell the app which physical device is which")
        dev_l=QVBoxLayout(dev_grp); dev_l.setSpacing(12); dev_l.setContentsMargins(18,22,18,16)
        self.dev_combos={}
        for slot in DEVICE_SLOTS:
            row=QHBoxLayout(); row.setSpacing(14)
            lbl=QLabel(DEVICE_LABELS[slot]); lbl.setMinimumWidth(420); lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size:20px;font-weight:bold;color:#ffffff;")
            combo=NoScrollCombo(); combo.setFixedHeight(46)
            self.dev_combos[slot]=combo
            row.addWidget(lbl); row.addWidget(combo,stretch=1)
            dev_l.addLayout(row)
        scan_row=QHBoxLayout()
        scan_btn=QPushButton("SCAN  FOR  DEVICES"); scan_btn.setFixedHeight(46); scan_btn.setMinimumWidth(240)
        scan_btn.clicked.connect(self._scan_devices)
        scan_row.addWidget(scan_btn); scan_row.addStretch()
        dev_l.addLayout(scan_row)
        root.addWidget(dev_grp)
        root.addWidget(gap(14)); root.addWidget(hdivider()); root.addWidget(gap(14))

        # ═══ MOVEMENT CARDS ═══════════════════════
        root.addWidget(section_heading("STEP  1-3  —  CONFIGURE  EACH  MOVEMENT"))
        root.addWidget(gap(8))
        hint=QLabel("For each movement:  ① Pick which axis controls it  ② Set keyboard keys  ③ Tune the feel")
        hint.setStyleSheet("color:#a098c8;font-size:18px;padding:4px 0 12px 4px;")
        root.addWidget(hint)

        slot_map={"yaw":"stick","pitch":"stick","roll":"stick","thrust":"throttle","strafe_lr":"pedals","strafe_ud":"throttle","pedals":"pedals"}
        for mv_name in ["yaw","pitch","roll","thrust","strafe_lr","strafe_ud"]:
            mv_cfg=self.profile["movements"].get(mv_name,{})
            slot=slot_map[mv_name]; dev_lbl=DEVICE_LABELS[slot]
            card=MovementCard(mv_name,mv_cfg,dev_lbl)
            card.changed.connect(self._on_changed)
            self._cards[mv_name]=card
            root.addWidget(card); root.addWidget(gap(10))

        root.addWidget(hdivider()); root.addWidget(gap(14))

        # ═══ LIVE MONITOR ══════════════════════════
        root.addWidget(section_heading("LIVE  MONITOR"))
        root.addWidget(gap(8))
        mon_grp=QGroupBox("What the app is currently reading from your sticks")
        mon_l=QVBoxLayout(mon_grp); mon_l.setSpacing(6); mon_l.setContentsMargins(18,22,18,16)
        for mv in ["yaw","pitch","roll","thrust","strafe_lr","strafe_ud"]:
            lbl_data=MOVEMENT_LABELS[mv]
            bar=LiveBar(lbl_data[0])   # just the short name, no cut-off description
            self._live_bars[mv]=bar; mon_l.addWidget(bar)
        root.addWidget(mon_grp)
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

        # ═══ KEY REFERENCE ════════════════════════
        root.addWidget(section_heading("KEYBOARD  KEY  NAMES"))
        root.addWidget(gap(8))
        key_grp=QGroupBox("Type any of these names into the key fields above")
        key_l=QVBoxLayout(key_grp); key_l.setContentsMargins(18,22,18,16); key_l.setSpacing(8)
        for line in [
            "Single letters:   a  b  c  ...  z",
            "Modifier keys:    shift   ctrl   alt   space   tab   enter   esc",
            "Arrow keys:       up   down   left   right",
            "Function keys:    f1  f2  f3  f4  f5  f6  f7  f8  f9  f10  f11  f12",
            "Left/Right mods:  lshift   rshift   lctrl   rctrl   lalt   ralt",
            "Other:            backspace   delete   home   end   page_up   page_down",
        ]:
            l=QLabel(line); l.setStyleSheet("color:#c0b8e8;font-size:20px;padding:5px 0;"); key_l.addWidget(l)
        root.addWidget(key_grp)
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
        msg.setStyleSheet("color:#c0b8e8;font-size:16px;line-height:160%;")
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
        _GC = GRAPH_COLORS.get(CURRENT_THEME, GRAPH_COLORS["Space"])
        # Apply theme only to the scrollable content area, NOT the header
        self._theme_container.setStyleSheet(build_stylesheet())
        # Update swatch button labels to reflect current selections
        self._refresh_swatch_buttons()
        for w in self._theme_container.findChildren(QWidget):
            w.update()
        # Force repaint of custom-drawn widgets inside theme container
        self._theme_container.update()
        # Persist theme change to session
        try: save_session_state(self.profile, CURRENT_THEME, dict(THEME_SWATCH))
        except: pass

    def _cycle_swatch(self, idx):
        """Cycle swatch index (0=bg,1=text,2=btn) to next of 4 options."""
        sw = THEME_SWATCH[CURRENT_THEME]
        sw[idx] = (sw[idx] + 1) % 4
        self._apply_theme()

    def _refresh_swatch_buttons(self):
        if not hasattr(self, '_swatch_btns'): return
        p  = THEME_PRESETS[CURRENT_THEME]
        sw = THEME_SWATCH[CURRENT_THEME]
        labels = ["BG", "TEXT", "BTN"]
        for i, btn in enumerate(self._swatch_btns):
            color = p[["bg","text","btn"][i]][sw[i]]
            # Show current swatch color as button background
            is_dark_color = _hex_to_rgb(color)[0] < 128 if color.startswith('#') and len(color)==7 else True
            txt_col = "#ffffff" if is_dark_color else "#000000"
            btn.setStyleSheet(
                f"background:{color};color:{txt_col};border:2px solid rgba(255,255,255,120);"
                f"border-radius:4px;font-size:11px;font-weight:bold;min-height:24px;padding:0 8px;"
            )


    # ── Device scan ──────────────────────────────────────────
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
                    proc=process_axis(raw,mv.get("deadzone",5),mv.get("inverted",False),
                                      mv.get("control_points",None))

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
            _,pv=results.get(mv_name,(0,0))
            card.feed_live(pv)

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
