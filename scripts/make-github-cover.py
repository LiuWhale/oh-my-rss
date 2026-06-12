#!/usr/bin/env python3
"""Compose the GitHub cover image from the generated background."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - developer helper script
    raise SystemExit("Install Pillow to regenerate the cover: python -m pip install pillow") from exc


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "github-cover-source.png"
OUTPUT = ROOT / "assets" / "github-cover.png"
WIDTH = 1280
HEIGHT = 640


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def crop_to_ratio(image: Image.Image, width: int, height: int) -> Image.Image:
    source_ratio = image.width / image.height
    target_ratio = width / height

    if source_ratio > target_ratio:
        new_width = round(image.height * target_ratio)
        left = (image.width - new_width) // 2
        return image.crop((left, 0, left + new_width, image.height))

    new_height = round(image.width / target_ratio)
    top = max(0, min(image.height - new_height, 68))
    return image.crop((0, top, image.width, top + new_height))


def add_left_readability_wash(image: Image.Image) -> None:
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    pixels = overlay.load()
    fade_width = int(WIDTH * 0.56)
    for x in range(fade_width):
        alpha = int(208 * (1 - x / fade_width) ** 1.6)
        for y in range(HEIGHT):
            pixels[x, y] = (255, 255, 255, alpha)
    image.alpha_composite(overlay)


def draw_text(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    graphite = (32, 47, 61)
    muted = (82, 101, 117)
    teal = (16, 143, 153)
    coral = (239, 103, 78)

    title_font = font(92, bold=True)
    subtitle_font = font(34)
    body_font = font(24)
    tag_font = font(21)

    x = 78
    y = 76
    draw.text((x, y), "Oh My RSS", fill=graphite, font=title_font)
    draw.rounded_rectangle((x + 2, y + 118, x + 242, y + 128), radius=5, fill=coral)
    draw.rounded_rectangle((x + 256, y + 118, x + 514, y + 128), radius=5, fill=teal)

    draw.text((x + 2, y + 154), "RSS-native AI research radar", fill=teal, font=subtitle_font)
    draw.text(
        (x + 4, y + 210),
        "FreshRSS -> Codex summaries -> category feeds -> monthly trends",
        fill=muted,
        font=body_font,
    )

    tag_x = x + 4
    tag_y = y + 270
    tags = ["self-hosted", "open source", "paper feeds", "Reeder-ready"]
    for tag in tags:
        text_bbox = draw.textbbox((0, 0), tag, font=tag_font)
        tag_width = text_bbox[2] - text_bbox[0] + 30
        draw.rounded_rectangle(
            (tag_x, tag_y, tag_x + tag_width, tag_y + 42),
            radius=21,
            fill=(255, 255, 255, 222),
            outline=(218, 230, 235),
            width=2,
        )
        draw.text((tag_x + 15, tag_y + 9), tag, fill=graphite, font=tag_font)
        tag_x += tag_width + 12


def main() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    cover = crop_to_ratio(source, WIDTH, HEIGHT).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    add_left_readability_wash(cover)
    draw_text(cover)
    cover.convert("RGB").save(OUTPUT, quality=95, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
