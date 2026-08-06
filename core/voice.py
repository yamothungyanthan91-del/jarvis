"""
Speaks text aloud using Microsoft Edge's free neural TTS (edge-tts),
then plays it back with a cross-platform audio player.

IMPORTANT: speak() waits for playback to actually finish before
returning. On a phone, the mic and speaker are right next to each
other with no echo cancellation, so if Jarvis started listening again
while still talking, it would hear its own voice through the speaker
and mistake it for you talking (a feedback loop). Waiting for the
exact audio duration to elapse before listening again prevents that.
"""
import asyncio
import os
import platform
import re
import subprocess
import tempfile
import time

import edge_tts
from mutagen.mp3 import MP3

from config import TTS_VOICE

# Tracks the currently-playing audio process (desktop only) so it can be
# killed on command via stop_speaking().
_current_process = None


def _strip_markdown(text: str) -> str:
    """Remove markdown symbols (**, ##, -, etc.) so TTS doesn't read them
    aloud and the printed text is clean."""
    text = re.sub(r"[*_`#]+", "", text)          # **bold**, _italic_, `code`, ## headers
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)  # bullet points
    text = re.sub(r"\n{2,}", ". ", text)          # collapse blank lines into a pause
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


async def _synthesize(text: str, out_path: str):
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(out_path)


def _is_termux() -> bool:
    return "ANDROID_ROOT" in os.environ or os.path.exists("/data/data/com.termux")


def _audio_duration_seconds(path: str) -> float:
    try:
        return MP3(path).info.length
    except Exception:
        return 4.0  # safe fallback if duration can't be read


def _play_and_wait(path: str):
    """Plays the audio and blocks until it's actually finished."""
    global _current_process
    system = platform.system()
    duration = _audio_duration_seconds(path)

    try:
        if _is_termux():
            subprocess.run(["termux-media-player", "play", path], check=False)
            # termux-media-player returns immediately even though playback
            # continues in the background, so wait out the real duration.
            time.sleep(duration + 0.4)
        elif system == "Darwin":
            _current_process = subprocess.Popen(["afplay", path])
            _current_process.wait()
        elif system == "Windows":
            os.startfile(path)  # noqa: S606
            time.sleep(duration + 0.4)
        else:  # Linux
            _current_process = subprocess.Popen(["mpg123", "-q", path])
            _current_process.wait()
    except FileNotFoundError:
        print(f"[voice] No audio player found for this platform. "
              f"Install mpg123 (Linux) or use termux-media-player (Android). "
              f"Audio saved at: {path}")
    finally:
        _current_process = None


def stop_speaking():
    """Immediately cuts off whatever Jarvis is currently saying."""
    if _is_termux():
        subprocess.run(["termux-media-player", "stop"], check=False)
    elif _current_process is not None:
        _current_process.terminate()


def speak(text: str):
    clean_text = _strip_markdown(text)
    print(f"Jarvis: {clean_text}")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name
    asyncio.run(_synthesize(clean_text, out_path))
    _play_and_wait(out_path)
