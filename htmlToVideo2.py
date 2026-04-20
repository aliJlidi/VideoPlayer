"""
HTML Slideshow to MP4 — Screencast Method
==========================================
Records the slideshow directly as a video using Playwright's
built-in screen recording. No frame dumping, no ffmpeg needed.

Requirements:
    pip install playwright tqdm
    playwright install chromium

Usage:
    Place this script next to restaurant_promo.html and photo_*.png
    python html_to_video.py

Output:
    restaurant_promo.mp4
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# ── Configuration ──
HTML_FILE = "restaurant_promo.html"
OUTPUT_VIDEO = "restaurant_promo.webm"
WIDTH = 1920
HEIGHT = 1080
RECORD_SECONDS = 34  # 4 screens x 8s + 2s buffer


def main():
    html_path = Path(HTML_FILE).resolve()
    if not html_path.exists():
        print(f"ERROR: {HTML_FILE} not found in current directory.")
        raise SystemExit(1)

    output_path = Path(OUTPUT_VIDEO).resolve()

    print(f"Recording {RECORD_SECONDS}s of slideshow at {WIDTH}x{HEIGHT}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            record_video_dir=str(output_path.parent),
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        page = context.new_page()
        page.goto(f"file://{html_path}", wait_until="networkidle")

        # Wait for fonts/images to load
        time.sleep(2)

        print("Recording started...")
        # Let the slideshow play through all 4 screens
        for i in range(RECORD_SECONDS):
            time.sleep(1)
            remaining = RECORD_SECONDS - i - 1
            print(f"  {remaining}s remaining...", end="\r")

        print("\nStopping recording...")
        video_path = page.video.path()
        context.close()
        browser.close()

    # Rename the auto-generated file to our desired name
    generated = Path(video_path)
    if generated.exists():
        final = generated.parent / OUTPUT_VIDEO
        generated.rename(final)
        file_size = final.stat().st_size / (1024 * 1024)
        print(f"\nDone: {final.name} ({file_size:.1f} MB)")
        print(f"Location: {final}")
    else:
        print("ERROR: Video file was not created.")


if __name__ == "__main__":
    main()