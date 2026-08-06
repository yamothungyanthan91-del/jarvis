"""
Listens for user speech and returns recognized text.

Android (Termux): records audio with the phone's microphone, then sends
it to Groq's Whisper model for transcription — far more accurate than
Android's built-in speech recognizer, and still completely free (uses
the same GROQ_API_KEY you already have).

Desktop: uses the local microphone via SpeechRecognition + Google's
free recognizer.

Falls back to typed input if neither is available.
"""
import os
import subprocess
import tempfile
import time

RECORD_SECONDS = 6  # how long Jarvis listens on Android before transcribing


def _is_termux() -> bool:
    return os.path.exists("/data/data/com.termux")


def _termux_listen() -> str:
    from groq import Groq
    from config import GROQ_API_KEY

    tmp_path = tempfile.mktemp(suffix=".wav")
    print(f"Listening (speak now — up to {RECORD_SECONDS}s)...")

    # termux-microphone-record returns immediately; the recording itself
    # keeps running in the background for RECORD_SECONDS, so wait it out.
    subprocess.run(
        ["termux-microphone-record", "-f", tmp_path, "-l", str(RECORD_SECONDS)],
        check=False,
    )
    time.sleep(RECORD_SECONDS + 0.5)
    subprocess.run(["termux-microphone-record", "-q"], check=False)  # make sure it's stopped

    if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
        return ""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(tmp_path), f.read()),
                model="whisper-large-v3-turbo",
            )
        text = transcription.text.strip()
        if text:
            print(f"You: {text}")
        return text
    except Exception as e:
        print(f"[listener] Whisper transcription failed: {e}")
        return ""
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def listen() -> str:
    if _is_termux():
        return _termux_listen()

    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)
        text = recognizer.recognize_google(audio)
        print(f"You: {text}")
        return text
    except Exception as e:
        print(f"[listener] Speech recognition unavailable ({e}). Falling back to typed input.")
        return input("Type your message: ").strip()
