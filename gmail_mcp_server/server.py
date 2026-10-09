import base64
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mcp.server import MCPServer

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

mcp = MCPServer(
    "gmail-mcp-server",
    instructions=(
        "You provide Gmail operations. Search before acting when the user refers "
        "to an existing message. Never invent message IDs or email addresses. "
        "Sending and replying are real external side effects."
    ),
)


def get_gmail_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json is missing. Put Google OAuth desktop credentials "
                    "inside gmail_mcp_server/."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def headers_to_dict(headers: list[dict[str, str]]) -> dict[str, str]:
    return {
        h.get("name", "").lower(): h.get("value", "")
        for h in headers
    }


def decode_body(payload: dict[str, Any]) -> str:
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(
            payload["body"]["data"] + "=="
        ).decode("utf-8", errors="replace")

    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(
                    data + "=="
                ).decode("utf-8", errors="replace")

    return ""


def summarize_message(service, message: dict[str, Any]) -> dict[str, Any]:
    full = service.users().messages().get(
        userId="me",
        id=message["id"],
        format="full",
    ).execute()
    headers = headers_to_dict(full.get("payload", {}).get("headers", []))

    return {
        "id": full["id"],
        "thread_id": full.get("threadId"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": full.get("snippet", ""),
        "body": decode_body(full.get("payload", {}))[:5000],
        "label_ids": full.get("labelIds", []),
    }


@mcp.tool()
def search_emails(query: str, max_results: int = 10) -> dict[str, Any]:
    """Search Gmail using Gmail search syntax, e.g. from:alice@example.com is:unread."""
    service = get_gmail_service()
    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=min(max_results, 50),
    ).execute()

    messages = result.get("messages", [])
    items = [summarize_message(service, m) for m in messages]
    return {"query": query, "count": len(items), "emails": items}


@mcp.tool()
def filter_emails(
    sender: str = "",
    subject: str = "",
    unread: bool = False,
    after: str = "",
    before: str = "",
    max_results: int = 10,
) -> dict[str, Any]:
    """Filter Gmail by sender, subject, unread status and optional YYYY/MM/DD dates."""
    terms = []
    if sender:
        terms.append(f"from:{sender}")
    if subject:
        terms.append(f"subject:{subject}")
    if unread:
        terms.append("is:unread")
    if after:
        terms.append(f"after:{after}")
    if before:
        terms.append(f"before:{before}")

    query = " ".join(terms) if terms else "in:anywhere"
    return search_emails(query, max_results)


@mcp.tool()
def get_email(message_id: str) -> dict[str, Any]:
    """Get one Gmail message by its message ID."""
    service = get_gmail_service()
    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()
    return summarize_message(service, message)


def send_raw(service, raw_message: MIMEText, thread_id: str | None = None):
    encoded = base64.urlsafe_b64encode(
        raw_message.as_bytes()
    ).decode("utf-8")
    body = {"raw": encoded}
    if thread_id:
        body["threadId"] = thread_id

    return service.users().messages().send(
        userId="me",
        body=body,
    ).execute()


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send a new plain-text email from the authenticated Gmail account."""
    service = get_gmail_service()
    message = MIMEText(body, "plain", "utf-8")
    message["to"] = to
    message["subject"] = subject

    sent = send_raw(service, message)
    return {
        "status": "sent",
        "message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "to": to,
        "subject": subject,
    }


@mcp.tool()
def reply_email(message_id: str, body: str) -> dict[str, Any]:
    """Reply to an existing Gmail message by message ID."""
    service = get_gmail_service()
    original = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()

    headers = headers_to_dict(original.get("payload", {}).get("headers", []))
    sender = headers.get("from", "")
    subject = headers.get("subject", "")

    reply = MIMEText(body, "plain", "utf-8")
    reply["to"] = sender
    reply["subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"

    message_id_header = headers.get("message-id")
    if message_id_header:
        reply["In-Reply-To"] = message_id_header
        reply["References"] = message_id_header

    sent = send_raw(service, reply, thread_id=original.get("threadId"))
    return {
        "status": "replied",
        "message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "to": sender,
    }


if __name__ == "__main__":
    mcp.run()
