# Jarvis

A personal AI voice assistant inspired by Iron Man's J.A.R.V.I.S. — powered by
the free Groq API (LLM) and Microsoft Edge's free neural text-to-speech.
Runs on both desktop (Windows/Linux/Mac) and Android (via Termux).

## Features
- Wake-free conversational loop — just talk, it listens and replies
- JARVIS-style personality (calm, witty, calls you "sir" by default — configurable)
- Free, no-cost stack: Groq (generous free tier) + Edge TTS (free)
- Cross-platform: auto-detects Termux vs desktop mic/speaker

## 1. Get a free Groq API key
Sign up at https://console.groq.com and create an API key.
**Never commit this key to GitHub** — it stays in your local `.env` file only.

## 2. Setup

### Desktop (Windows / Linux / Mac)
```bash
git clone https://github.com/<your-username>/jarvis.git
cd jarvis
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste in your real GROQ_API_KEY
python main.py
```
On Linux you also need `mpg123` for audio playback: `sudo apt install mpg123`

### Android (Termux)
```bash
pkg update && pkg install python git termux-api -y
git clone https://github.com/<your-username>/jarvis.git
cd jarvis
pip install groq edge-tts python-dotenv
cp .env.example .env
nano .env   # paste in your real GROQ_API_KEY, save with Ctrl+O then Ctrl+X
python main.py
```
Also install the **Termux:API** app from F-Droid/Play Store so
`termux-speech-to-text` and `termux-media-player` work.

## 3. Push to GitHub (without leaking your key)
The `.gitignore` already excludes `.env`, so your key is safe by default.
```bash
git init
git add .
git commit -m "Initial Jarvis assistant"
git branch -M main
git remote add origin https://github.com/<your-username>/jarvis.git
git push -u origin main
```

## Customize the voice
Edit `TTS_VOICE` in `.env`. Some deep, JARVIS-like options:
- `en-GB-RyanNeural` (default — crisp British, closest vibe to the movie)
- `en-US-GuyNeural`
- `en-GB-ThomasNeural`

Run `edge-tts --list-voices` to see all available voices.

## Project structure
```
jarvis/
├── main.py            # entry point / conversation loop
├── config.py           # loads secrets from .env
├── core/
│   ├── brain.py        # Groq LLM call + JARVIS personality prompt
│   ├── voice.py         # text-to-speech (Edge TTS)
│   └── listener.py      # speech-to-text (Termux or desktop mic)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Notes
- On PC without a mic set up, Jarvis automatically falls back to typed input.
- Conversation memory resets each time you restart the script (in-memory only for now).
