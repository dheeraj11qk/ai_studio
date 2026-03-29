import os
import subprocess
import json
import re
import shutil
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "template.txt")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
SCENES_DIR = os.path.join(TEMP_DIR, "scenes")
CLIPS_DIR = os.path.join(TEMP_DIR, "clips")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "final.mp4")

MODEL = "qwen2.5:7b"
LLM_TIMEOUT = 300  # 5 minutes

# Colors for terminal
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


class QuickBoardAI:
    def __init__(self):
        self.output_path = OUTPUT_VIDEO
        self._setup_folders()

    def _log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}]  {msg}")

    def _log_sep(self):
        print("─" * 55)

    def _run_cmd(self, cmd, timeout=None):
        self._log(f"$ {cmd}")
        try:
            result = subprocess.run(
                cmd, shell=True, text=True, timeout=timeout
            )
            if result.returncode != 0:
                raise Exception(f"Command failed with exit code {result.returncode}")
            return ""
        except subprocess.TimeoutExpired:
            self._log(f"⏰ FAIL: Command timed out after {timeout}s: {cmd}")
            raise Exception("Command timeout")

    def _setup_folders(self):
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        if os.path.exists(OUTPUT_VIDEO):
            os.remove(OUTPUT_VIDEO)
            
        os.makedirs(CLIPS_DIR, exist_ok=True)
        os.makedirs(SCENES_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def _run_qwen(self, prompt):
        self._log("🤖 Ollama Generating Video Scene (streaming)...")
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

            process.stdin.write(prompt)
            process.stdin.close()

            print()
            for line in process.stdout:
                print(line, end="", flush=True)
                output_chunks.append(line)

                if time.time() - start > LLM_TIMEOUT:
                    process.kill()
                    self._log(f"\n⏰ FAIL: LLM timed out after {LLM_TIMEOUT}s")
                    raise Exception("LLM timeout")

            process.wait()
            print()

            if process.returncode != 0:
                raise Exception("Ollama failed")

            elapsed = round(time.time() - start, 1)
            self._log(f"✅ Model done in {elapsed}s")
            return "".join(output_chunks)

        except Exception as e:
            raise e

    def _generate_json(self, user_prompt):
        with open(PROMPT_PATH) as f:
            template = f.read()

        examples_dir = os.path.join(BASE_DIR, "prompts", "manim", "examples")
        examples_combined = ""
        
        if os.path.exists(examples_dir):
            example_files = [f for f in os.listdir(examples_dir) if f.endswith(".py")]
            for filename in sorted(example_files):
                with open(os.path.join(examples_dir, filename)) as f:
                    examples_combined += f"\n\n# --- EXAMPLES FROM {filename} ---\n"
                    examples_combined += f.read()
            self._log(f"📚 Injected {len(example_files)} Manim examples into prompt")

        svg_root = os.path.join(BASE_DIR, "media", "svgs")
        png_root = os.path.join(BASE_DIR, "media", "pngs")
        
        final_prompt = template.replace("{SVG_ROOT}", svg_root)
        final_prompt = final_prompt.replace("{PNG_ROOT}", png_root)
        final_prompt = final_prompt.replace("{MANIM_EXAMPLES}", examples_combined)
        final_prompt = final_prompt.replace("{USER_PROMPT}", user_prompt)

        raw_output = self._run_qwen(final_prompt)

        try:
            start_index = raw_output.find("{")
            end_index = raw_output.rfind("}")
            if start_index != -1 and end_index != -1:
                clean_output = raw_output[start_index : end_index + 1]
            else:
                clean_output = raw_output
        except:
            clean_output = raw_output

        json_path = os.path.join(BASE_DIR, "json", "data.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w") as f:
            f.write(clean_output)
        
        self._log("✅ Clean JSON saved")
        return json.loads(re.sub(r",\s*([}\]])", r"\1", clean_output))

    def _process_rendering(self, data):
        # Create Scene File
        s = data.get("storyboard", data)
        scene_id = 1
        file_path = os.path.join(SCENES_DIR, f"scene_{scene_id}.py")
        raw_code = s.get("animation_engine", "")
        code = str(raw_code)

        if isinstance(code, dict):
            code = code.get("code", code.get("animation_engine", str(code)))

        code = code.strip()
        if code.startswith("```"):
            code = code.split("\n", 1)[-1]
            if "```" in code:
                code = code.rsplit("```", 1)[0]
        code = code.strip()

        global_setup = """
from manim import *
# Global visibility fixes
config.background_color = BLACK
SVGMobject.set_default(color=WHITE, stroke_width=2)
Text.set_default(color=WHITE)
"""
        if "from manim import *" in code:
            code = code.replace("from manim import *", global_setup)
        else:
            code = global_setup + "\n" + code

        with open(file_path, "w") as f:
            f.write(code)
        self._log("✅ Scene file created")

        # Render
        self._log(f"▶ Rendering Scene {scene_id}...")
        cmd = f"manim -ql {file_path} Scene{scene_id} --media_dir {TEMP_DIR}"
        self._run_cmd(cmd)
        self._log("✅ Rendering complete")

    def _merge_videos(self):
        self._log("📂 Collecting clips...")
        clips = []
        for root, _, files in os.walk(TEMP_DIR):
            for file in files:
                if file.endswith(".mp4") and "Scene" in file:
                    clips.append(os.path.abspath(os.path.join(root, file)))

        if not clips:
            raise Exception("No rendered clips found")

        list_path = os.path.join(TEMP_DIR, "list.txt")
        with open(list_path, "w") as f:
            for clip in sorted(clips):
                f.write(f"file '{clip}'\n")

        self._log("🎬 Merging videos...")
        cmd = f"ffmpeg -y -f concat -safe 0 -i {list_path} -c copy {OUTPUT_VIDEO}"
        self._run_cmd(cmd)
        self._log(f"✅ Final video saved to: {OUTPUT_VIDEO}")

    def gen_video(self, user_prompt):
        """Main method to generate a video from a prompt. Returns result path."""
        try:
            self._log_sep()
            self._log("🎬 Starting QuickBoard AI Pipeline...")
            self._log_sep()

            # 1. Setup
            self._setup_folders()

            # 2. Generate JSON from LLM
            data = self._generate_json(user_prompt)
            self._log_sep()

            # 3. Process Code & Render
            self._process_rendering(data)
            self._log_sep()

            # 4. Merge
            self._merge_videos()
            self._log_sep()

            self._log("🎬 Done! Video generation successful.")
            
            # 5. Cleanup
            if os.path.exists(TEMP_DIR):
                shutil.rmtree(TEMP_DIR)
                self._log("🧹 Temp cleaned")

            return self.output_path

        except Exception as e:
            self._log(f"🔥 Pipeline failed: {e}")
            if os.path.exists(TEMP_DIR):
                shutil.rmtree(TEMP_DIR)
            return None


# =========================
# CLI ENTRY POINT
# =========================
if __name__ == "__main__":
    ai = QuickBoardAI()
    
    sample_prompt = """
    A student walked toward a school.
    He entered a bus and traveled to a university.
    In the university, he met a teacher and studied a book.
    After a long day, he went home and looked at the stars.
    """
    
    video_path = ai.gen_video(sample_prompt)
    if video_path:
        print(f"\n🚀 SUCCESS! Video location: {video_path}")
    else:
        print("\n❌ FAILED to generate video.")