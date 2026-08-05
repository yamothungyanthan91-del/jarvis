"""
Speaks text aloud using Microsoft Edge's free neural TTS (edge-tts),
then plays it back with a cross-platform audio player.
"""
import asyncio
import os
import platform
import subprocess
import tempfile

import edge_tts

from config import TTS_VOICE


async def _synthesize(text: str, out_path: str):
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(out_path)


def _play(path: str):
    system = platform.system()
    try:
        if "ANDROID_ROOT" in os.environ or os.path.exists("/data/data/com.termux"):
            # Termux on Android
            subprocess.run(["termux-media-player", "play", path], check=False)
        elif system == "Darwin":
            subprocess.run(["afplay", path], check=False)
        elif system == "Windows":
            os.startfile(path)  # noqa: S606
        else:  # Linux
            subprocess.run(["mpg123", "-q", path], check=False)
    except FileNotFoundError:
        print(f"[voice] No audio player found for this platform. "
              f"Install mpg123 (Linux) or use termux-media-player (Android). "
              f"Audio saved at: {path}")


def speak(text: str):
    print(f"Jarvis: {text}")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name
    asyncio.run(_synthesize(text, out_path))
    _play(out_path)
