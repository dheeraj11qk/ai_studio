"""
main.py — entry point
Usage: python main.py [scene_file]
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from engine.scene_builder import build_frames
from engine.animator import render

def run(scene_file: str = "scenes/test_scene.json"):
    scene_path = os.path.join(BASE_DIR, scene_file)
    out_path   = os.path.join(BASE_DIR, "output", "video.mp4")

    print(f"[Main] Building frames from: {scene_file}")
    frames = build_frames(scene_path)
    print(f"[Main] {len(frames)} frames built")

    render(frames, out_path)

if __name__ == "__main__":
    scene = sys.argv[1] if len(sys.argv) > 1 else "scenes/test_scene.json"
    run(scene)
