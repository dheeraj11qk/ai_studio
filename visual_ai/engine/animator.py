"""
animator.py
Renders PIL frames to an H.264 MP4 via OpenCV + ffmpeg re-mux.
"""

import os
import subprocess
import numpy as np
import cv2

FPS = 24


def render(frames: list, out_path: str, fps: int = FPS) -> None:
    if not frames:
        print("[Animator] No frames to render.")
        return

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    tmp_path = out_path.replace(".mp4", "_raw.mp4")

    first  = frames[0].convert("RGB")
    w, h   = first.size
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_path, fourcc, fps, (w, h))

    for img in frames:
        rgb = np.array(img.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        writer.write(bgr)

    writer.release()

    # Re-mux to H.264 so QuickTime / macOS can play it
    subprocess.run([
        "ffmpeg", "-y", "-i", tmp_path,
        "-vcodec", "libx264", "-pix_fmt", "yuv420p",
        out_path
    ], check=True, capture_output=True)

    os.remove(tmp_path)
    print(f"[Animator] Saved -> {out_path}  ({len(frames)} frames @ {fps}fps)")
