"""
Speaks text aloud using Microsoft Edge's free neural TTS (edge-tts),
then plays it back with a cross-platform audio player.

Supports being interrupted mid-sentence (see stop_speaking()).
"""
import asyncio
import os
import platform
import re
import subprocess
import tempfile

import edge_tts

from config import TTS_VOICE

# Tracks the currently-playing audio process (desktop only) so it can be
# killed on command. Android playback is handled by a system service instead
# (see stop_speaking()).
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


def _play(path: str):
    global _current_process
    system = platform.system()
    try:
        if _is_termux():
            # termux-media-player returns immediately; playback runs as a
            # background service, which is what lets us listen for "stop"
            # while it's still talking.
            subprocess.run(["termux-media-player", "play", path], check=False)
        elif system == "Darwin":
            _current_process = subprocess.Popen(["afplay", path])
        elif system == "Windows":
            os.startfile(path)  # noqa: S606
        else:  # Linux
            _current_process = subprocess.Popen(["mpg123", "-q", path])
    except FileNotFoundError:
        print(f"[voice] No audio player found for this platform. "
              f"Install mpg123 (Linux) or use termux-media-player (Android). "
              f"Audio saved at: {path}")


def stop_speaking():
    """Immediately cuts off whatever Jarvis is currently saying."""
    global _current_process
    if _is_termux():
        subprocess.run(["termux-media-player", "stop"], check=False)
    elif _current_process is not None:
        _current_process.terminate()
        _current_process = None


def speak(text: str):
    clean_text = _strip_markdown(text)
    print(f"Jarvis: {clean_text}")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name
    asyncio.run(_synthesize(clean_text, out_path))
    _play(out_path)
