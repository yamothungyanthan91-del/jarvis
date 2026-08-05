"""
The brain: sends conversation to Groq's LLM and returns a reply.
"""
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, ASSISTANT_NAME, USER_TITLE

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a personal AI assistant inspired by
Tony Stark's J.A.R.V.I.S. from Iron Man. You address the user as "{USER_TITLE}".

Personality:
- Calm, witty, dryly humorous, unfailingly polite and a little formal.
- Efficient — you give useful, concise answers, not rambling ones.
- Confident and a bit sardonic, but always genuinely helpful and loyal.
- You may make a light quip occasionally, but never at the cost of clarity.

Keep spoken replies conversational and reasonably short, since they will be
read aloud with text-to-speech. Avoid markdown formatting, bullet points, or
anything that doesn't sound natural when spoken.
"""


class Brain:
    def __init__(self, history_limit: int = 20):
        self.history_limit = history_limit
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def think(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})

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
