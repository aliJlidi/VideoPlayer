#!/usr/bin/env python3

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed. Run: pip install Pillow")
    sys.exit(1)


def convert_to_png(image_path: str) -> None:
    path = Path(image_path.strip())

    if not path.exists():
        print(f"Error: file not found -> {path}")
        return

    if not path.is_file():
        print(f"Error: not a file -> {path}")
        return

    if path.suffix.lower() == ".png":
        print("The file is already a PNG. Nothing to do.")
        return

    output_path = path.with_suffix(".png")

    try:
        with Image.open(path) as img:
            img_rgb = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
            img_rgb.save(output_path, format="PNG")
        print(f"Converted: {path.name} -> {output_path.name}")

        path.unlink()
        print(f"Deleted original: {path.name}")
        print(f"Done. PNG saved at: {output_path.resolve()}")

    except Exception as e:
        print(f"Error during conversion: {e}")


def main():
    if len(sys.argv) > 1:
        image_path = " ".join(sys.argv[1:])
    else:
        image_path = input("Enter the path to the image to convert: ")

    convert_to_png(image_path)


if __name__ == "__main__":
    main()