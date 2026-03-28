import os
import json
import shutil
import subprocess
from datetime import datetime

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMP_DIR = os.path.join(BASE_DIR, "temp")
CLIPS_DIR = os.path.join(TEMP_DIR, "clips")
SCENES_DIR = os.path.join(TEMP_DIR, "scenes")

JSON_PATH = os.path.join(BASE_DIR, "json", "data.json")
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "template.txt")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "final.mp4")
LOG_FILE = os.path.join(BASE_DIR, "pipeline.log")

MODEL = "qwen2.5:7b"
VIDEO_TIMEOUT = 600 # 10 Minutes for heavy renders/merges
LLM_TIMEOUT = 180   # Seconds for JSON generation


# =========================
# LOGGER
# =========================
def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


# =========================
# RUN COMMAND
# =========================
def run(cmd, timeout=None):
    log(f"$ {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            log(f"❌ ERROR:\n{result.stderr}")
            raise Exception(f"Command failed: {cmd}")
        return result.stdout
    except subprocess.TimeoutExpired:
        log(f"⏰ FAIL: Command timed out after {timeout}s: {cmd}")
        raise Exception("Command timeout")


# =========================
# QWEN CALL
# =========================
def run_qwen(prompt):
    log("🤖 Running Qwen model...")

    try:
        result = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=None
        )
        if result.returncode != 0:
            log(f"❌ LLM Error: {result.stderr}")
            raise Exception("Qwen failed")
        return result.stdout
    except subprocess.TimeoutExpired:
        log(f"⏰ FAIL: LLM timed out after {LLM_TIMEOUT}s")
        raise Exception("LLM timeout")


# =========================
# GENERATE JSON
# =========================
def generate_json(user_prompt):
    log("📄 Generating JSON...")

    with open(PROMPT_PATH) as f:
        template: str = f.read()

    final_prompt: str = template.replace("{USER_PROMPT}", user_prompt)

    raw_output: str = run_qwen(final_prompt)

    # Clean the output BEFORE saving: find the first '{' and last '}'
    try:
        start_index: int = raw_output.find("{")
        end_index: int = raw_output.rfind("}")
        
        if start_index != -1 and end_index != -1:
            clean_output: str = raw_output[start_index : end_index + 1] # type: ignore
        else:
            clean_output = raw_output
    except:
        clean_output = raw_output

    # Save clean JSON
    with open(JSON_PATH, "w") as f:
        f.write(clean_output)

    log("✅ Clean JSON saved")


# =========================
# LOAD JSON
# =========================
def load_json():
    log("📦 Loading JSON...")

    with open(JSON_PATH) as f:
        content = f.read().strip()

    # Find the JSON part even if there's text/markdown around it
    try:
        start_index: int = content.find("{")
        end_index: int = content.rfind("}")
        
        if start_index == -1 or end_index == -1:
            raise ValueError("No JSON object found in output")
            
        # Explicit slicing to satisfy interpreter
        json_str: str = content[start_index : end_index + 1] # type: ignore
        data = json.loads(json_str)

    except Exception as e:
        log(f"❌ JSON Parse Error: {e}")
        # Log the raw content for debugging
        debug_content: str = str(content)
        log(f"📄 Raw LLM Output (first 100 chars): {debug_content[0:100]}...") # type: ignore
        raise

    log(f"✅ Loaded {len(data['scenes'])} scenes")
    return data


# =========================
# CREATE SCENE FILES
# =========================
def create_scene_files(data):
    log("🎬 Creating scene files...")

    for s in data["scenes"]:
        file_path = os.path.join(SCENES_DIR, f"scene_{s['scene']}.py")
        raw_code = s.get("videoCode", "")
        code: str = str(raw_code) if raw_code is not None else ""

        # Handle if AI accidentally returns a dictionary instead of string
        if isinstance(code, dict):
            code = code.get("code", code.get("videoCode", str(code)))

        # Safety net: Strip markdown backticks if AI included them inside the JSON string
        code = code.strip()
        if code.startswith("```"):
            # Remove starting ```json or ```
            code = code.split("\n", 1)[-1]
            if "```" in code:
                code = code.rsplit("```", 1)[0]
        code = code.strip()

        # Extra safety net: Handle if AI wraps code in extra JSON string structure
        if isinstance(code, str) and '"code": "' in code:
            try:
                extracted = code.split('"code": "', 1)[1]
                if extracted.endswith('"}'):
                    extracted = extracted.rsplit('"}', 1)[0]
                code = extracted.replace('\\n', '\n').replace('\\"', '"')
                log(f"⚠️ Fixed nested JSON in Scene {s['scene']}")
            except:
                pass

        # Ensure imports are present
        if "from manim import *" not in code:
            code = "from manim import *\n\n" + code

        with open(file_path, "w") as f:
            f.write(code)

    log("✅ Scene files created")


# =========================
# SETUP FOLDERS
# =========================
def setup_folders():
    log("⚙️ Setting up folders...")

    # Create directories for results and data
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

    # Reset temp folder for rendering
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    
    os.makedirs(CLIPS_DIR, exist_ok=True)
    os.makedirs(SCENES_DIR, exist_ok=True) # Inside temp now

    log("✅ Folders ready")


# =========================
# RENDER SCENES
# =========================
def render_scenes(data):
    log("🎥 Rendering scenes...")

    for s in data["scenes"]:
        scene_id = s["scene"]
        file = os.path.join(SCENES_DIR, f"scene_{scene_id}.py")

        log(f"▶ Scene {scene_id}")

        # Removed -p flag to avoid opening the video clip
        cmd = f"manim -ql {file} Scene{scene_id} --media_dir {TEMP_DIR}"
        run(cmd)

    log("✅ All scenes rendered")


# =========================
# COLLECT CLIPS
# =========================
def collect_clips():
    log("📂 Collecting clips...")
    clips = []
    
    # Search for MP4 files in the temp directory
    for root, _, files in os.walk(TEMP_DIR):
        if "PartialMovieFiles" in root: continue # Skip partials
        
        for f in files:
            if f.endswith(".mp4"):
                full_path = os.path.abspath(os.path.join(root, f))
                clips.append(full_path)

    # Sort clips numerically by scene number (e.g., Scene1.mp4, Scene2.mp4...)
    def get_scene_num(path):
        filename = os.path.basename(path)
        # Extract digits from 'Scene1.mp4'
        nums = "".join([c for c in filename if c.isdigit()])
        return int(nums) if nums else 0

    clips.sort(key=get_scene_num)

    list_path = os.path.join(TEMP_DIR, "list.txt")
    with open(list_path, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    log(f"✅ {len(clips)} clips collected in {list_path}")


# =========================
# MERGE VIDEOS
# =========================
def merge_videos():
    log("🎬 Merging videos...")

    cmd = f"ffmpeg -f concat -safe 0 -i {TEMP_DIR}/list.txt -c copy {OUTPUT_VIDEO}"
    run(cmd)

    log(f"✅ Final video: {OUTPUT_VIDEO}")


# =========================
# CLEANUP
# =========================
def cleanup():
    log("🧹 Cleaning temp...")

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    log("✅ Temp removed")


# =========================
# MAIN PIPELINE
# =========================
def main():
    try:
        user_prompt = "Mango grow geourny video 1 minutes"
        log(f"🎬 Starting Pipeline for: '{user_prompt}'")

        setup_folders()
        generate_json(user_prompt)

        data = load_json()

        create_scene_files(data)
        render_scenes(data)

        collect_clips()
        merge_videos()
        log("🎬 Pipeline finished successfully!")

    except Exception as e:
        log(f"🔥 Pipeline failed: {e}")

    finally:
        cleanup()


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()