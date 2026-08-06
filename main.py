"""
Jarvis — a personal AI voice assistant.
Run: python main.py

Say "stop" right after Jarvis finishes a reply to skip past it, or just
start talking about something new — no special command needed.
Say "check my email" (or similar) to hear your unread Gmail count.
"""
from core.brain import Brain
from core.email_checker import check_unread_emails
from core.listener import listen
from core.voice import speak, stop_speaking
from config import ASSISTANT_NAME, USER_TITLE

EXIT_WORDS = {"exit", "quit", "goodbye", "shut down", "shutdown"}
STOP_WORDS = {"stop", "stop talking", "wait", "hold on", "quiet"}
EMAIL_KEYWORDS = ("check my email", "check email", "any emails", "my inbox", "new emails")


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

        if any(kw in cleaned for kw in EMAIL_KEYWORDS):
            reply = check_unread_emails()
            speak(reply)
            continue

        stop_speaking()
        for chunk in brain.think_stream(user_text):
            speak(chunk)


if __name__ == "__main__":
    main()
