"""
animate.py — runs inside Blender Python
Reads scene.json → drives RIG-rain bones + shape keys → renders PNG frames to temp
"""

import bpy
import json
import os
import sys
import math

# ── locate scene.json ─────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
SCENE_JSON  = os.path.join(SCRIPT_DIR, "scene.json")
TEMP_DIR    = "/tmp/3d_model_video_frames"
os.makedirs(TEMP_DIR, exist_ok=True)

# ── load scene data ───────────────────────────────────────────────────────────
with open(SCENE_JSON) as f:
    scene_data = json.load(f)

FPS      = scene_data.get("fps", 24)
DURATION = scene_data.get("duration", 1)
CLIPS    = scene_data.get("clips", [])

total_frames = int(DURATION * FPS)

# ── Blender scene setup ───────────────────────────────────────────────────────
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end   = total_frames
scene.render.fps  = FPS

rig = bpy.data.objects.get("RIG-rain")
if rig is None:
    raise RuntimeError("[animate] RIG-rain not found in scene")

# ── move model up so full body is visible ─────────────────────────────────────
rig.location.z = 0.3

# ── rest pose: hands straight down ───────────────────────────────────────────
hand_l = rig.pose.bones.get("IK-Hand.L")
hand_r = rig.pose.bones.get("IK-Hand.R")
for bone in [hand_l, hand_r]:
    if bone:
        bone.location.x = 0.0
        bone.location.y = 0.0
        bone.location.z = -0.25   # pull hands down below default
        bone.keyframe_insert(data_path="location", frame=1)

# ── import actions library ────────────────────────────────────────────────────
sys.path.insert(0, SCRIPT_DIR)
from actions import apply_action, apply_emotion

# ── process each clip ─────────────────────────────────────────────────────────
total_clips = len(CLIPS)
for idx, clip in enumerate(CLIPS):
    start_f = max(1, int(clip["start"] * FPS) + 1)
    end_f   = min(total_frames, int(clip["end"]   * FPS))
    action  = clip.get("action",  "idle")
    emotion = clip.get("emotion", "neutral")

    pct = int((idx / total_clips) * 100)
    print(f"[animate] {pct}% — clip {idx+1}/{total_clips}: action={action} emotion={emotion} frames={start_f}-{end_f}")

    apply_emotion(rig, scene, start_f, end_f, emotion)
    apply_action(rig, scene, start_f, end_f, action)

print("[animate] 100% — all clips keyframed")

# ── lighting ──────────────────────────────────────────────────────────────────
for obj in list(bpy.data.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)

key_light = bpy.data.lights.new(name="Key", type='AREA')
key_obj   = bpy.data.objects.new("Key", key_light)
bpy.context.collection.objects.link(key_obj)
key_obj.location = (1.5, -2.2, 2.2)
key_light.energy = 300
key_light.size   = 4

fill_light = bpy.data.lights.new(name="Fill", type='AREA')
fill_obj   = bpy.data.objects.new("Fill", fill_light)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = (-1.5, -2.2, 1.5)
fill_light.energy = 100
fill_light.size   = 4

world = bpy.data.worlds["World"]
world.use_nodes = True
bg_node = world.node_tree.nodes["Background"]
bg_node.inputs[0].default_value = (0.05, 0.05, 0.05, 1)
bg_node.inputs[1].default_value = 0.5

# ── camera (unchanged) ────────────────────────────────────────────────────────
if "Camera" in bpy.data.objects:
    cam = bpy.data.objects["Camera"]
else:
    cam_data = bpy.data.cameras.new(name="Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)

cam.location = (-0.3, -4.5, 1.2)   # pulled back + lowered to see full body
target    = bpy.data.objects["RIG-rain"]
body_center = target.location.copy()
body_center.z += 1.0               # aim at body center, not just head
direction = body_center - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ── render to temp PNG frames ─────────────────────────────────────────────────
scene.render.filepath = os.path.join(TEMP_DIR, "frame_")
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

print(f"[animate] Rendering {total_frames} frames to {TEMP_DIR} ...")

# render frame by frame with progress log
for f in range(1, total_frames + 1):
    scene.frame_set(f)
    scene.render.filepath = os.path.join(TEMP_DIR, f"frame_{f:04d}")
    bpy.ops.render.render(write_still=True)
    pct = int((f / total_frames) * 100)
    print(f"[animate] Rendering... {pct}% (frame {f}/{total_frames})")

print(f"[animate] Done — {total_frames} frames saved to {TEMP_DIR}")
