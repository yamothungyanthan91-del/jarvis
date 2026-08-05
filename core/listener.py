"""
Listens for user speech and returns recognized text.
Auto-detects Termux (Android) vs a desktop mic via SpeechRecognition.
Falls back to typed input if neither is available.
"""
import os
import subprocess


def _is_termux() -> bool:
    return os.path.exists("/data/data/com.termux")


def listen() -> str:
    if _is_termux():
        try:
            result = subprocess.run(
                ["termux-speech-to-text"], capture_output=True, text=True, timeout=15
            )
            text = result.stdout.strip()
            if text:
                print(f"You: {text}")
            return text
        except Exception as e:
            print(f"[listener] termux-speech-to-text failed: {e}")
            return ""

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
