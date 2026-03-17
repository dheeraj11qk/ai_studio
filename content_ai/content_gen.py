"""
content_gen.py
All content generation functions using Ollama (qwen2.5:7b).
Falls back to static data if Ollama is unavailable.
"""

import requests
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_ai.prompt_builder import (
    parse_duration,
    segment_count,
    title_prompt,
    description_prompt,
    story_prompt,
    video_prompts_prompt,
)

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"


# ── Ollama core ──────────────────────────────────────────────────────────────

def _ollama(prompt: str, num_predict: int = 300) -> str:
    """Send a prompt to Ollama and return the text response."""
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.8, "num_predict": num_predict},
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


# ── Fallbacks ────────────────────────────────────────────────────────────────

def _fallback_title(topic: str) -> str:
    return f"The Amazing {topic.title()} Story"

def _fallback_description(topic: str) -> str:
    return (
        f"Join us on an incredible journey featuring {topic}! "
        "Watch as the story unfolds with excitement, heart, and unforgettable moments. "
        "Don't forget to like and subscribe for more amazing stories!"
    )

def _fallback_story(topic: str) -> str:
    return (
        f"It was a quiet evening when the story of {topic} began. "
        "Every moment felt alive with possibility and wonder. "
        "Challenges arose, but courage and determination led the way. "
        "In the end, everything came together beautifully. "
        "And so the adventure concluded, leaving smiles all around."
    )

def _fallback_prompts(topic: str, count: int) -> list[str]:
    """Generate simple topic-based fallback prompts when Ollama is unavailable."""
    templates = [
        "Generate a video of {topic}, wide establishing shot, cinematic lighting, soft illustration style, warm pastel palette, highly detailed",
        "Generate a video of {topic}, close-up shot, dramatic lighting, rich colors, storybook illustration style, cinematic atmosphere",
        "Generate a video of {topic}, tracking shot, golden hour lighting, vibrant colors, soft illustration style, detailed background",
        "Generate a video of {topic}, low-angle shot, atmospheric lighting, deep background, illustration style with warm tones, cinematic depth of field",
        "Generate a video of {topic}, aerial shot, bright cheerful lighting, colorful environment, soft storybook illustration style, 8K detail",
    ]
    return [templates[i % len(templates)].format(topic=topic) for i in range(count)]


# ── Public functions ─────────────────────────────────────────────────────────

def get_title(topic: str) -> str:
    """Generate a short YouTube title."""
    try:
        return _ollama(title_prompt(topic), num_predict=50)
    except Exception as e:
        print(f"[ContentGen] Ollama unavailable for title ({e}), using fallback.")
        return _fallback_title(topic)


def get_description(topic: str) -> str:
    """Generate a YouTube description."""
    try:
        return _ollama(description_prompt(topic), num_predict=150)
    except Exception as e:
        print(f"[ContentGen] Ollama unavailable for description ({e}), using fallback.")
        return _fallback_description(topic)


def get_story(topic: str) -> str:
    """Generate a ~50 word children's story."""
    try:
        return _ollama(story_prompt(topic), num_predict=200)
    except Exception as e:
        print(f"[ContentGen] Ollama unavailable for story ({e}), using fallback.")
        return _fallback_story(topic)


def get_video_prompts(topic: str, user_request: str = "1 min video") -> list[str]:
    """
    Parse user_request for duration, calculate segment count,
    generate that many detailed cinematic prompts via Ollama.
    """
    duration_sec = parse_duration(user_request)
    count = segment_count(duration_sec)
    print(f"[ContentGen] Duration: {duration_sec}s → {count} video segments")

    try:
        raw = _ollama(video_prompts_prompt(topic, count), num_predict=count * 120)
        start = raw.find("[")
        end   = raw.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found in response")
        prompts = json.loads(raw[start:end])
        if isinstance(prompts, list) and len(prompts) > 0:
            # pad with cycled prompts if Ollama returned fewer than needed
            while len(prompts) < count:
                prompts.append(prompts[len(prompts) % len(prompts)])
            return prompts[:count]
        raise ValueError("Empty or invalid JSON array")
    except Exception as e:
        print(f"[ContentGen] Ollama unavailable for video prompts ({e}), using fallback.")
        return _fallback_prompts(topic, count)


# ── CLI test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    topic       = "man working in office late night"
    user_request = "1 min video"

    print("\n=== TITLE ===")
    print(get_title(topic))

    print("\n=== DESCRIPTION ===")
    print(get_description(topic))

    print("\n=== STORY ===")
    print(get_story(topic))

    prompts = get_video_prompts(topic, user_request)
    print(f"\n=== VIDEO PROMPTS ({len(prompts)}) ===")
    for i, p in enumerate(prompts, 1):
        print(f"\n{i}. {p}")
