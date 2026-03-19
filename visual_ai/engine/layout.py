"""
layout.py
Handles placing characters and objects on a scene canvas.
"""

from PIL import Image

W, H = 1280, 720   # output resolution


def make_background(style: str = "outdoor") -> Image.Image:
    """Simple flat 2D background."""
    from PIL import ImageDraw
    bg   = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(bg)

    if style == "outdoor":
        draw.rectangle([0, 0, W, H // 2],     fill=(135, 206, 235, 255))  # sky
        draw.rectangle([0, H // 2, W, H],     fill=(100, 180, 80,  255))  # ground
        draw.ellipse([W-160, 20, W-40, 140],  fill=(255, 230, 50,  255))  # sun
    elif style == "indoor":
        draw.rectangle([0, 0, W, H*2//3],     fill=(210, 190, 160, 255))  # wall
        draw.rectangle([0, H*2//3, W, H],     fill=(140, 100, 70,  255))  # floor
        draw.rectangle([W-260, 60, W-60, 280],fill=(180, 220, 255, 255))  # window
        draw.rectangle([W-260, 60, W-60, 280],outline=(80, 60, 40, 255), width=6)
    elif style == "night":
        draw.rectangle([0, 0, W, H // 2],     fill=(15, 15, 50,   255))
        draw.rectangle([0, H // 2, W, H],     fill=(30, 50, 30,   255))
        draw.ellipse([W-150, 20, W-50, 120],  fill=(240, 240, 200, 255))  # moon

    return bg


def place_character(bg: Image.Image, char_img: Image.Image,
                    x: int, scale: float = 3.0,
                    style: str = "outdoor") -> Image.Image:
    """
    Paste character onto background.
    x: horizontal center position
    scale: upscale factor (poses are 80x110 — need to be bigger on 1280x720)
    """
    frame = bg.copy()
    w = max(1, int(char_img.width  * scale))
    h = max(1, int(char_img.height * scale))
    char = char_img.resize((w, h), Image.NEAREST)  # NEAREST keeps pixel art crisp

    ground_y = H // 2 if style != "indoor" else H * 2 // 3
    paste_x  = x - w // 2
    paste_y  = ground_y - h

    frame.paste(char, (paste_x, paste_y), char)
    return frame
