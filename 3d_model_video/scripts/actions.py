"""
actions.py
Animation + emotion library for RIG-rain.
Includes: hand IK, head FK, blink, spine sway, shoulder shrug, finger curl, lipsync.
"""

import math
import bpy

FPS = 24

# ── Emotion → shape key values ────────────────────────────────────────────────
EMOTIONS = {
    "happy":     {"Smile.L": 0.85, "Smile.R": 0.85, "EyelidsClose.L": 0.1,   "EyelidsClose.R": 0.1},
    "neutral":   {"Smile.L": 0.0,  "Smile.R": 0.0,  "EyelidsClose.L": 0.0,   "EyelidsClose.R": 0.0},
    "sad":       {"Smile.L": 0.0,  "Smile.R": 0.0,  "EyebrowsDown.L": 0.6,   "EyebrowsDown.R": 0.6},
    "surprised": {"Smile.L": 0.3,  "Smile.R": 0.3,  "EyelidsClose.L": -0.3,  "EyelidsClose.R": -0.3},
    "thinking":  {"Smile.L": 0.1,  "Smile.R": 0.1,  "EyebrowsTogether.L": 0.5, "EyebrowsTogether.R": 0.5},
}


def _set_shape_key(name: str, value: float, frame: int):
    """Set a shape key by name across all meshes and keyframe it."""
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            key = obj.data.shape_keys.key_blocks.get(name)
            if key:
                key.value = value
                key.keyframe_insert(data_path="value", frame=frame)


def apply_emotion(rig, scene, start_f: int, end_f: int, emotion: str):
    values = EMOTIONS.get(emotion, EMOTIONS["neutral"])
    for name, v in values.items():
        _set_shape_key(name, v, start_f)
        _set_shape_key(name, v, end_f)


def apply_action(rig, scene, start_f: int, end_f: int, action: str):
    hand_l = rig.pose.bones.get("IK-Hand.L")
    hand_r = rig.pose.bones.get("IK-Hand.R")
    head   = rig.pose.bones.get("HNG-Head")
    total  = max(end_f - start_f, 1)

    for i, frame in enumerate(range(start_f, end_f + 1)):
        scene.frame_set(frame)
        t = i / total
        p = t * math.pi * 2

        if action == "idle":
            _idle(hand_l, hand_r, head, t, p, frame)
        elif action == "wave":
            _wave(hand_l, hand_r, head, t, p, frame)
        elif action == "talk":
            _talk(hand_l, hand_r, head, t, p, frame)
            _lipsync(frame)
        elif action == "nod":
            _nod(hand_l, hand_r, head, t, p, frame)
        elif action == "point":
            _point(hand_l, hand_r, head, t, p, frame)
        elif action == "shrug":
            _shrug(hand_l, hand_r, head, t, p, frame)
        elif action == "think":
            _think(hand_l, hand_r, head, t, p, frame)

        # blink every ~72 frames (3 sec), 3-frame blink
        _blink(frame)

        # subtle spine sway on every action
        _spine_sway(frame, t)

        for bone in [hand_l, hand_r, head]:
            if bone:
                bone.keyframe_insert(data_path="location")
                bone.keyframe_insert(data_path="rotation_euler")


# ── Blink ─────────────────────────────────────────────────────────────────────
def _blink(frame: int):
    """Blink every 24 frames (1 sec), 3-frame close/open."""
    cycle = frame % 24
    if cycle in (0, 4):
        v = 0.0   # open
    elif cycle in (1, 3):
        v = 0.5   # half close
    elif cycle == 2:
        v = 1.0   # fully closed
    else:
        v = 0.0
    _set_shape_key("EyelidsClose.L", v, frame)
    _set_shape_key("EyelidsClose.R", v, frame)


# ── Spine sway ────────────────────────────────────────────────────────────────
def _spine_sway(frame: int, t: float):
    """Subtle breathing/sway via Spine_Fwd shape key."""
    value = 0.04 * math.sin(frame * 0.15)
    _set_shape_key("Spine_Fwd", max(0.0, value), frame)


# ── Finger curl helpers ───────────────────────────────────────────────────────
FINGER_KEYS_L = ["Finger_Index1.L", "Finger_Index2.L", "Finger_Middle1.L", "Finger_Ring1.L", "Finger_Pinky1.L"]
FINGER_KEYS_R = ["Finger_Index1.R", "Finger_Index2.R", "Finger_Middle1.R", "Finger_Ring1.R", "Finger_Pinky1.R"]

def _curl_fingers(side: str, value: float, frame: int):
    keys = FINGER_KEYS_L if side == "L" else FINGER_KEYS_R
    for k in keys:
        _set_shape_key(k, value, frame)


# ── Action implementations ────────────────────────────────────────────────────

def _idle(hl, hr, hd, t, p, frame):
    if hl:
        hl.location.x =  0.01 * math.sin(p * 0.5)
        hl.location.z = -0.25 + 0.01 * math.sin(p * 0.3)
    if hr:
        hr.location.x =  0.01 * math.sin(p * 0.5 + 1)
        hr.location.z = -0.25 + 0.01 * math.sin(p * 0.3 + 0.5)
    if hd:
        hd.rotation_euler[0] = 0.02 * math.sin(p * 0.4)
    # fingers relaxed (slight curl)
    _curl_fingers("L", 0.2, frame)
    _curl_fingers("R", 0.2, frame)


def _wave(hl, hr, hd, t, p, frame):
    if hl:
        hl.location.x = 0.3 + 0.15 * math.sin(p * 2)
        hl.location.z = 0.25 + 0.1  * math.sin(p * 2 + 0.5)
    if hr:
        hr.location.x = 0.02 * math.sin(p)
        hr.location.z = -0.25 + 0.02 * math.sin(p * 0.7)
    if hd:
        hd.rotation_euler[2] = 0.08 * math.sin(p)
    # wave hand: fingers open
    _curl_fingers("L", 0.0, frame)
    _curl_fingers("R", 0.2, frame)
    # shoulder shrug on wave side
    _set_shape_key("Shoulder_Down.L", 0.0, frame)


def _talk(hl, hr, hd, t, p, frame):
    if hl:
        hl.location.x = 0.05 * math.sin(p * 0.8)
        hl.location.z = -0.15 + 0.04 * math.sin(p * 0.6)
    if hr:
        hr.location.x = 0.05 * math.sin(p * 0.8 + 1)
        hr.location.z = -0.15 + 0.04 * math.sin(p * 0.6 + 0.5)
    if hd:
        hd.rotation_euler[0] = 0.04 * math.sin(p * 0.7)
        hd.rotation_euler[2] = 0.03 * math.sin(p * 0.5)
    _curl_fingers("L", 0.15, frame)
    _curl_fingers("R", 0.15, frame)


def _nod(hl, hr, hd, t, p, frame):
    if hd:
        hd.rotation_euler[0] = 0.15 * math.sin(p * 1.5)
        hd.rotation_euler[2] = 0.02 * math.sin(p)
    if hl:
        hl.location.x = 0.01 * math.sin(p)
        hl.location.z = -0.25
    if hr:
        hr.location.x = 0.01 * math.sin(p + 1)
        hr.location.z = -0.25
    _curl_fingers("L", 0.2, frame)
    _curl_fingers("R", 0.2, frame)


def _point(hl, hr, hd, t, p, frame):
    if hr:
        hr.location.x = -0.2 - 0.05 * math.sin(p * 0.5)
        hr.location.z =  0.15 + 0.03 * math.sin(p * 0.5)
    if hl:
        hl.location.x = 0.02 * math.sin(p)
        hl.location.z = -0.25
    if hd:
        hd.rotation_euler[2] = -0.05 * math.sin(p * 0.5)
    # pointing hand: index finger extended, others curled
    _curl_fingers("R", 0.0, frame)
    _set_shape_key("Finger_Middle1.R", 0.8, frame)
    _set_shape_key("Finger_Ring1.R",   0.8, frame)
    _set_shape_key("Finger_Pinky1.R",  0.8, frame)
    _curl_fingers("L", 0.2, frame)


def _shrug(hl, hr, hd, t, p, frame):
    shrug_z = 0.2 * math.sin(p * math.pi)
    if hl:
        hl.location.x =  0.15
        hl.location.z =  shrug_z
    if hr:
        hr.location.x = -0.15
        hr.location.z =  shrug_z
    if hd:
        hd.rotation_euler[0] = 0.05 * math.sin(p * math.pi)
    # shoulders up via shape key
    shrug_val = 0.8 * math.sin(p * math.pi)
    _set_shape_key("Shoulder_Down.L", max(0, -shrug_val), frame)
    _set_shape_key("Shoulder_Down.R", max(0, -shrug_val), frame)
    _curl_fingers("L", 0.3, frame)
    _curl_fingers("R", 0.3, frame)


def _think(hl, hr, hd, t, p, frame):
    if hr:
        hr.location.x = -0.05 + 0.01 * math.sin(p)
        hr.location.z =  0.3  + 0.01 * math.sin(p * 0.5)
    if hl:
        hl.location.x = 0.02 * math.sin(p)
        hl.location.z = -0.25
    if hd:
        hd.rotation_euler[2] = 0.06 * math.sin(p * 0.4)
    _curl_fingers("R", 0.4, frame)
    _curl_fingers("L", 0.2, frame)


def _lipsync(frame: int):
    # stronger open/close so it's clearly visible
    value = max(0.0, 0.7 * math.sin(frame * 0.6) + 0.2 * math.sin(frame * 1.3))
    _set_shape_key("mouth_open", value, frame)
    # also animate LipsWide for more expression
    wide = max(0.0, 0.3 * math.sin(frame * 0.4))
    _set_shape_key("LipsWide.L", wide, frame)
    _set_shape_key("LipsWide.R", wide, frame)
