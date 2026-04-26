"""
HTML Slideshow to MP4 — High Resolution Converter
===================================================
Records an HTML slideshow as a high-quality MP4 using Playwright
for capture and ffmpeg for post-processing (WebM -> MP4, high bitrate).

Requirements:
    pip install playwright tqdm
    playwright install chromium
    ffmpeg must be installed and in PATH (apt install ffmpeg / brew install ffmpeg)

Usage:
    python html_to_mp4.py
    python html_to_mp4.py --file path/to/slideshow.html
    python html_to_mp4.py --file slideshow.html --duration 40 --width 1920 --height 1080
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

from tqdm import tqdm

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_DURATION = 80   # seconds — adjust to match your slideshow length
DEFAULT_CRF = 18        # ffmpeg CRF: 0=lossless, 18=visually lossless, 23=default
DEFAULT_PRESET = "slow" # ffmpeg preset: ultrafast / fast / medium / slow / veryslow


def ask_html_file() -> Path:
    """Prompt user to enter the HTML file path and validate it."""
    while True:
        raw = input("Enter the path to the HTML file to convert: ").strip()
        if not raw:
            print("  Path cannot be empty. Try again.")
            continue
        path = Path(raw).resolve()
        if not path.exists():
            print(f"  File not found: {path}. Try again.")
            continue
        if path.suffix.lower() not in (".html", ".htm"):
            confirm = input(f"  '{path.suffix}' is not .html — continue anyway? [y/N]: ").strip().lower()
            if confirm != "y":
                continue
        return path


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def record_webm(html_path: Path, width: int, height: int, duration: int) -> Path:
    """Use Playwright to record the slideshow as a WebM file."""
    output_dir = html_path.parent

    print(f"\nLaunching browser at {width}x{height}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=str(output_dir),
            record_video_size={"width": width, "height": height},
        )
        page = context.new_page()
        page.goto(f"file://{html_path}", wait_until="networkidle")

        # Wait for fonts/images to settle
        time.sleep(2)

        print(f"Recording {duration}s of slideshow...")
        for _ in tqdm(range(duration), unit="s", desc="Recording", ncols=70):
            time.sleep(1)

        raw_video_path = page.video.path()
        context.close()
        browser.close()

    webm_path = output_dir / (html_path.stem + "_raw.webm")
    Path(raw_video_path).rename(webm_path)
    print(f"Raw WebM saved: {webm_path.name}")
    return webm_path


def convert_to_mp4(webm_path: Path, output_mp4: Path, crf: int, preset: str) -> None:
    """Convert WebM to high-quality MP4 using ffmpeg."""
    print(f"\nConverting to MP4 (CRF={crf}, preset={preset})...")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(webm_path),
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",   # maximum compatibility
        "-movflags", "+faststart", # web-optimized: metadata at start
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # ensure even dimensions
        str(output_mp4),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg error:\n", result.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Convert an HTML slideshow to a high-res MP4.")
    parser.add_argument("--file",     type=str,  help="Path to the HTML file")
    parser.add_argument("--duration", type=int,  default=DEFAULT_DURATION, help=f"Recording duration in seconds (default: {DEFAULT_DURATION})")
    parser.add_argument("--width",    type=int,  default=DEFAULT_WIDTH,    help=f"Viewport width (default: {DEFAULT_WIDTH})")
    parser.add_argument("--height",   type=int,  default=DEFAULT_HEIGHT,   help=f"Viewport height (default: {DEFAULT_HEIGHT})")
    parser.add_argument("--crf",      type=int,  default=DEFAULT_CRF,      help=f"ffmpeg CRF quality, lower=better (default: {DEFAULT_CRF})")
    parser.add_argument("--preset",   type=str,  default=DEFAULT_PRESET,   help=f"ffmpeg encoding preset (default: {DEFAULT_PRESET})")
    args = parser.parse_args()

    # Resolve HTML file
    html_path = Path(args.file).resolve() if args.file else ask_html_file()

    if not html_path.exists():
        print(f"ERROR: File not found: {html_path}")
        sys.exit(1)

    output_mp4 = html_path.parent / (html_path.stem + ".mp4")

    # Check ffmpeg availability
    has_ffmpeg = check_ffmpeg()
    if not has_ffmpeg:
        print("WARNING: ffmpeg not found in PATH. Output will stay as WebM (no MP4 conversion).")
        print("         Install ffmpeg: https://ffmpeg.org/download.html\n")

    # Record
    webm_path = record_webm(html_path, args.width, args.height, args.duration)

    # Convert
    if has_ffmpeg:
        convert_to_mp4(webm_path, output_mp4, args.crf, args.preset)
        webm_path.unlink()  # remove intermediate WebM
        size_mb = output_mp4.stat().st_size / (1024 * 1024)
        print(f"\nDone: {output_mp4.name} ({size_mb:.1f} MB)")
        print(f"Location: {output_mp4}")
    else:
        fallback = html_path.parent / (html_path.stem + ".webm")
        webm_path.rename(fallback)
        size_mb = fallback.stat().st_size / (1024 * 1024)
        print(f"\nDone (WebM only): {fallback.name} ({size_mb:.1f} MB)")
        print(f"Location: {fallback}")


if __name__ == "__main__":
    main()