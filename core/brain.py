"""
The brain: sends conversation to Groq's LLM and returns a reply.

Includes:
- Live date/time awareness (no internet needed — pulled from the device clock)
- Persistent memory of facts you ask it to remember (stored in memory.json)
- Real-time web info (news, current events) via Groq's "compound" model,
  which has built-in web search — automatically used when your question
  needs current information.
"""
from datetime import datetime
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, ASSISTANT_NAME, USER_TITLE
from core.memory import facts_as_text, save_fact

client = Groq(api_key=GROQ_API_KEY)

# Keywords that suggest the question needs live/real-time info from the web
SEARCH_KEYWORDS = (
    "news", "today", "latest", "current", "currently", "right now",
    "weather", "score", "stock", "price of", "who won", "happening",
)

SEARCH_MODEL = "groq/compound"  # Groq's free model with built-in web search


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

    def think(self, user_text: str) -> str:
        # "remember that ..." / "remember I ..." saves a fact for next time
        lowered = user_text.lower().strip()
        if lowered.startswith("remember that ") or lowered.startswith("remember "):
            fact = user_text.split(" ", 1)[1]
            if fact.lower().startswith("that "):
                fact = fact[5:]
            save_fact(fact)
            reply = f"Noted, {USER_TITLE}. I'll remember that {fact}."
            self.messages.append({"role": "user", "content": user_text})
            self.messages.append({"role": "assistant", "content": reply})
            return reply

        self._refresh_system_prompt()
        self.messages.append({"role": "user", "content": user_text})

        # Route questions needing live info to the search-capable model.
        # The search model has a much smaller request-size limit, so it gets
        # only the current question — not the full running conversation.
        needs_search = any(kw in lowered for kw in SEARCH_KEYWORDS)

        if needs_search:
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
        else:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=self.messages,
                temperature=0.7,
                max_tokens=512,
            )
        reply = response.choices[0].message.content.strip()

        self.messages.append({"role": "assistant", "content": reply})

        # keep the context window small so requests stay fast/cheap
        if len(self.messages) > self.history_limit:
            self.messages = [self.messages[0]] + self.messages[-(self.history_limit - 1):]

        return reply
