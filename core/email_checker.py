"""
Checks your Gmail inbox for unread emails using IMAP (built into Python —
no extra installs needed). Uses a Gmail "App Password", which is simpler
to set up on a phone than full OAuth and doesn't require a browser login.

Setup (one-time, see README for full steps):
1. Turn on 2-Step Verification on your Google account.
2. Create an "App Password" at myaccount.google.com/apppasswords
3. Put your Gmail address and that app password in .env as
   GMAIL_ADDRESS and GMAIL_APP_PASSWORD.
"""
import email
import imaplib
from email.header import decode_header

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


def _decode(raw: str) -> str:
    parts = decode_header(raw)
    decoded = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            decoded += text.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += text
    return decoded


def check_unread_emails(max_results: int = 5) -> str:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return (
            "I don't have your Gmail credentials set up yet, sir. Add "
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD to your .env file to "
            "enable this."
        )

    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        imap.select("INBOX")

        status, data = imap.search(None, "UNSEEN")
        if status != "OK":
            return "I couldn't check your inbox just now, sir."

        ids = data[0].split()
        count = len(ids)

        if count == 0:
            imap.logout()
            return "No new emails, sir. Your inbox is all caught up."

        senders = []
        for msg_id in ids[-max_results:]:
            _, msg_data = imap.fetch(msg_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            sender = _decode(msg.get("From", "Unknown sender"))
            # Keep just the name/address, not the full header junk
            sender = sender.split("<")[0].strip(' "') or sender
            senders.append(sender)

        imap.logout()

        sender_list = ", ".join(senders)
        return (
            f"You have {count} unread email{'s' if count != 1 else ''}, sir. "
            f"Most recently from: {sender_list}."
        )

    except imaplib.IMAP4.error:
        return (
            "I couldn't log into your Gmail, sir. Please double check the "
            "app password in your .env file."
        )
    except Exception as e:
        return f"I ran into a problem checking your email, sir: {e}"
