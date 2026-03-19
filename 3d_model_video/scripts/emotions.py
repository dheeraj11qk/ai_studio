"""
emotions.py
Maps emotion names to shape key values.
Call apply_emotion(rig, emotion, frame) to keyframe an emotion.
"""

# emotion → {shape_key_name: value}
EMOTION_MAP = {
    "happy":   {"Smile.L": 0.8, "Smile.R": 0.8, "EyelidsClose.L": 0.1, "EyelidsClose.R": 0.1},
    "neutral": {"Smile.L": 0.0, "Smile.R": 0.0, "EyelidsClose.L": 0.0, "EyelidsClose.R": 0.0},
    "sad":     {"Smile.L": 0.0, "Smile.R": 0.0, "EyebrowsTogether.L": 0.5, "EyebrowsTogether.R": 0.5},
    "excited": {"Smile.L": 1.0, "Smile.R": 1.0, "EyelidsClose.L": 0.0, "EyelidsClose.R": 0.0,
                "EyebrowsDown.L": 0.0, "EyebrowsDown.R": 0.0},
    "thinking":{"Smile.L": 0.1, "Smile.R": 0.1, "EyebrowsTogether.L": 0.3, "EyebrowsTogether.R": 0.3},
}


def apply_emotion(objects, emotion: str, frame: int):
    """Apply emotion shape keys to all meshes at given frame."""
    preset = EMOTION_MAP.get(emotion, EMOTION_MAP["neutral"])
    for obj in objects:
        if obj.type != 'MESH' or not obj.data.shape_keys:
            continue
        keys = {k.name: k for k in obj.data.shape_keys.key_blocks}
        for key_name, value in preset.items():
            if key_name in keys:
                keys[key_name].value = value
                keys[key_name].keyframe_insert(data_path="value", frame=frame)
