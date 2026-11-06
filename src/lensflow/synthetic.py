"""Deterministic abstract image generation for examples and tests."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def generate_sample_set(output_dir: Path, *, count: int = 6) -> list[Path]:
    if not 1 <= count <= 20:
        raise ValueError("count must be between 1 and 20")
    output = output_dir.resolve(strict=False)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("sample output directory must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    width, height = 800, 600
    for index in range(count):
        image = Image.new(
            "RGB",
            (width, height),
            ((31 + index * 29) % 256, (78 + index * 37) % 256, (126 + index * 43) % 256),
        )
        draw = ImageDraw.Draw(image)
        inset = 55 + index * 7
        draw.ellipse(
            (inset, 70 + index * 9, width - inset, height - 90 - index * 8),
            fill=((218 + index * 11) % 256, (150 + index * 23) % 256, (78 + index * 31) % 256),
            outline=(245, 245, 245),
            width=8,
        )
        draw.polygon(
            [
                (width // 2, 95 + index * 13),
                (width - 100 - index * 5, height // 2),
                (width // 2, height - 100 - index * 7),
                (100 + index * 5, height // 2),
            ],
            fill=((95 + index * 29) % 256, (45 + index * 31) % 256, (190 + index * 17) % 256),
        )
        draw.rectangle(
            (180 + index * 8, 205, 620 - index * 8, 395),
            outline=(255, 255, 255),
            width=5,
        )
        path = output / f"synthetic_{index + 1:02d}.png"
        image.save(path, format="PNG", optimize=False)
        image.close()
        results.append(path)
    return results
