#!/usr/bin/env python3
"""
Demo Player — New User Experience & Quality Assurance Test

BUSINESS CONTEXT:
Simulates a brand-new user arriving at the demo for the first time.
Validates that the demo delivers a maximum learning experience by checking:

1. AUDIO/VIDEO SYNC — drift between narration and video stays under threshold
2. PACING — narration words-per-minute is within comfortable listening range
3. CONTENT ABSORPTION — each slide provides enough dwell time for the content
4. MEDIA READINESS — audio never starts before video is visually playing
5. TRANSITION SMOOTHNESS — slides auto-advance only after both media finish
6. ACCESSIBILITY — subtitles visible, keyboard navigation works
7. FIRST IMPRESSION — page loads quickly, no console errors, clear UI cues

Run:
    python tests/e2e/test_demo_new_user_experience.py

    # Specific slides only (comma-separated):
    python tests/e2e/test_demo_new_user_experience.py --slides 1,2,10,20

    # All 20 slides (takes ~15 minutes):
    python tests/e2e/test_demo_new_user_experience.py --all
"""

import argparse
import asyncio
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page, BrowserContext

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("TEST_BASE_URL", "https://techuni.ai")
REPORT_DIR = Path("test-reports/demo-ux")

# Thresholds (tweak these to tighten/loosen quality gates)
MAX_DRIFT_MS = 300          # Max acceptable audio/video drift in milliseconds
MAX_WPM = 180               # Narration faster than this is hard to follow
MIN_WPM = 100               # Slower than this feels sluggish
MIN_DWELL_SECONDS = 10      # Minimum slide display time for content absorption
MAX_LOAD_TIME_S = 8         # Page must be interactive within this many seconds
SYNC_SAMPLE_INTERVAL_S = 2  # How often to sample drift during playback
MEDIA_READY_TIMEOUT_MS = 15000  # Max wait for media to buffer


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SlideSample:
    """A single sync measurement taken during playback."""
    timestamp_s: float       # Wall-clock seconds since play started
    video_time_s: float      # video.currentTime
    audio_time_s: float      # audio.currentTime
    drift_ms: float          # (video - audio) * 1000
    video_paused: bool
    audio_paused: bool
    video_ended: bool
    audio_ended: bool


@dataclass
class SlideReport:
    """Quality report for one slide."""
    slide_id: int
    title: str
    narration_word_count: int
    narration_wpm: float
    audio_duration_s: float
    video_duration_s: float
    effective_duration_s: float  # max(audio, video)
    dwell_time_ok: bool
    wpm_ok: bool
    max_drift_ms: float
    avg_drift_ms: float
    drift_ok: bool
    media_started_together: bool
    audio_before_video: bool    # True = bad (audio played while video frozen)
    auto_advanced_cleanly: bool
    samples: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


@dataclass
class DemoReport:
    """Full quality report for the entire demo."""
    url: str
    page_load_time_s: float
    page_load_ok: bool
    console_errors: list
    subtitles_visible: bool
    keyboard_nav_works: bool
    slides: list = field(default_factory=list)
    overall_pass: bool = True


# ---------------------------------------------------------------------------
# Browser helper: evaluate JS to read media state
# ---------------------------------------------------------------------------

MEDIA_STATE_JS = """
() => {
    const video = document.querySelector('video');
    const audio = document.querySelector('audio');
    if (!video || !audio) return null;
    return {
        videoTime: video.currentTime,
        audioTime: audio.currentTime,
        videoPaused: video.paused,
        audioPaused: audio.paused,
        videoEnded: video.ended,
        audioEnded: audio.ended,
        videoDuration: video.duration,
        audioDuration: audio.duration,
        videoReadyState: video.readyState,
        audioReadyState: audio.readyState,
    };
}
"""

SLIDE_INFO_JS = """
() => {
    const header = document.querySelector('[class*="progressIndicator"]');
    if (!header) return null;
    const m = header.textContent.match(/Slide\\s+(\\d+)/);
    return m ? parseInt(m[1]) : null;
}
"""

NARRATION_TEXT_JS = """
() => {
    const box = document.querySelector('[class*="narrationBox"]');
    return box ? box.textContent.replace(/^CC/, '').trim() : null;
}
"""

CONSOLE_ERRORS_JS = """
() => window.__demoTestConsoleErrors || []
"""


# ---------------------------------------------------------------------------
# Core test logic
# ---------------------------------------------------------------------------

async def inject_console_capture(page: Page):
    """Inject JS to capture console errors for later inspection."""
    await page.evaluate("""
        window.__demoTestConsoleErrors = [];
        const origError = console.error;
        console.error = function(...args) {
            window.__demoTestConsoleErrors.push(args.map(String).join(' '));
            origError.apply(console, args);
        };
    """)


async def measure_page_load(page: Page, url: str) -> float:
    """Navigate to the demo and return load time in seconds."""
    start = time.monotonic()
    await page.goto(url + "/demo", wait_until="domcontentloaded")
    # Wait for the Play button as the "interactive" signal
    await page.wait_for_selector("button:has-text('Play')", timeout=MAX_LOAD_TIME_S * 1000)
    elapsed = time.monotonic() - start
    return round(elapsed, 2)


async def check_subtitles(page: Page) -> bool:
    """Verify subtitle/narration box is visible on load."""
    narration = page.locator("[class*='narrationBox']")
    return await narration.is_visible()


async def check_keyboard_nav(page: Page) -> bool:
    """Test basic keyboard navigation without disrupting state."""
    # Press 'c' to toggle subtitles off then on
    await page.keyboard.press("c")
    await asyncio.sleep(0.3)
    hidden = not await page.locator("[class*='narrationBox']").is_visible()
    await page.keyboard.press("c")
    await asyncio.sleep(0.3)
    shown = await page.locator("[class*='narrationBox']").is_visible()
    return hidden and shown


async def navigate_to_slide(page: Page, slide_id: int):
    """Click a slide in the timeline to jump to it."""
    slide_item = page.locator(f"li[aria-label*='Slide {slide_id}:']")
    if await slide_item.count() == 0:
        # Fallback: match by text
        slide_item = page.get_by_role(
            "listitem", name=f"Slide {slide_id}:"
        ).first
    await slide_item.click()
    # Wait for slide to load
    await asyncio.sleep(0.5)


async def wait_for_media_ready(page: Page, timeout_ms: int = MEDIA_READY_TIMEOUT_MS) -> bool:
    """Wait until both video and audio have readyState >= 3 (HAVE_FUTURE_DATA)."""
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        state = await page.evaluate(MEDIA_STATE_JS)
        if state and state["videoReadyState"] >= 3 and state["audioReadyState"] >= 3:
            return True
        await asyncio.sleep(0.2)
    return False


async def check_audio_before_video(page: Page) -> bool:
    """
    After pressing play, sample rapidly to see if audio starts
    while video is still frozen (readyState < 3 or currentTime == 0).
    Returns True if audio started before video (BAD).
    """
    for _ in range(20):  # Sample for ~1 second
        state = await page.evaluate(MEDIA_STATE_JS)
        if not state:
            break
        # Audio playing but video hasn't moved yet
        if (not state["audioPaused"] and state["audioTime"] > 0.1
                and state["videoTime"] < 0.05 and not state["videoPaused"]):
            return True
        if state["videoTime"] > 0.1:
            break  # Video started, we're good
        await asyncio.sleep(0.05)
    return False


async def play_and_sample_slide(
    page: Page,
    slide_id: int,
    narration_text: str,
    max_play_seconds: float = 120,
) -> SlideReport:
    """
    Play a single slide and collect sync samples + quality metrics.
    """
    word_count = len(narration_text.split())
    report = SlideReport(
        slide_id=slide_id,
        title="",
        narration_word_count=word_count,
        narration_wpm=0,
        audio_duration_s=0,
        video_duration_s=0,
        effective_duration_s=0,
        dwell_time_ok=True,
        wpm_ok=True,
        max_drift_ms=0,
        avg_drift_ms=0,
        drift_ok=True,
        media_started_together=True,
        audio_before_video=False,
        auto_advanced_cleanly=True,
    )

    # Get slide title from timeline
    title_el = page.locator(f"li[aria-label*='Slide {slide_id}:']")
    if await title_el.count() > 0:
        label = await title_el.get_attribute("aria-label") or ""
        report.title = label.split(":")[1].split(",")[0].strip() if ":" in label else f"Slide {slide_id}"
    else:
        report.title = f"Slide {slide_id}"

    # Wait for media to buffer
    ready = await wait_for_media_ready(page)
    if not ready:
        report.errors.append("Media did not reach ready state within timeout")
        return report

    # Get initial durations
    state = await page.evaluate(MEDIA_STATE_JS)
    if state:
        report.video_duration_s = round(state["videoDuration"], 1)
        report.audio_duration_s = round(state["audioDuration"], 1)
        report.effective_duration_s = max(report.video_duration_s, report.audio_duration_s)

    # Calculate WPM from audio duration
    if report.audio_duration_s > 0:
        report.narration_wpm = round((word_count / report.audio_duration_s) * 60, 1)
        report.wpm_ok = MIN_WPM <= report.narration_wpm <= MAX_WPM

    # Check dwell time
    report.dwell_time_ok = report.effective_duration_s >= MIN_DWELL_SECONDS

    # Press Play
    play_btn = page.get_by_role("button", name="Play")
    if await play_btn.count() > 0:
        await play_btn.click()
    else:
        report.errors.append("Play button not found")
        return report

    # Rapid check: did audio start before video?
    report.audio_before_video = await check_audio_before_video(page)
    if report.audio_before_video:
        report.media_started_together = False
        report.warnings.append("Audio started playing before video was visually active")

    # Sample drift periodically until slide ends or we time out.
    #
    # DETECTION APPROACH for auto-advance:
    # The sampling interval (2s) is too coarse to reliably catch the brief
    # moment when both media are in 'ended' state before the slide transitions.
    # Instead, we track the maximum audio/video currentTime seen. If the max
    # observed time reaches >= 95% of the media duration, we consider it
    # "completed naturally" even if we didn't sample the exact ended event.
    start_wall = time.monotonic()
    drift_values = []
    saw_video_ended = False
    saw_audio_ended = False
    max_video_time = 0.0
    max_audio_time = 0.0

    while (time.monotonic() - start_wall) < max_play_seconds:
        state = await page.evaluate(MEDIA_STATE_JS)
        if not state:
            await asyncio.sleep(SYNC_SAMPLE_INTERVAL_S)
            continue

        drift_ms = round((state["videoTime"] - state["audioTime"]) * 1000, 1)
        sample = SlideSample(
            timestamp_s=round(time.monotonic() - start_wall, 2),
            video_time_s=round(state["videoTime"], 2),
            audio_time_s=round(state["audioTime"], 2),
            drift_ms=drift_ms,
            video_paused=state["videoPaused"],
            audio_paused=state["audioPaused"],
            video_ended=state["videoEnded"],
            audio_ended=state["audioEnded"],
        )
        report.samples.append(sample)

        # Only count drift while both are actively playing
        if not state["videoPaused"] and not state["audioPaused"]:
            drift_values.append(abs(drift_ms))

        # Track ended states and max times
        if state["videoEnded"]:
            saw_video_ended = True
        if state["audioEnded"]:
            saw_audio_ended = True
        max_video_time = max(max_video_time, state["videoTime"])
        max_audio_time = max(max_audio_time, state["audioTime"])

        # Check if slide advanced (we moved to a different slide)
        current_slide = await page.evaluate(SLIDE_INFO_JS)
        if current_slide and current_slide != slide_id:
            break

        if saw_video_ended and saw_audio_ended:
            # Both ended, wait briefly for auto-advance then exit
            await asyncio.sleep(2)
            break

        await asyncio.sleep(SYNC_SAMPLE_INTERVAL_S)

    # Compute drift stats
    if drift_values:
        report.max_drift_ms = round(max(drift_values), 1)
        report.avg_drift_ms = round(sum(drift_values) / len(drift_values), 1)
        report.drift_ok = report.max_drift_ms <= MAX_DRIFT_MS

    # Auto-advance check: did both media play to completion before advancing?
    # We consider media "completed" if either:
    #   (a) we directly observed the ended event, OR
    #   (b) the max observed time reached >= 95% of the duration
    COMPLETION_THRESHOLD = 0.95
    video_completed = (
        saw_video_ended
        or (report.video_duration_s > 0
            and max_video_time >= report.video_duration_s * COMPLETION_THRESHOLD)
    )
    audio_completed = (
        saw_audio_ended
        or (report.audio_duration_s > 0
            and max_audio_time >= report.audio_duration_s * COMPLETION_THRESHOLD)
    )

    if not (video_completed and audio_completed):
        report.auto_advanced_cleanly = False
        report.errors.append(
            f"Slide advanced before both media completed "
            f"(video: {'done' if video_completed else f'{max_video_time:.1f}/{report.video_duration_s}s'}, "
            f"audio: {'done' if audio_completed else f'{max_audio_time:.1f}/{report.audio_duration_s}s'})"
        )

    # Add warnings for WPM issues
    if report.narration_wpm > MAX_WPM:
        report.warnings.append(
            f"Narration too fast at {report.narration_wpm} WPM "
            f"(max {MAX_WPM}). Learners may struggle to follow."
        )
    elif report.narration_wpm < MIN_WPM:
        report.warnings.append(
            f"Narration too slow at {report.narration_wpm} WPM "
            f"(min {MIN_WPM}). May feel sluggish."
        )

    if not report.dwell_time_ok:
        report.warnings.append(
            f"Slide only {report.effective_duration_s}s — below {MIN_DWELL_SECONDS}s minimum. "
            f"Users may not absorb the content."
        )

    return report


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_demo_ux_test(slide_ids: Optional[list] = None, base_url: str = BASE_URL):
    """
    Main test runner. Plays through selected slides (or a default sample)
    and produces a comprehensive quality report.
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Default: test a representative sample (first, middle, last, plus edge cases)
    if slide_ids is None:
        slide_ids = [1, 2, 3, 10, 15, 20]

    print(f"\n{'='*70}")
    print(f"  DEMO PLAYER — NEW USER EXPERIENCE TEST")
    print(f"  URL: {base_url}/demo")
    print(f"  Slides to test: {slide_ids}")
    print(f"{'='*70}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--ignore-certificate-errors",
                "--autoplay-policy=no-user-gesture-required",
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )

        page = await context.new_page()

        # Inject console error capture
        await inject_console_capture(page)

        # ---------------------------------------------------------------
        # Phase 1: First Impression — Page Load
        # ---------------------------------------------------------------
        print("[Phase 1] First Impression — Page Load")
        try:
            load_time = await measure_page_load(page, base_url)
            load_ok = load_time <= MAX_LOAD_TIME_S
            status = "PASS" if load_ok else "FAIL"
            print(f"  Page load time: {load_time}s [{status}] (max {MAX_LOAD_TIME_S}s)")
        except Exception as e:
            load_time = -1
            load_ok = False
            print(f"  Page load FAILED: {e}")

        demo_report = DemoReport(
            url=f"{base_url}/demo",
            page_load_time_s=load_time,
            page_load_ok=load_ok,
            console_errors=[],
            subtitles_visible=False,
            keyboard_nav_works=False,
        )

        if not load_ok and load_time == -1:
            print("\n  FATAL: Could not load demo page. Aborting.")
            demo_report.overall_pass = False
            await browser.close()
            return demo_report

        # ---------------------------------------------------------------
        # Phase 2: Accessibility Quick-Check
        # ---------------------------------------------------------------
        print("\n[Phase 2] Accessibility Quick-Check")

        demo_report.subtitles_visible = await check_subtitles(page)
        print(f"  Subtitles visible: {'PASS' if demo_report.subtitles_visible else 'FAIL'}")

        demo_report.keyboard_nav_works = await check_keyboard_nav(page)
        print(f"  Keyboard nav (C key): {'PASS' if demo_report.keyboard_nav_works else 'FAIL'}")

        # ---------------------------------------------------------------
        # Phase 3: Slide-by-Slide Playback Quality
        # ---------------------------------------------------------------
        print(f"\n[Phase 3] Slide-by-Slide Playback Quality ({len(slide_ids)} slides)")
        print(f"  Thresholds: max drift={MAX_DRIFT_MS}ms, WPM={MIN_WPM}-{MAX_WPM}, min dwell={MIN_DWELL_SECONDS}s")
        print()

        for idx, sid in enumerate(slide_ids):
            print(f"  --- Slide {sid} ({idx+1}/{len(slide_ids)}) ---")

            # Navigate to slide
            await navigate_to_slide(page, sid)
            await asyncio.sleep(1)  # Let media sources load

            # Get narration text
            narration = await page.evaluate(NARRATION_TEXT_JS) or ""
            if not narration:
                print(f"    WARNING: No narration text found for slide {sid}")

            # Play and collect measurements
            slide_report = await play_and_sample_slide(
                page, sid, narration,
                max_play_seconds=120,
            )
            demo_report.slides.append(slide_report)

            # Print slide results
            print(f"    Title: {slide_report.title}")
            print(f"    Words: {slide_report.narration_word_count} | "
                  f"WPM: {slide_report.narration_wpm} "
                  f"[{'PASS' if slide_report.wpm_ok else 'WARN'}]")
            print(f"    Audio: {slide_report.audio_duration_s}s | "
                  f"Video: {slide_report.video_duration_s}s | "
                  f"Effective: {slide_report.effective_duration_s}s")
            print(f"    Dwell time: "
                  f"[{'PASS' if slide_report.dwell_time_ok else 'WARN'}] "
                  f"(min {MIN_DWELL_SECONDS}s)")
            print(f"    Sync drift: avg={slide_report.avg_drift_ms}ms, "
                  f"max={slide_report.max_drift_ms}ms "
                  f"[{'PASS' if slide_report.drift_ok else 'FAIL'}] "
                  f"(max {MAX_DRIFT_MS}ms)")
            print(f"    Media start together: "
                  f"[{'PASS' if slide_report.media_started_together else 'FAIL'}]")
            print(f"    Auto-advance clean: "
                  f"[{'PASS' if slide_report.auto_advanced_cleanly else 'FAIL'}]")

            if slide_report.warnings:
                for w in slide_report.warnings:
                    print(f"    WARNING: {w}")
            if slide_report.errors:
                for e in slide_report.errors:
                    print(f"    ERROR: {e}")
            print()

            # Pause before next slide (let auto-advance settle)
            pause_btn = page.get_by_role("button", name="Pause")
            if await pause_btn.count() > 0:
                await pause_btn.click()
            await asyncio.sleep(0.5)

        # ---------------------------------------------------------------
        # Phase 4: Console Error Check
        # ---------------------------------------------------------------
        print("[Phase 4] Console Errors")
        console_errors = await page.evaluate(CONSOLE_ERRORS_JS) or []
        demo_report.console_errors = console_errors
        if console_errors:
            print(f"  FAIL: {len(console_errors)} console error(s):")
            for err in console_errors[:10]:
                print(f"    - {err[:120]}")
        else:
            print("  PASS: No console errors")

        # ---------------------------------------------------------------
        # Phase 5: Overall Verdict
        # ---------------------------------------------------------------
        print(f"\n{'='*70}")
        print("  OVERALL RESULTS")
        print(f"{'='*70}")

        # Determine overall pass/fail
        all_slide_checks = []
        for sr in demo_report.slides:
            all_slide_checks.extend([
                sr.drift_ok,
                sr.media_started_together,
                sr.auto_advanced_cleanly,
            ])

        critical_pass = (
            demo_report.page_load_ok
            and demo_report.subtitles_visible
            and len(console_errors) == 0
            and all(all_slide_checks)
        )
        demo_report.overall_pass = critical_pass

        # Summary table
        print(f"\n  {'Check':<35} {'Result':<8}")
        print(f"  {'-'*35} {'-'*8}")
        print(f"  {'Page load < ' + str(MAX_LOAD_TIME_S) + 's':<35} "
              f"{'PASS' if demo_report.page_load_ok else 'FAIL':<8}")
        print(f"  {'Subtitles visible':<35} "
              f"{'PASS' if demo_report.subtitles_visible else 'FAIL':<8}")
        print(f"  {'Keyboard navigation':<35} "
              f"{'PASS' if demo_report.keyboard_nav_works else 'FAIL':<8}")
        print(f"  {'Console errors = 0':<35} "
              f"{'PASS' if not console_errors else 'FAIL':<8}")

        for sr in demo_report.slides:
            label = f"Slide {sr.slide_id} sync (<{MAX_DRIFT_MS}ms)"
            print(f"  {label:<35} {'PASS' if sr.drift_ok else 'FAIL':<8}")

        for sr in demo_report.slides:
            label = f"Slide {sr.slide_id} media start"
            print(f"  {label:<35} {'PASS' if sr.media_started_together else 'FAIL':<8}")

        for sr in demo_report.slides:
            label = f"Slide {sr.slide_id} auto-advance"
            print(f"  {label:<35} {'PASS' if sr.auto_advanced_cleanly else 'FAIL':<8}")

        # WPM / dwell warnings (not critical failures)
        wpm_warnings = [sr for sr in demo_report.slides if not sr.wpm_ok]
        dwell_warnings = [sr for sr in demo_report.slides if not sr.dwell_time_ok]

        if wpm_warnings:
            print(f"\n  PACING WARNINGS ({len(wpm_warnings)} slides):")
            for sr in wpm_warnings:
                print(f"    Slide {sr.slide_id}: {sr.narration_wpm} WPM "
                      f"({'too fast' if sr.narration_wpm > MAX_WPM else 'too slow'})")

        if dwell_warnings:
            print(f"\n  DWELL TIME WARNINGS ({len(dwell_warnings)} slides):")
            for sr in dwell_warnings:
                print(f"    Slide {sr.slide_id}: {sr.effective_duration_s}s "
                      f"(min {MIN_DWELL_SECONDS}s)")

        verdict = "PASS" if demo_report.overall_pass else "FAIL"
        print(f"\n  {'='*35}")
        print(f"  VERDICT: {verdict}")
        print(f"  {'='*35}\n")

        # ---------------------------------------------------------------
        # Save JSON report
        # ---------------------------------------------------------------
        report_path = REPORT_DIR / "demo_ux_report.json"
        report_data = {
            "url": demo_report.url,
            "page_load_time_s": demo_report.page_load_time_s,
            "page_load_ok": demo_report.page_load_ok,
            "subtitles_visible": demo_report.subtitles_visible,
            "keyboard_nav_works": demo_report.keyboard_nav_works,
            "console_errors": demo_report.console_errors,
            "overall_pass": demo_report.overall_pass,
            "thresholds": {
                "max_drift_ms": MAX_DRIFT_MS,
                "max_wpm": MAX_WPM,
                "min_wpm": MIN_WPM,
                "min_dwell_seconds": MIN_DWELL_SECONDS,
                "max_load_time_s": MAX_LOAD_TIME_S,
            },
            "slides": [
                {
                    "slide_id": sr.slide_id,
                    "title": sr.title,
                    "word_count": sr.narration_word_count,
                    "wpm": sr.narration_wpm,
                    "audio_duration_s": sr.audio_duration_s,
                    "video_duration_s": sr.video_duration_s,
                    "effective_duration_s": sr.effective_duration_s,
                    "dwell_time_ok": sr.dwell_time_ok,
                    "wpm_ok": sr.wpm_ok,
                    "max_drift_ms": sr.max_drift_ms,
                    "avg_drift_ms": sr.avg_drift_ms,
                    "drift_ok": sr.drift_ok,
                    "media_started_together": sr.media_started_together,
                    "audio_before_video": sr.audio_before_video,
                    "auto_advanced_cleanly": sr.auto_advanced_cleanly,
                    "sample_count": len(sr.samples),
                    "warnings": sr.warnings,
                    "errors": sr.errors,
                }
                for sr in demo_report.slides
            ],
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        print(f"  Report saved: {report_path}")

        await browser.close()

    return demo_report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Demo Player — New User Experience & Quality Assurance Test"
    )
    parser.add_argument(
        "--slides",
        type=str,
        default=None,
        help="Comma-separated slide IDs to test (e.g. 1,2,10,20). "
             "Default: representative sample [1,2,3,10,15,20]."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all 20 slides (takes ~15 minutes)."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help=f"Base URL to test. Default: {BASE_URL}"
    )
    args = parser.parse_args()

    base_url = args.url if args.url else BASE_URL

    if args.all:
        slide_ids = list(range(1, 21))
    elif args.slides:
        slide_ids = [int(s.strip()) for s in args.slides.split(",")]
    else:
        slide_ids = None  # Use default sample

    report = asyncio.run(run_demo_ux_test(slide_ids, base_url))

    sys.exit(0 if report.overall_pass else 1)


if __name__ == "__main__":
    main()
