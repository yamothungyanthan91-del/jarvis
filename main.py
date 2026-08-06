"""
Jarvis — a personal AI voice assistant.
Run: python main.py

Jarvis keeps listening while it's talking, so you can jump in anytime:
- Say "stop" to immediately cut off whatever it's saying.
- Just start talking about something new — it'll follow you there, no
  special command needed.
"""
from core.brain import Brain
from core.listener import listen
from core.voice import speak, stop_speaking
from config import ASSISTANT_NAME, USER_TITLE

EXIT_WORDS = {"exit", "quit", "goodbye", "shut down", "shutdown"}
STOP_WORDS = {"stop", "stop talking", "wait", "hold on", "quiet"}


def main():
    brain = Brain()
    speak(f"{ASSISTANT_NAME} online. At your service, {USER_TITLE}.")

    while True:
        user_text = listen()
        if not user_text:
            continue

        cleaned = user_text.lower().strip(".! ")

        if cleaned in EXIT_WORDS:
            speak(f"Shutting down. Goodbye, {USER_TITLE}.")
            break

        if cleaned in STOP_WORDS:
            stop_speaking()
            print(f"Jarvis: (stopped) Go ahead, {USER_TITLE}.")
            continue

        # Anything else — including a brand new topic — just gets answered
        # normally. Saying "stop" first cuts off the old reply; the next
        # thing you say becomes the new question, no special phrasing needed.
        stop_speaking()
        reply = brain.think(user_text)
        speak(reply)


if __name__ == "__main__":
    main()
