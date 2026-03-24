"""
image_ai/main.py
Fast image generation using SD-Turbo (~2GB) on Mac MPS.
"""

import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image, ImageEnhance
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── CONFIG ────────────────────────────────────────────────────────────────────
prompt = (
    "a modern smartphone displaying a Flutter app with new UI features, "
    "clean minimal design, vibrant material design colors, code editor on laptop screen in background, "
    "tech workspace, professional product photo, soft natural lighting, sharp focus, photorealistic"
)
steps    = 4
out_file = os.path.join(OUTPUT_DIR, "output.png")

# ── LOAD ──────────────────────────────────────────────────────────────────────
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"[image_ai] Loading SD-Turbo on {device}...")

pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/sd-turbo",
    torch_dtype=torch.float32,
    use_safetensors=True
).to(device)

# ── GENERATE ──────────────────────────────────────────────────────────────────
print(f"[image_ai] Generating ({steps} steps)...")
result = pipe(
    prompt=prompt,
    num_inference_steps=steps,
    guidance_scale=0.0,
).images[0]

image = result.convert("RGB")

# mild natural color correction only — no heavy saturation boost
image = ImageEnhance.Color(image).enhance(1.2)      # subtle, keeps natural tones
image = ImageEnhance.Contrast(image).enhance(1.05)

image.save(out_file)

# upscale 2x
upscaled = image.resize((image.width * 2, image.height * 2), resample=Image.LANCZOS)
upscaled_file = out_file.replace(".png", "_2x.png")
upscaled.save(upscaled_file)
print(f"[image_ai] Saved    → {out_file}  ({image.width}x{image.height})")
print(f"[image_ai] Upscaled → {upscaled_file}  ({image.width*2}x{image.height*2})")
