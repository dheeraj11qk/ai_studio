"""
main.py — AI Talking Human Video Generator
mode = "fast" → Wav2Lip (lip sync on video)
mode = "real" → LivePortrait (realistic face animation from image)
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── CONFIG ────────────────────────────────────────────────────────────────────
mode             = "fast"   # "fast" | "real"

face_image       = os.path.join(BASE_DIR, "input/face.jpg")
input_video      = os.path.join(BASE_DIR, "input/video.mp4")
input_audio      = os.path.join(BASE_DIR, "input/audio.wav")
wav2lip_out      = os.path.join(BASE_DIR, "output/wav2lip.mp4")
liveportrait_out = os.path.join(BASE_DIR, "output/liveportrait.mp4")
wav2lip_model    = os.path.join(BASE_DIR, "models/wav2lip_gan.pth")  # GAN = sharper lips
wav2lip_dir      = os.path.join(BASE_DIR, "wav2lip")
liveportrait_dir = os.path.join(BASE_DIR, "liveportrait")

WAV2LIP_REPO     = "https://github.com/Rudrabha/Wav2Lip"
WAV2LIP_MODEL_URL = "https://iiitaphyd-my.sharepoint.com/:u:/g/personal/radrabha_m_research_iiit_ac_in/Eb3LEzbfuKlJiR600lQWRxgBIY27JZg80f7V9jtFfbnu9A?e=TBGTAQ"

LIVEPORTRAIT_REPO = "https://github.com/KwaiVGI/LivePortrait"


# ── SETUP HELPERS ─────────────────────────────────────────────────────────────

def setup_wav2lip():
    """Clone Wav2Lip repo if not present."""
    if not os.path.exists(os.path.join(wav2lip_dir, "inference.py")):
        print("[setup] Cloning Wav2Lip...")
        subprocess.run(["git", "clone", WAV2LIP_REPO, wav2lip_dir], check=True)
        print("[setup] Wav2Lip cloned.")
    else:
        print("[setup] Wav2Lip already present.")

    if not os.path.exists(wav2lip_model):
        print("[setup] Wav2Lip model not found — downloading from HuggingFace...")
        try:
            from huggingface_hub import hf_hub_download
            hf_hub_download(
                repo_id="Nekochu/Wav2Lip",
                filename="wav2lip.pth",
                local_dir=os.path.join(BASE_DIR, "models")
            )
            print("[setup] Model downloaded.")
        except Exception as e:
            print(f"[setup] Auto-download failed: {e}")
            print(f"[setup] Download manually: https://huggingface.co/Nekochu/Wav2Lip/tree/main")
            print(f"[setup] Place at: {wav2lip_model}")
            sys.exit(1)


def setup_liveportrait():
    """Clone LivePortrait repo if not present."""
    if not os.path.exists(os.path.join(liveportrait_dir, "run.py")):
        print("[setup] Cloning LivePortrait...")
        subprocess.run(["git", "clone", LIVEPORTRAIT_REPO, liveportrait_dir], check=True)
        print("[setup] LivePortrait cloned.")
    else:
        print("[setup] LivePortrait already present.")


def check_inputs(*paths):
    for p in paths:
        if not os.path.exists(p):
            print(f"[main] ⚠️  Missing input file: {p}")
            sys.exit(1)


# ── RUN ───────────────────────────────────────────────────────────────────────

os.makedirs(os.path.join(BASE_DIR, "output"), exist_ok=True)

if mode == "fast":
    setup_wav2lip()
    check_inputs(input_video, input_audio)

    print("[main] Running Wav2Lip (fast lip sync)...")
    cmd = (
        f"python {wav2lip_dir}/inference.py "
        f"--checkpoint_path {wav2lip_model} "
        f"--face {input_video} "
        f"--audio {input_audio} "
        f"--outfile {wav2lip_out}"
    )
    print(f"[main] CMD: {cmd}")
    os.system(cmd)

    # sharpen the lip region with ffmpeg unsharp filter
    sharp_out = wav2lip_out.replace(".mp4", "_sharp.mp4")
    sharpen_cmd = (
        f"ffmpeg -y -i {wav2lip_out} "
        f"-vf 'unsharp=5:5:1.5:5:5:0.0' "
        f"-c:a copy {sharp_out}"
    )
    print("[main] Sharpening output...")
    os.system(sharpen_cmd)
    os.replace(sharp_out, wav2lip_out)
    print(f"[main] Done ✅  → {wav2lip_out}")

elif mode == "real":
    setup_liveportrait()
    check_inputs(face_image, input_audio)

    print("[main] Running LivePortrait (realistic face animation)...")
    cmd = (
        f"python {liveportrait_dir}/run.py "
        f"--source_image {face_image} "
        f"--driving_audio {input_audio} "
        f"--output {liveportrait_out}"
    )
    print(f"[main] CMD: {cmd}")
    os.system(cmd)
    print(f"[main] Done ✅  → {liveportrait_out}")

else:
    print(f"[main] Unknown mode: '{mode}'. Use 'fast' or 'real'.")
    sys.exit(1)
