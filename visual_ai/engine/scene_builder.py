"""
scene_builder.py
Reads a scene JSON and produces a list of (frame, duration_ms) tuples.
"""

import json
import os
from PIL import Image

from engine.mapper import get_pose_path, get_walk_cycle
from engine.layout import make_background, place_character, W, H

FPS = 24


def _load(path: str) -> Image.Image | None:
    if not os.path.exists(path):
        print(f"[SceneBuilder] Missing: {path}")
        return None
    return Image.open(path).convert("RGBA")


def build_frames(scene_path: str) -> list[Image.Image]:
    """
    Parse scene JSON → list of PIL frames at FPS rate.
    """
    with open(scene_path) as f:
        scene = json.load(f)

    bg_style = scene.get("background", "outdoor")
    bg       = make_background(bg_style)
    scale    = scene.get("character_scale", 3.5)
    frames   = []

    for clip in scene["clips"]:
        character = clip.get("character", "Player")
        action    = clip.get("action", "idle")
        duration  = clip.get("duration", 2.0)
        x_start   = clip.get("x_start", W // 4)
        x_end     = clip.get("x_end",   x_start)
        total_f   = int(duration * FPS)

        if action == "walk":
            walk_paths = get_walk_cycle(character)
            walk_imgs  = [_load(p) for p in walk_paths]
            walk_imgs  = [i for i in walk_imgs if i]
            for i in range(total_f):
                t     = i / max(total_f - 1, 1)
                x     = int(x_start + (x_end - x_start) * t)
                pose  = walk_imgs[i % len(walk_imgs)]
                frame = place_character(bg, pose, x, scale, bg_style)
                frames.append(frame)
        else:
            pose_path = get_pose_path(character, action)
            pose_img  = _load(pose_path)
            if pose_img is None:
                pose_img = _load(get_pose_path(character, "idle"))
            x = int((x_start + x_end) / 2)
            for _ in range(total_f):
                frame = place_character(bg, pose_img, x, scale, bg_style)
                frames.append(frame)

    return frames
