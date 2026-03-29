import os
import requests
import json
import re
import subprocess
import time
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "content_template.txt")
JSON_DIR = os.path.join(BASE_DIR, "json")

MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Helper to parse duration (Moved from prompt_builder)
def parse_duration(user_request: str) -> int:
    text = user_request.lower()
    duration = 60
    m = re.search(r'(\d+)\s*min', text)
    if m:
        duration = int(m.group(1)) * 60
    else:
        m = re.search(r'(\d+)\s*sec', text)
        if m:
            duration = int(m.group(1))
        else:
            m = re.search(r'(\d+)\s*words?', text)
            if m:
                duration = int(int(m.group(1)) * 0.5)
    return max(20, min(duration, 300))

class ContentGenAI:
    def __init__(self):
        os.makedirs(JSON_DIR, exist_ok=True)
        self.audio_root = os.path.abspath(os.path.join(BASE_DIR, "..", "audio_ai", "music"))
        self.asset_map = {} # Maps simple filename -> full path for AI resolution

    def _get_available_assets(self):
        """Scans the audio_ai directory and updates the asset map."""
        self.asset_map = {}
        music_names = []
        sfx_names = []
        
        bg_dir = os.path.join(self.audio_root, "background")
        sfx_dir = os.path.join(self.audio_root, "sound_effects")

        # 1. Background Music
        if os.path.exists(bg_dir):
            for f in os.listdir(bg_dir):
                if f.endswith(('.mp3', '.wav')):
                    full_path = f"music/background/{f}"
                    self.asset_map[f] = full_path
                    music_names.append(f)
        
        # 2. Sound Effects (Recursive)
        if os.path.exists(sfx_dir):
            for root, _, files in os.walk(sfx_dir):
                for f in files:
                    if f.endswith(('.mp3', '.wav')):
                        full_path = os.path.relpath(os.path.join(root, f), os.path.join(self.audio_root, ".."))
                        self.asset_map[f] = full_path
                        sfx_names.append(f)

        # 3. Save mapping to a physical JSON file for user reference
        assets_json_path = os.path.join(os.path.dirname(self.audio_root), "music_assets.json")
        try:
            with open(assets_json_path, "w") as f:
                json.dump(self.asset_map, f, indent=2)
            self._log(f"📋 Updated asset mapping file at {assets_json_path}")
        except Exception as e:
            self._log(f"⚠️ Failed to save music_assets.json: {e}")

        return ", ".join(music_names), ", ".join(sfx_names)

    def _resolve_paths(self, data):
        """Walks through the JSON data and replaces filenames with full mapped paths."""
        if "tracks" not in data:
            return data
            
        # Resolve Music
        for item in data["tracks"].get("music", []):
            name = item.get("file", "")
            if name in self.asset_map:
                item["file"] = self.asset_map[name]
        
        # Resolve SFX
        for item in data["tracks"].get("sfx", []):
            name = item.get("file", "")
            if name in self.asset_map:
                item["file"] = self.asset_map[name]
                
        return data

    def _log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [ContentGenAI] {msg}")

    def _ollama(self, prompt: str, num_predict: int = 2000) -> str:
        """Send a prompt to Ollama and stream the response to the terminal."""
        self._log("🤖 Ollama Generating Production Script (streaming)...")
        
        import time
        start = time.time()
        output_chunks = []

        try:
            # Using Popen for streaming output
            process = subprocess.Popen(
                ["ollama", "run", MODEL],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send the prompt
            process.stdin.write(prompt)
            process.stdin.close()

            # Stream the output
            for line in process.stdout:
                print(line, end="", flush=True)
                output_chunks.append(line)

                # Safety timeout (10 minutes)
                if time.time() - start > 600:
                    process.kill()
                    self._log("❌ ERROR: Generation timed out")
                    return ""

            process.wait()
            print() # New line after stream

            if process.returncode != 0:
                self._log(f"❌ ERROR: Ollama returned {process.returncode}")
                return ""

            elapsed = round(time.time() - start, 1)
            return "".join(output_chunks)

        except Exception as e:
            self._log(f"❌ ERROR: Streaming failed ({e})")
            return ""

    def generate(self, topic: str, duration_str: str = "5 sec", lang: str = "en", character: str = "communicator"):
        """
        Generates full YouTube story content and saves it to a JSON file.
        Supports 'en', 'hi', 'hinglish'.
        Characters: 'funny', 'teacher', 'communicator'.
        """
        duration_sec = parse_duration(duration_str)
        self._log(f"Starting generation: {topic} ({duration_sec}s) | Lang: {lang} | Mode: {character}")
        
        # 1. Load Main Template
        if not os.path.exists(PROMPT_PATH):
            raise FileNotFoundError(f"Template not found at {PROMPT_PATH}")
        with open(PROMPT_PATH) as f:
            template = f.read()

        # 2. Load Character Psychology (Voice Over Mind)
        mind_path = os.path.join(BASE_DIR, "prompts", "voice_overs_mind", f"{character}.txt")
        if not os.path.exists(mind_path):
            mind_path = os.path.join(BASE_DIR, "prompts", "voice_overs_mind", "communicator.txt")
        
        with open(mind_path) as f:
            mind_instructions = f.read()

        # 3. Get Available Assets
        music_names, sfx_names = self._get_available_assets()
        
        # 4. Prepare Prompt
        lang_context = "Hindi (हिन्दी script)" if lang.lower() == "hi" else "English"
        
        # --- ULTIMATE STRIKE INSTRUCTIONS ---
        strict_constraints = f"""
        ### 🛑 ABSOLUTE SYSTEM CONSTRAINTS 🛑
        1. VOICE LANGUAGE: All 'voice' track narration text MUST be in {lang_context}.
        2. VISUALS TRACK (CRITICAL): EVERY field inside the 'visuals' track (description, search_key_word) MUST remain in PURE ENGLISH. 
           - DO NOT translate the visual track. Keep it English to ensure our search engine (Pexels) works.
        3. DYNAMIC PACING: Set 'duration' for 'silence' segments based on the Mind instructions.
        """

        final_prompt = template.replace("{TOPIC}", topic)
        final_prompt = final_prompt.replace("{DURATION}", str(duration_sec))
        final_prompt = final_prompt.replace("{AVAILABLE_MUSIC}", music_names if music_names else "None")
        final_prompt = final_prompt.replace("{AVAILABLE_SFX}", sfx_names if sfx_names else "None")

        # Inject Mind & Language
        final_prompt = f"{strict_constraints}\n\n{final_prompt}"
        final_prompt += f"\n\n### VOICE OVER MIND & PACING (Role: {character.upper()}):\n{mind_instructions}"
        final_prompt += f"\n\nIMPORTANT: THE NARRATION, TITLE, AND DESCRIPTION MUST BE IN {lang_context}."
        
        # 5. Call AI
        raw_output = self._ollama(final_prompt)
        
        # 6. Extract and Parse JSON
        try:
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found in AI response")
            
            data = json.loads(raw_output[start:end])
            
            # 7. RESOLVE PATHS: Swap simple names for full directory paths
            data = self._resolve_paths(data)
            
            # 8. Save to JSON folder
            filename = "content.json"
            save_path = os.path.join(JSON_DIR, filename)
            
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            self._log(f"✅ Success! Resolved paths and saved to {save_path}")
            return data

        except Exception as e:
            self._log(f"❌ Failed to parse or save JSON: {e}")
            return None

# =========================
# CLI ENTRY POINT
# =========================
if __name__ == "__main__":
    ai = ContentGenAI()
    
    # Example Test
    topic = "a brave cat fighting a dragon"
    ai.generate(topic, "30 sec")
