"""
The brain: sends conversation to Groq's LLM and returns a reply.

Includes:
- Live date/time awareness (no internet needed — pulled from the device clock)
- Persistent memory of facts you ask it to remember (stored in memory.json)
- Real-time web info (news, current events) via Groq's "compound" model,
  which has built-in web search — automatically used when your question
  needs current information.
- Streamed replies: think_stream() yields text sentence-by-sentence as
  Groq generates it, so Jarvis can start speaking the first sentence
  while the rest of the reply is still being written — this is what
  makes responses feel noticeably faster.
"""
from datetime import datetime
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, ASSISTANT_NAME, USER_TITLE
from core.memory import facts_as_text, save_fact

client = Groq(api_key=GROQ_API_KEY)

# Specific phrases that suggest the question needs live web info.
# Kept narrow and multi-word on purpose — a broad single word like "current"
# or "right now" was firing on ordinary sentences (e.g. "quarantine right
# now") and routing them to the search model by accident.
SEARCH_KEYWORDS = (
    "search for", "look up", "google ", "the news", "in the news",
    "today's news", "latest news", "the weather", "weather today",
    "weather like", "who won", "score of", "stock price", "price of",
)

SEARCH_MODEL = "groq/compound"  # Groq's free model with built-in web search

# A chunk gets spoken once it ends with one of these AND has enough
# content to be worth a separate TTS call (avoids choppy one-word audio).
SENTENCE_ENDERS = (".", "!", "?", "\n")
MIN_CHUNK_LEN = 12


def _build_system_prompt() -> str:
    now = datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
    return f"""You are {ASSISTANT_NAME}, a personal AI assistant inspired by
Tony Stark's J.A.R.V.I.S. from Iron Man. You address the user as "{USER_TITLE}".

The current date and time is: {now}.

Personality:
- Calm, witty, dryly humorous, unfailingly polite and a little formal.
- Efficient — you give useful, concise answers, not rambling ones.
- Confident and a bit sardonic, but always genuinely helpful and loyal.
- You may make a light quip occasionally, but never at the cost of clarity.

Known facts about {USER_TITLE} and their circle (remembered from past
conversations):
{facts_as_text()}

Keep spoken replies conversational and reasonably short, since they will be
read aloud with text-to-speech. Avoid markdown formatting, bullet points, or
anything that doesn't sound natural when spoken.
"""


class Brain:
    def __init__(self, history_limit: int = 20):
        self.history_limit = history_limit
        self.messages = [{"role": "system", "content": _build_system_prompt()}]

    def _refresh_system_prompt(self):
        # Rebuild each turn so date/time and memory stay current
        self.messages[0] = {"role": "system", "content": _build_system_prompt()}

    def _trim_history(self):
        if len(self.messages) > self.history_limit:
            self.messages = [self.messages[0]] + self.messages[-(self.history_limit - 1):]

    def think_stream(self, user_text: str):
        """Yields the reply in speakable chunks (roughly one sentence at a
        time) as soon as each chunk is ready, instead of waiting for the
        entire reply to finish generating."""
        lowered = user_text.lower().strip()

        # "remember that ..." saves a fact — short-circuit, nothing to stream
        if lowered.startswith("remember that ") or lowered.startswith("remember "):
            fact = user_text.split(" ", 1)[1]
            if fact.lower().startswith("that "):
                fact = fact[5:]
            save_fact(fact)
            reply = f"Noted, {USER_TITLE}. I'll remember that {fact}."
            self.messages.append({"role": "user", "content": user_text})
            self.messages.append({"role": "assistant", "content": reply})
            yield reply
            return

        self._refresh_system_prompt()
        self.messages.append({"role": "user", "content": user_text})

        needs_search = any(kw in lowered for kw in SEARCH_KEYWORDS)

        if needs_search:
            # The search model has a small request-size limit, so it only
            # gets the current question, not the full history — and it
            # doesn't support streaming, so it's spoken as one chunk.
            # If it fails for any reason, fall back to the regular model
            # rather than crashing the whole session.
            try:
                search_messages = [
                    {"role": "system", "content": (
                        f"You are {ASSISTANT_NAME}, a helpful assistant with live "
                        f"web search. Answer briefly and conversationally, since "
                        f"this will be read aloud."
                    )},
                    {"role": "user", "content": user_text},
                ]
                response = client.chat.completions.create(
                    model=SEARCH_MODEL,
                    messages=search_messages,
                )
                reply = response.choices[0].message.content.strip()
                self.messages.append({"role": "assistant", "content": reply})
                self._trim_history()
                yield reply
                return
            except Exception:
                yield "I couldn't reach a live search just now, sir, but let me try to help anyway."
                # falls through to the normal model below

        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=self.messages,
            temperature=0.7,
            max_tokens=512,
            stream=True,
        )

        buffer = ""
        full_reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if not delta:
                continue
            buffer += delta
            full_reply += delta
            if buffer.rstrip().endswith(SENTENCE_ENDERS) and len(buffer.strip()) >= MIN_CHUNK_LEN:
                yield buffer.strip()
                buffer = ""

        if buffer.strip():
            yield buffer.strip()

        self.messages.append({"role": "assistant", "content": full_reply})
        self._trim_history()

    def think(self, user_text: str) -> str:
        """Non-streaming convenience wrapper — collects the full reply.
        Prefer think_stream() for anything spoken aloud."""
        return " ".join(self.think_stream(user_text))
