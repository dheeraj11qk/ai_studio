import os
import shutil
import uuid
import json
import math
from TTS.api import TTS
from pydub import AudioSegment

# =========================
# CONFIGURATION
# =========================
AUDIO_AI_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(os.path.dirname(AUDIO_AI_DIR), "temp", "segments")
OUTPUT_DIR = os.path.join(AUDIO_AI_DIR, "output")

class Audio_AI:
    """
    Modular Audio AI engine for generating voice tracks, sound effects, 
    and background music mixes based on production JSON tracks.
    """

    def __init__(
        self,
        speaker_wav: str = "voice_sample.wav",
        language: str = "en",
        model: str = "tts_models/multilingual/multi-dataset/xtts_v2",
    ):
        print(f"[Audio_AI] Initializing TTS with model: {model}")
        self.tts = TTS(model_name=model)
        
        # Resolve speaker_wav path (relative to this file)
        self.speaker_wav = speaker_wav if os.path.isabs(speaker_wav) else os.path.join(AUDIO_AI_DIR, speaker_wav)
        self.language = language
        print("[Audio_AI] Engine ready.")

    def generate_voice(self, voice_track: list, output_path: str = None, speed: float = 1.15) -> str:
        """
        Processes the 'voice' track from content.json and generates a single merged WAV file.
        Uses native XTTS speed parameter for higher quality than digital speedup.
        """
        if output_path is None:
            output_path = os.path.join(OUTPUT_DIR, "voice.wav")
            
        print(f"[Audio_AI] Generating voice track to {output_path} (Speed: {speed}x)...")
        
        audio_parts = []
        session_id = uuid.uuid4().hex
        tmp_dir = os.path.join(TEMP_DIR, session_id)
        os.makedirs(tmp_dir, exist_ok=True)

        try:
            for i, segment in enumerate(voice_track):
                seg_type = segment.get("type", "text")
                seg_id = segment.get("id", f"seg_{i}")
                
                if seg_type == "silence":
                    duration_ms = int(segment.get("duration", 0.5) * 1000)
                    print(f"[Audio_AI] [{seg_id}] Generating silence: {duration_ms}ms")
                    audio_parts.append(AudioSegment.silent(duration=duration_ms))
                
                else:
                    text = segment.get("text", "")
                    if not text:
                        continue
                        
                    tmp_path = os.path.join(tmp_dir, f"{seg_id}.wav")
                    emotion = segment.get("emotion", "neutral")
                    
                    print(f"[Audio_AI] [{seg_id}] Narrating ({emotion}) @ {speed}x: '{text[:50]}...'")
                    
                    # XTTS to file with NATIVE SPEED (High Quality)
                    self.tts.tts_to_file(
                        text=text,
                        speaker_wav=self.speaker_wav,
                        language=self.language,
                        file_path=tmp_path,
                        speed=speed
                    )
                    
                    seg_audio = AudioSegment.from_wav(tmp_path)
                    audio_parts.append(seg_audio)

            if not audio_parts:
                print("[Audio_AI] Warning: No audio segments were generated.")
                return ""

            print("[Audio_AI] Merging all segments...")
            final_audio = sum(audio_parts, AudioSegment.empty())
            
            final_output_path = os.path.abspath(output_path)
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
            final_audio.export(final_output_path, format="wav")
            
            print(f"[Audio_AI] Success! Voice track saved to: {final_output_path}")
            return final_output_path

        finally:
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def generate_master_mix(self, tracks: dict, output_path: str = None, character_voice: str = "communicator") -> str:
        """
        Creates a final master audio file by mixing Voice, SFX, and Music.
        Instantiates specific speeds based on the chosen character mindset.
        """
        if output_path is None:
            output_path = os.path.join(OUTPUT_DIR, "master_audio.wav")
            
        print(f"[Audio_AI] Generating Master Audio Mix to {output_path}...")

        # --- High Fidelity Voice Tuning ---
        # Map characters to optimal narrator speeds
        speed_map = {
            "funny": 1.25,      # Snappy, energetic delivery
            "teacher": 1.05,    # Clear and patient
            "communicator": 1.15 # Professional and engaging
        }
        v_speed = speed_map.get(character_voice.lower(), 1.15)
        
        # 1. Generate Voice Baseline
        voice_track = tracks.get("voice", [])
        voice_wav = os.path.join(OUTPUT_DIR, "voice.wav")
        voice_path = self.generate_voice(voice_track, output_path=voice_wav, speed=v_speed) 
        
        if not voice_path:
            return None
            
        master = AudioSegment.from_wav(voice_path)
        
        # 2. Add Music
        music_tracks = tracks.get("music", [])
        for music in music_tracks:
            filename = music.get("file")
            m_path = self._resolve_asset_path(filename)
            if not m_path or not os.path.exists(m_path):
                print(f"[Audio_AI] ❌ Warning: Music asset '{filename}' not found.")
                continue
                
            print(f"[Audio_AI] Layering music: {filename}")
            m_audio = AudioSegment.from_file(m_path)
            vol = music.get("volume", 0.4)
            # Correct math using math.log10
            m_audio = m_audio + (20 * math.log10(vol) if vol > 0 else -100)
            
            start_ms = int(music.get("start", 0.0) * 1000)
            if music.get("loop", True):
                while len(m_audio) < len(master):
                    m_audio += m_audio
            
            master = master.overlay(m_audio, position=start_ms)

        # 3. Add SFX
        sfx_tracks = tracks.get("sfx", [])
        for sfx in sfx_tracks:
            filename = sfx.get("file")
            s_path = self._resolve_asset_path(filename)
            if not s_path or not os.path.exists(s_path):
                print(f"[Audio_AI] ❌ Warning: SFX asset '{filename}' not found.")
                continue
                
            print(f"[Audio_AI] Triggering SFX: {filename}")
            s_audio = AudioSegment.from_file(s_path)
            vol = sfx.get("volume", 0.9)
            # Correct math using math.log10
            s_audio = s_audio + (20 * math.log10(vol) if vol > 0 else -100)
            
            start_ms = int(sfx.get("start", 0.0) * 1000)
            master = master.overlay(s_audio, position=start_ms)

        # 4. Save Master
        master.export(output_path, format="wav")
        print(f"[Audio_AI] ✅ SUCCESS! Master Mix saved to: {output_path}")
        return output_path

    def _resolve_asset_path(self, filename: str) -> str:
        """Find the full path from mapping with fuzzy matching."""
        mapping_path = os.path.join(AUDIO_AI_DIR, "music_assets.json")
        if not os.path.exists(mapping_path):
            return None
            
        with open(mapping_path) as f:
            mapping = json.load(f)

        if filename in mapping:
            return os.path.join(AUDIO_AI_DIR, mapping[filename])

        fn_lower = filename.lower()
        for k, v in mapping.items():
            if k.lower() == fn_lower:
                return os.path.join(AUDIO_AI_DIR, v)

        base_name = os.path.splitext(fn_lower)[0]
        for k, v in mapping.items():
            k_lower = k.lower()
            if base_name in k_lower or k_lower in base_name:
                print(f"[Audio_AI] 🔍 Fuzzy match: '{filename}' -> '{k}'")
                return os.path.join(AUDIO_AI_DIR, v)

        return None

if __name__ == "__main__":
    ai = Audio_AI(speaker_wav="voice_sample.wav")
    content_path = os.path.join(os.path.dirname(AUDIO_AI_DIR), "content_ai", "json", "content.json")
    if os.path.exists(content_path):
        with open(content_path) as f:
            data = json.load(f)
        ai.generate_master_mix(data.get("tracks", {}))
