"""
mapper.py
Maps character names and pose names to actual asset file paths.
"""

import os

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_DIR   = os.path.join(BASE_DIR, "assets", "characters", "PNG")

# Available characters
CHARACTERS = ["Player", "Adventurer", "Female", "Soldier", "Zombie"]

# Pose name → filename (same for all characters, just different prefix)
POSE_MAP = {
    "idle":    "idle",
    "walk1":   "walk1",
    "walk2":   "walk2",
    "jump":    "jump",
    "fall":    "fall",
    "duck":    "duck",
    "talk":    "talk",
    "cheer1":  "cheer1",
    "cheer2":  "cheer2",
    "hurt":    "hurt",
    "stand":   "stand",
    "action1": "action1",
    "action2": "action2",
    "climb1":  "climb1",
    "climb2":  "climb2",
    "skid":    "skid",
    "slide":   "slide",
    "back":    "back",
    "hang":    "hang",
    "hold1":   "hold1",
    "hold2":   "hold2",
    "kick":    "kick",
    "swim1":   "swim1",
    "swim2":   "swim2",
}


def get_pose_path(character: str, pose: str) -> str:
    """Return full path to a pose PNG for a given character."""
    char = character.capitalize()
    prefix = char.lower()
    filename = f"{prefix}_{POSE_MAP.get(pose, 'idle')}.png"
    return os.path.join(CHAR_DIR, char, "Poses", filename)


def get_walk_cycle(character: str) -> list[str]:
    """Return [walk1, walk2] paths for walk animation."""
    return [get_pose_path(character, "walk1"),
            get_pose_path(character, "walk2")]
