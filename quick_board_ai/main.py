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

MODEL = "qwen2.5:7b"
VIDEO_TIMEOUT = 600
LLM_TIMEOUT = 300


# =========================
# LOGGER
# =========================
# ANSI color codes
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
MAGENTA= "\033[95m"
BLUE   = "\033[94m"
WHITE  = "\033[97m"

def _color_for(msg):
    if any(x in msg for x in ["✅", "done", "ready", "saved", "rendered", "collected", "complete"]):
        return GREEN
    if any(x in msg for x in ["❌", "🔥", "FAIL", "Error", "failed"]):
        return RED
    if any(x in msg for x in ["⚠️", "Skipped", "timeout"]):
        return YELLOW
    if any(x in msg for x in ["🤖", "Running Ollama", "Generating"]):
        return MAGENTA
    if any(x in msg for x in ["🎬", "Pipeline", "Merging", "Rendering"]):
        return CYAN
    if msg.startswith("$"):
        return DIM
    return WHITE

def log(msg):
    now = datetime.now().strftime('%H:%M:%S')
    color = _color_for(msg)
    print(f"{DIM}[{now}]{RESET}  {color}{msg}{RESET}", flush=True)

def log_sep():
    print(f"{DIM}{'─' * 55}{RESET}", flush=True)

def log_banner():
    print()
    print(f"{BOLD}{CYAN}╔{'═'*51}╗{RESET}")
    print(f"{BOLD}{CYAN}║{'  🎬  QUICK BOARD AI  •  VIDEO PIPELINE':^51}║{RESET}")
    print(f"{BOLD}{CYAN}╚{'═'*51}╝{RESET}")
    print()


# =========================
# RUN COMMAND
# =========================
def run(cmd, timeout=None):
    log(f"$ {cmd}")
    try:
        # Run and show output in terminal
        result = subprocess.run(
            cmd, shell=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            raise Exception(f"Command failed with exit code {result.returncode}")
        return ""
    except subprocess.TimeoutExpired:
        log(f"⏰ FAIL: Command timed out after {timeout}s: {cmd}")
        raise Exception("Command timeout")


# =========================
# QWEN CALL
# =========================
def run_qwen(prompt):
    log("🤖 Ollama Generating Video Scene (streaming)...")
    print("What will happen in video you need make:")

    import time
    start = time.time()
    output_chunks = []

    try:
        process = subprocess.Popen(
            ["ollama", "run", MODEL],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send prompt and close stdin
        process.stdin.write(prompt)
        process.stdin.close()

        print()  # blank line before stream starts
        # Stream output token by token
        for line in process.stdout:
            print(line, end="", flush=True)
            output_chunks.append(line)

            # Timeout check
            if time.time() - start > LLM_TIMEOUT:
                process.kill()
                log(f"\n⏰ FAIL: LLM timed out after {LLM_TIMEOUT}s")
                raise Exception("LLM timeout")

        process.wait()
        print()  # blank line after stream ends

        if process.returncode != 0:
            err = process.stderr.read()
            log(f"❌ LLM Error: {err}")
            raise Exception("Ollama failed")

        elapsed = round(time.time() - start, 1)
        log(f"✅ Model done in {elapsed}s")
        return "".join(output_chunks)

    except Exception as e:
        raise



# =========================
# GENERATE JSON
# =========================
def generate_json(user_prompt):
    # 1. Read the main prompt template
    with open(PROMPT_PATH) as f:
        template: str = f.read()

    # 2. Automatically read and combine ALL your examples
    examples_dir = os.path.join(BASE_DIR, "prompts", "manim", "examples")
    examples_combined = ""
    
    if os.path.exists(examples_dir):
        # Loop through the folder and read each .py file
        example_files = [f for f in os.listdir(examples_dir) if f.endswith(".py")]
        for filename in sorted(example_files):
            with open(os.path.join(examples_dir, filename)) as f:
                examples_combined += f"\n\n# --- EXAMPLES FROM {filename} ---\n"
                examples_combined += f.read()
        log(f"📚 Injected {len(example_files)} Manim examples into prompt")

    # 3. Inject absolute SVG/PNG paths for the AI to use
    svg_root = os.path.join(BASE_DIR, "media", "svgs")
    png_root = os.path.join(BASE_DIR, "media", "pngs")
    final_prompt: str = template.replace("{SVG_ROOT}", svg_root)
    final_prompt = final_prompt.replace("{PNG_ROOT}", png_root)
    final_prompt = final_prompt.replace("{MANIM_EXAMPLES}", examples_combined)
    final_prompt = final_prompt.replace("{USER_PROMPT}", user_prompt)

    # 4. Run the model with the full prompt
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

        # Fix trailing commas before ] or } (common phi3 quirk)
        import re
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

        data = json.loads(json_str)

    except Exception as e:
        log(f"❌ JSON Parse Error: {e}")
        # Log the raw content for debugging
        debug_content: str = str(content)
        log(f"📄 Raw LLM Output (first 100 chars): {debug_content[0:100]}...") # type: ignore
        raise

    log(f"✅ Scene loaded")
    return data


# =========================
# CREATE SCENE FILES
# =========================
def create_scene_files(data):
    # Handle if storyboard key is missing or is top level
    s = data.get("storyboard", data)
    
    scene_id = 1
    file_path = os.path.join(SCENES_DIR, f"scene_{scene_id}.py")
    raw_code = s.get("animation_engine", "")
    code: str = str(raw_code) if raw_code is not None else ""

    # Handle if AI accidentally returns a dictionary instead of string
    if isinstance(code, dict):
        code = code.get("code", code.get("animation_engine", str(code)))

    # Strip markdown backticks
    code = code.strip()
    if code.startswith("```"):
        code = code.split("\n", 1)[-1]
        if "```" in code:
            code = code.rsplit("```", 1)[0]
    code = code.strip()

    # Inject global visibility settings at the top
    global_setup = """
from manim import *
# Global visibility fixes
config.background_color = BLACK
SVGMobject.set_default(color=WHITE, stroke_width=2)
Text.set_default(color=WHITE)
"""
    
    # Ensure imports are present but replaced by our custom global setup
    if "from manim import *" in code:
        code = code.replace("from manim import *", global_setup)
    else:
        code = global_setup + "\n" + code

    with open(file_path, "w") as f:
        f.write(code)

    log(f"✅ Scene file created")


# =========================
# SETUP FOLDERS
# =========================
def setup_folders():
    # Create directories for results and data
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

    # Reset temp folder for rendering
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    # Delete old final video if exists
    if os.path.exists(OUTPUT_VIDEO):
        os.remove(OUTPUT_VIDEO)

    os.makedirs(CLIPS_DIR, exist_ok=True)
    os.makedirs(SCENES_DIR, exist_ok=True)


# =========================
# RENDER SCENES
# =========================
def render_scenes(data):
    scene_id = 1 # We use a single scene now
    file = os.path.join(SCENES_DIR, f"scene_{scene_id}.py")

    log(f"▶ Rendering Scene {scene_id}...")
    cmd = f"manim -ql {file} Scene{scene_id} --media_dir {TEMP_DIR}"
    try:
        run(cmd)
    except Exception as e:
        log(f"⚠️ Scene {scene_id} failed: {e}")
    log("✅ Rendering complete")


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
        user_prompt = """
      A student walked toward a school.
He entered a bus and traveled to a university.
In the university, he met a teacher and studied a book.
After a long day, he went home and looked at the stars.
        """

        log_sep()
        log("🎬 Starting Pipeline...")
        log_sep()
        setup_folders()
        generate_json(user_prompt)
        log_sep()
        data = load_json()
        log_sep()
        create_scene_files(data)
        log_sep()
        render_scenes(data)
        log_sep()
        collect_clips()
        merge_videos()
        log_sep()
        log(f"🎬 Done! Video saved to output/final.mp4")

    except Exception as e:
        log_sep()
        log(f"🔥 Pipeline failed: {e}")

    finally:
        cleanup()

if __name__ == "__main__":
    main()