"""
Config loader.
Reads secrets from environment variables (populated from a local .env file
that is NEVER committed to git — see .gitignore).
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from a .env file if present

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Voice settings (Edge TTS). Try "en-GB-RyanNeural" or
# "en-US-GuyNeural" for a deeper, more JARVIS-like tone.
TTS_VOICE = os.getenv("TTS_VOICE", "en-GB-RyanNeural")

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jarvis")
USER_TITLE = os.getenv("USER_TITLE", "sir")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found. Copy .env.example to .env and add your key."
    )
