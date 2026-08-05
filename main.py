"""
Jarvis — a personal AI voice assistant.
Run: python main.py
"""
from core.brain import Brain
from core.listener import listen
from core.voice import speak
from config import ASSISTANT_NAME, USER_TITLE

EXIT_WORDS = {"exit", "quit", "stop", "goodbye", "shut down"}


def main():
    brain = Brain()
    speak(f"{ASSISTANT_NAME} online. At your service, {USER_TITLE}.")

    while True:
        user_text = listen()
        if not user_text:
            continue

        if user_text.lower().strip(".! ") in EXIT_WORDS:
            speak(f"Shutting down. Goodbye, {USER_TITLE}.")
            break

        reply = brain.think(user_text)
        speak(reply)


if __name__ == "__main__":
    main()
