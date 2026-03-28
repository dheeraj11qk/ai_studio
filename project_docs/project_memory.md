# Project Memory - AI Studio

## Overview
AI Studio is a modular, multi-modal AI content generation platform designed for automated video, audio, and animation creation. It leverages specialized AI modules for different media types, orchestrating them into complex pipelines.

## Project Components

### 1. **metaVisionMacApp** (Main Orchestrator)
- **Repo/Dir**: `agent_ai/`, `vision_ai/`, `audio_ai/`, `content_ai/`, `video_edit/`, `meta_ai/`
- **Purpose**: End-to-end video generation (Story → Voice → Video Segments → Merge).
- **Core Tech**: 
    - `agent_ai`: SQLAlchemy-based persistence for long-running jobs.
    - `meta_ai`: Swift-based macOS browser app for Meta AI video generation.
    - `audio_ai`: XTTS v2 for voice narration.
    - `video_edit`: MoviePy for stitching and merging.

### 2. **quick_board_ai** (Current Focus 🚀)
- **Repo/Dir**: `quick_board_ai/`
- **Purpose**: Dynamic "whiteboard-style" animations using [Manim](https://www.manim.community/).
- **Tools**:
    - `main.py`: The Manim rendering engine.
    - `make_video.py`: A CLI tool that uses **qwen2.5:7b** to generate scripts (`script.json`) from a topic, which are then rendered into videos automatically.
- **Workflow**: `python make_video.py "your topic"` → Script Gen → SVG Mapping → Manim Render → `output/DynamicWhiteboard.mp4`.

### 3. **talking_human_ai**
- **Purpose**: Digital human video generation with two modes:
    - `fast`: **Wav2Lip** for quick lip-syncing on existing video.
    - `real`: **LivePortrait** for realistic face animation from a static image.
- **Components**: Cloned repos for Wav2Lip and LivePortrait with specialized model loaders in `main.py`.

### 4. **image_ai**
- **Purpose**: Fast high-quality image generation.
- **Core Tech**: StabilityAI's **SD-Turbo** optimized for Mac (MPS). Includes integrated upscaling (2x) and subtle color enhancement.

### 5. **visual_ai**
- **Purpose**: Modular animation engine.
- **Architecture**: Separates `scene_builder` (frame logic) and `animator` (rendering). Designed for custom procedural animations.

### 6. **3d_model_video**
- **Purpose**: Scripted 3D animations via **Blender**.
- **Workflow**: Uses `blender_runner.py` for headless rendering of Blender scenes.

## In Progress
- **Active Focus**: `quick_board_ai` — perfecting whiteboard animations using various media, images, and Manim-based effects.
- **Goal**: Create a seamless pipeline for educational and explainer whiteboard videos.

## Technology Stack
- **Languages**: Python, Swift (macOS app), JavaScript.
- **Libraries**: MoviePy, Manim, SQLAlchemy, PyTorch (MPS), Diffusers, OpenCV.
- **Tools**: Blender, FFmpeg, SQLite.

## Workflow Patterns
- Each module (`*_ai`) is designed to be standalone but integrable into the `agent_ai` pipeline.
- Input files are typically placed in `input/` and results in `output/` folders within each module.

---
*Last Updated: 2026-03-28*
