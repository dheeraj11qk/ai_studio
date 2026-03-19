import subprocess
from config import BLENDER_PATH, BLEND_FILE, SCRIPT_FILE

def run_blender():
    command = [
        BLENDER_PATH,
        BLEND_FILE,
        "--background",
        "--python",
        SCRIPT_FILE
    ]

    subprocess.run(command)