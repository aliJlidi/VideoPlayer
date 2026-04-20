"""
HTML Slideshow to MP4 Converter
================================
Captures the restaurant promo HTML slideshow frame-by-frame
and encodes it into a 1920x1080 MP4 video.

Requirements:
    pip install playwright
    playwright install chromium
    # ffmpeg must be installed and in PATH

Usage:
    python html_to_video.py

Output:
    restaurant_promo.mp4 in the same directory
"""

import subprocess
import shutil
import os
import time
from pathlib import Path
from tqdm import tqdm
from playwright.sync_api import sync_playwright

# ── Configuration ──
HTML_FILE = "restaurant_promo.html"  # path to your HTML file
OUTPUT_VIDEO = "restaurant_promo.mp4"
WIDTH = 1920
HEIGHT = 1080
FPS = 30
DURATION_SECONDS = 36  # 4 screens x 8s each + 4s buffer for transitions
FRAME_DIR = "frames"


def check_dependencies():
    """Verify ffmpeg is installed."""
    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found in PATH.")
        print("Install it:")
        print("  Windows: https://ffmpeg.org/download.html")
        print("  Mac:     brew install ffmpeg")
        print("  Linux:   sudo apt install ffmpeg")
        raise SystemExit(1)


def capture_frames():
    """Launch headless browser, screenshot each frame."""
    html_path = Path(HTML_FILE).resolve()
    if not html_path.exists():
        print(f"ERROR: {HTML_FILE} not found.")
        print("Place this script in the same folder as restaurant_promo.html")
        raise SystemExit(1)

    frame_dir = Path(FRAME_DIR)
    frame_dir.mkdir(exist_ok=True)

    total_frames = FPS * DURATION_SECONDS
    interval_ms = 1000 / FPS  # ~33.3ms per frame

    print(f"Capturing {total_frames} frames at {FPS}fps ({DURATION_SECONDS}s)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.goto(f"file://{html_path}", wait_until="networkidle")

        # Wait for fonts and images to load
        time.sleep(2)

        for i in tqdm(range(total_frames), desc="Capturing", unit="frame"):
            frame_path = frame_dir / f"frame_{i:05d}.png"
            page.screenshot(path=str(frame_path))

            # Advance time by sleeping the real interval
            # playwright runs in real time so animations play naturally
            page.wait_for_timeout(interval_ms)

        browser.close()

    print(f"Captured {total_frames} frames in ./{FRAME_DIR}/")


def encode_video():
    """Encode PNG frames into MP4 using ffmpeg."""
    print("Encoding video with ffmpeg...")

    cmd = [
        "ffmpeg",
        "-y",                          # overwrite output
        "-framerate", str(FPS),        # input framerate
        "-i", f"{FRAME_DIR}/frame_%05d.png",  # input pattern
        "-c:v", "libx264",            # H.264 codec
        "-preset", "slow",            # better compression
        "-crf", "18",                 # high quality (lower = better, 18 is near lossless)
        "-pix_fmt", "yuv420p",        # compatibility with most players
        "-movflags", "+faststart",    # web-friendly (metadata at start)
        OUTPUT_VIDEO,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("ffmpeg error:")
        print(result.stderr)
        raise SystemExit(1)

    file_size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"Done: {OUTPUT_VIDEO} ({file_size:.1f} MB)")


def cleanup():
    """Remove temporary frame images."""
    frame_dir = Path(FRAME_DIR)
    if frame_dir.exists():
        count = len(list(frame_dir.glob("*.png")))
        shutil.rmtree(frame_dir)
        print(f"Cleaned up {count} temporary frames.")


def main():
    check_dependencies()
    capture_frames()
    encode_video()
    cleanup()
    print(f"\nVideo ready: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()