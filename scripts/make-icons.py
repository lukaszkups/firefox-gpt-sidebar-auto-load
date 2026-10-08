#!/usr/bin/env python3
"""Crop icons/logo.png and write the toolbar sizes on a transparent background."""

from PIL import Image
from pathlib import Path


def remove_white(image):
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            red, green, blue, _alpha = pixels[x, y]
            alpha = max(255 - red, 255 - green, 255 - blue)
            if alpha <= 0:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            # The source is flattened on white. Restore the logo color at the fringe.
            coverage = alpha / 255
            white = 255 * (1 - coverage)

            def channel(value):
                return max(0, min(255, round((value - white) / coverage)))

            pixels[x, y] = (channel(red), channel(green), channel(blue), alpha)
    return image


def crop_to_content(image):
    bounds = image.getbbox()
    if bounds is None:
        raise SystemExit("logo.png has no visible pixels")
    return image.crop(bounds)


def fit_square(image):
    width, height = image.size
    side = max(width, height)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(image, ((side - width) // 2, (side - height) // 2), image)
    return canvas


def main():
    root = Path(__file__).resolve().parents[1]
    icons = root / "icons"
    source = remove_white(Image.open(icons / "logo.png"))
    master = fit_square(crop_to_content(source))
    for size in (32, 48, 96):
        master.resize((size, size), Image.Resampling.LANCZOS).save(icons / f"robot-{size}.png")


if __name__ == "__main__":
    main()
