# Gmail MCP Assistant

A local assignment project that demonstrates:

Browser UI -> FastAPI app -> MCP Client -> Gmail MCP Server -> Gmail API
                         |
                         -> OpenAI Responses API

## 1. Requirements
- Python 3.10+
- VS Code
- A Google account with Gmail
- An OpenAI API key
- A Google Cloud project with Gmail API enabled

The official MCP Python SDK currently uses the v2 line and supports both MCP clients and servers. The Gmail API supports authorized mailbox access and sending email.

## 2. Google setup
1. Open Google Cloud Console.
2. Create/select a project.
3. Enable Gmail API.
4. Configure Google Auth Platform / OAuth consent screen.
5. Create an OAuth 2.0 Client ID for a Desktop app.
6. Download the JSON credentials.
7. Rename it to `credentials.json`.
8. Put it inside `gmail_mcp_server/`.

On first use, Google opens a browser for OAuth consent. A local `token.json` is then stored by the server. Do not commit either credentials.json or token.json.

## 3. Install
Create a virtual environment:

Windows:
python -m venv .venv
.venv\Scripts\activate

macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate

Install:
pip install -r requirements.txt

Copy `.env.example` to `.env` and add your OPENAI_API_KEY.

## 4. Run
From the project root:

uvicorn app.main:app --reload

Open:
http://127.0.0.1:8000

The FastAPI application launches the Gmail MCP server as a stdio subprocess when a chat request arrives.

## 5. Test commands in the UI
Examples:
- Search my unread emails from the last week.
- Find emails from example@gmail.com about the project.
- Send a test email to my address with subject "MCP Gmail Test".
- Reply to message ID <id> saying "Thanks, I received this."

For the assignment, use a test recipient you control.

## 6. MCP Inspector
You can inspect the server independently:

uv run mcp dev gmail_mcp_server/server.py

## 7. Security
- Never commit `.env`, `credentials.json`, or `token.json`.
- The UI is intended for local development.
- Sending/replying creates real Gmail side effects, so use a test mailbox.
