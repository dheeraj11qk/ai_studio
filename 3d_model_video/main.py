"""
main.py — orchestrates Blender render + ffmpeg assembly
Usage: python main.py [scene_json_path] [output_video_path]
"""

import subprocess
import sys
import os
import glob
import shutil

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR    = "/tmp/3d_model_video_frames"
SCRIPT_FILE = os.path.join(BASE_DIR, "scripts", "animate.py")
BLEND_FILE  = os.path.join(BASE_DIR, "scene", "rain_v332", "rain_v3.2.blend")
BLENDER     = "/Applications/Blender.app/Contents/MacOS/Blender"
OUT_DIR     = os.path.join(BASE_DIR, "output")

scene_json  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "scripts", "scene.json")
output_mp4  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(OUT_DIR, "video.mp4")

os.makedirs(OUT_DIR,  exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ── Step 1: Blender render ────────────────────────────────────────────────────
print("[main] Step 1/2 — Running Blender render...")

result = subprocess.run(
    [BLENDER, BLEND_FILE, "--background", "--python", SCRIPT_FILE],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)

# stream Blender output, filter for our progress lines
for line in result.stdout.splitlines():
    if line.startswith("[animate]"):
        print(line)

if result.returncode != 0:
    print("[main] Blender failed. Full output:")
    print(result.stdout)
    sys.exit(1)

# ── Step 2: ffmpeg assemble ───────────────────────────────────────────────────
frames = sorted(glob.glob(os.path.join(TEMP_DIR, "frame_*.png")))
if not frames:
    print("[main] No frames found in temp dir — render may have failed.")
    sys.exit(1)

print(f"[main] Step 2/2 — Assembling {len(frames)} frames → {output_mp4}")

subprocess.run([
    "ffmpeg", "-y",
    "-framerate", "24",
    "-i", os.path.join(TEMP_DIR, "frame_%04d.png"),
    "-vcodec", "libx264",
    "-pix_fmt", "yuv420p",
    output_mp4
], check=True, capture_output=True)

# cleanup temp frames
shutil.rmtree(TEMP_DIR, ignore_errors=True)

print(f"[main] Done ✅  Video saved → {output_mp4}")
