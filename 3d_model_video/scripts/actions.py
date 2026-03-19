"""
actions.py
Animation + emotion library for RIG-rain.
Called by animate.py — runs inside Blender Python.
"""

import math

FPS = 24

# ── Emotion → shape key values ────────────────────────────────────────────────
EMOTIONS = {
    "happy":    {"Smile.L": 0.85, "Smile.R": 0.85, "EyelidsClose.L": 0.1,  "EyelidsClose.R": 0.1},
    "neutral":  {"Smile.L": 0.0,  "Smile.R": 0.0,  "EyelidsClose.L": 0.0,  "EyelidsClose.R": 0.0},
    "sad":      {"Smile.L": 0.0,  "Smile.R": 0.0,  "EyebrowsDown.L": 0.6,  "EyebrowsDown.R": 0.6},
    "surprised":{"Smile.L": 0.3,  "Smile.R": 0.3,  "EyelidsClose.L": -0.3, "EyelidsClose.R": -0.3},
    "thinking": {"Smile.L": 0.1,  "Smile.R": 0.1,  "EyebrowsTogether.L": 0.5, "EyebrowsTogether.R": 0.5},
}

def apply_emotion(rig, scene, start_f: int, end_f: int, emotion: str):
    """Keyframe shape keys for an emotion across a frame range."""
    values = EMOTIONS.get(emotion, EMOTIONS["neutral"])
    for obj in __import__('bpy').data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            for key in obj.data.shape_keys.key_blocks:
                if key.name in values:
                    v = values[key.name]
                    key.value = v
                    key.keyframe_insert(data_path="value", frame=start_f)
                    key.keyframe_insert(data_path="value", frame=end_f)


def apply_action(rig, scene, start_f: int, end_f: int, action: str):
    """Drive bones for a named action across a frame range."""
    hand_l = rig.pose.bones.get("IK-Hand.L")
    hand_r = rig.pose.bones.get("IK-Hand.R")
    head   = rig.pose.bones.get("HNG-Head")
    total  = max(end_f - start_f, 1)

    for i, frame in enumerate(range(start_f, end_f + 1)):
        scene.frame_set(frame)
        t = i / total  # 0.0 → 1.0
        p = t * math.pi * 2  # full cycle

        if action == "idle":
            _idle(hand_l, hand_r, head, t, p)

        elif action == "wave":
            _wave(hand_l, hand_r, head, t, p)

        elif action == "talk":
            _talk(hand_l, hand_r, head, t, p)
            _lipsync(scene, frame, t)

        elif action == "nod":
            _nod(hand_l, hand_r, head, t, p)

        elif action == "point":
            _point(hand_l, hand_r, head, t, p)

        elif action == "shrug":
            _shrug(hand_l, hand_r, head, t, p)

        elif action == "think":
            _think(hand_l, hand_r, head, t, p)

        # keyframe bones
        for bone in [hand_l, hand_r, head]:
            if bone:
                bone.keyframe_insert(data_path="location")
                bone.keyframe_insert(data_path="rotation_euler")


# ── Action implementations ────────────────────────────────────────────────────

def _idle(hl, hr, hd, t, p):
    # hands hang straight down with tiny breathing sway
    if hl:
        hl.location.x =  0.01 * math.sin(p * 0.5)
        hl.location.z = -0.25 + 0.01 * math.sin(p * 0.3)
    if hr:
        hr.location.x =  0.01 * math.sin(p * 0.5 + 1)
        hr.location.z = -0.25 + 0.01 * math.sin(p * 0.3 + 0.5)
    if hd:
        hd.rotation_euler[0] = 0.02 * math.sin(p * 0.4)


def _wave(hl, hr, hd, t, p):
    if hl:
        hl.location.x = 0.3 + 0.15 * math.sin(p * 2)
        hl.location.z = 0.25 + 0.1  * math.sin(p * 2 + 0.5)
    if hr:
        hr.location.x = 0.02 * math.sin(p)
        hr.location.z = 0.02 * math.sin(p * 0.7)
    if hd:
        hd.rotation_euler[2] = 0.08 * math.sin(p)


def _talk(hl, hr, hd, t, p):
    if hl:
        hl.location.x = 0.05 * math.sin(p * 0.8)
        hl.location.z = -0.15 + 0.04 * math.sin(p * 0.6)
    if hr:
        hr.location.x = 0.05 * math.sin(p * 0.8 + 1)
        hr.location.z = -0.15 + 0.04 * math.sin(p * 0.6 + 0.5)
    if hd:
        hd.rotation_euler[0] = 0.04 * math.sin(p * 0.7)
        hd.rotation_euler[2] = 0.03 * math.sin(p * 0.5)


def _nod(hl, hr, hd, t, p):
    if hd:
        hd.rotation_euler[0] = 0.15 * math.sin(p * 1.5)
        hd.rotation_euler[2] = 0.02 * math.sin(p)
    if hl:
        hl.location.x = 0.01 * math.sin(p)
    if hr:
        hr.location.x = 0.01 * math.sin(p + 1)


def _point(hl, hr, hd, t, p):
    # right hand extends forward/up as a point gesture
    if hr:
        hr.location.x = -0.2 - 0.05 * math.sin(p * 0.5)
        hr.location.z =  0.15 + 0.03 * math.sin(p * 0.5)
    if hl:
        hl.location.x = 0.02 * math.sin(p)
        hl.location.z = 0.01 * math.sin(p)
    if hd:
        hd.rotation_euler[2] = -0.05 * math.sin(p * 0.5)


def _shrug(hl, hr, hd, t, p):
    shrug_z = 0.2 * math.sin(p * math.pi)  # rises then falls
    if hl:
        hl.location.x =  0.15
        hl.location.z =  shrug_z
    if hr:
        hr.location.x = -0.15
        hr.location.z =  shrug_z
    if hd:
        hd.rotation_euler[0] = 0.05 * math.sin(p * math.pi)


def _think(hl, hr, hd, t, p):
    # right hand near chin
    if hr:
        hr.location.x = -0.05 + 0.01 * math.sin(p)
        hr.location.z =  0.3  + 0.01 * math.sin(p * 0.5)
    if hl:
        hl.location.x = 0.02 * math.sin(p)
        hl.location.z = 0.01 * math.sin(p)
    if hd:
        hd.rotation_euler[2] = 0.06 * math.sin(p * 0.4)


def _lipsync(scene, frame: int, t: float):
    """Animate mouth_open for talk action."""
    import bpy
    value = max(0.0, 0.4 * math.sin(frame * 0.55) + 0.1 * math.sin(frame * 1.1))
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            for key in obj.data.shape_keys.key_blocks:
                if key.name == "mouth_open":
                    key.value = value
                    key.keyframe_insert(data_path="value")
