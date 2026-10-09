# Gmail MCP Assistant
### An LLM-Powered Gmail Assistant Using the Model Context Protocol (MCP)

## Overview

**Gmail MCP Assistant** is a local AI-powered application that enables users to interact with their Gmail mailbox through a simple conversational web interface.

The application combines a Large Language Model (LLM), the Model Context Protocol (MCP), FastAPI, and the Gmail API to interpret natural-language requests and execute the corresponding email operations through dedicated MCP tools.

The project demonstrates how an LLM-based application can connect to an external service through a standardized tool interface rather than directly accessing the service.

## Key Features

- **Email Search:** Search Gmail messages using Gmail search queries.
- **Email Filtering:** Filter messages by sender, subject, unread status, and date range.
- **Email Retrieval:** Retrieve message details, including sender, recipient, subject, date, and available message content.
- **Email Sending:** Compose and send plain-text emails through Gmail.
- **Email Replies:** Reply to existing messages using their message IDs.
- **Natural-Language Interaction:** Express email requests in everyday language through the web interface.
- **MCP Tool Integration:** Discover and invoke Gmail operations exposed by the MCP server.
- **OAuth 2.0 Authentication:** Authorize access to Gmail through Google's authentication flow.

## System Architecture

The application follows a modular architecture that separates user interaction, language-model reasoning, tool orchestration, and Gmail integration.

```text
                 User
                  |
                  v
             Web Interface
                  |
                  v
               FastAPI
                  |
                  v
          LLM via OpenRouter
                  |
                  v
              MCP Client
                  |
             MCP Protocol
                  |
                  v
           Gmail MCP Server
                  |
                  v
              Gmail API
                  |
                  v
                Gmail
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| Web Interface | Accepts natural-language requests and displays responses. |
| FastAPI | Provides the backend API and coordinates request processing. |
| LLM / OpenRouter | Interprets user requests and selects appropriate tools. |
| MCP Client | Discovers available tools, invokes them, and receives their results. |
| Gmail MCP Server | Implements Gmail operations as MCP tools. |
| Gmail API | Provides authorized access to Gmail functionality. |
| Google OAuth 2.0 | Authorizes the application to access the user's mailbox. |

### Request Workflow

1. The user submits a request through the web interface.
2. FastAPI receives the request and invokes the application logic.
3. The LLM interprets the request and determines whether a Gmail tool is needed.
4. The MCP client communicates with the Gmail MCP server and invokes the selected tool.
5. The MCP server executes the corresponding Gmail API operation.
6. The result is returned through the MCP client to the application.
7. The LLM generates a response based on the tool result, and the interface displays it.

## Technology Stack

- **Programming Language:** Python
- **Backend Framework:** FastAPI
- **AI / LLM Integration:** OpenRouter API
- **Tool Integration Protocol:** Model Context Protocol (MCP)
- **MCP Implementation:** MCP Python SDK
- **Email Service:** Gmail API
- **Authentication:** Google OAuth 2.0
- **Frontend:** HTML, CSS, and JavaScript
- **Development Environment:** Visual Studio Code

## MCP Tools

The Gmail MCP server exposes five tools.

| Tool | Description |
|---|---|
| `search_emails` | Searches messages using Gmail search syntax. |
| `filter_emails` | Filters messages using sender, subject, unread status, and date criteria. |
| `get_email` | Retrieves an existing message by its Gmail message ID. |
| `send_email` | Sends a new plain-text email. |
| `reply_email` | Replies to an existing message using its message ID. |

These tools provide a structured interface through which the LLM-powered application can interact with Gmail.

## Project Structure

```text
gmail-mcp-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── static/
│       └── index.html
├── gmail_mcp_server/
│   └── server.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── test_mcp.py
```

**File descriptions**

- `app/main.py` — FastAPI application, LLM integration, MCP client orchestration, and chat endpoint.
- `app/static/index.html` — Web interface for interacting with the assistant.
- `gmail_mcp_server/server.py` — MCP server implementation and Gmail tools.
- `test_mcp.py` — Script for testing MCP connectivity and tool functionality.
- `requirements.txt` — Python package dependencies.
- `.env.example` — Example environment configuration without real credentials.
- `.gitignore` — Excludes local environment files, credentials, and generated files.

## Prerequisites

Before running the application, ensure that you have:

- Python 3.10 or a compatible version supported by the installed dependencies.
- Git.
- Visual Studio Code or another Python development environment.
- A Google account with Gmail.
- A Google Cloud project with the Gmail API enabled.
- An OpenRouter API key and access to a compatible model.
- Google OAuth desktop application credentials.

## Installation and Configuration

### 1. Clone the Repository

```bash
git clone https://github.com/Negma-Abderhman/gmail-mcp-assistant.git
cd gmail-mcp-assistant
```

### 2. Create a Virtual Environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure OpenRouter

Create a local `.env` file in the project root. Use `.env.example` as a reference, and configure the variables expected by `app/main.py`.

Example:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
MCP_SERVER_PATH=./gmail_mcp_server/server.py
```

Replace the placeholder with your own API key. The selected model must be available through OpenRouter and support the tool-calling format used by the application.

Free model availability and usage limits may change.

### 5. Configure Google OAuth

1. Open the Google Cloud Console.
2. Create or select a Google Cloud project.
3. Enable the Gmail API.
4. Configure the Google Auth Platform and OAuth consent screen.
5. Create an OAuth 2.0 Client ID for a Desktop application.
6. Download the client credentials JSON file.
7. Place the downloaded file at:

   `gmail_mcp_server/credentials.json`

8. Configure the OAuth consent screen and test users as required by your Google account setup.

On first authorized use, Google may open a browser window to request consent. The application stores the resulting token locally in `gmail_mcp_server/token.json`.

**Security:** Never commit `.env`, `credentials.json`, or `token.json` to version control.

## Running the Application

From the project root, activate the virtual environment and run:

```bash
uvicorn app.main:app --reload
```

Open the application in your browser:

http://127.0.0.1:8000

The FastAPI application launches the Gmail MCP server as a subprocess when processing a chat request.

The `--reload` option is intended for local development, not production deployment.

## Example User Requests

The following requests illustrate the intended interaction style:

**Search emails**
- "Search my latest five emails."
- "Find my unread emails."

**Filter emails**
- "Find unread emails from Google."
- "Find emails with a specific subject."

**Read an email**
- "Retrieve the email with this message ID."

**Send an email**
- "Send a test email to my test address with subject 'MCP Gmail Test'."

**Reply to an email**
- "Reply to the selected message and say, 'Thank you for your email.'"

Actual results depend on the authenticated mailbox, the request parameters, and the availability of the configured LLM and external services.

## Testing and Evaluation

The application can be evaluated through functional and integration tests covering the implemented Gmail operations.

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| T01 | MCP server connection | The MCP client connects successfully. |
| T02 | Tool discovery | The five Gmail tools are listed. |
| T03 | Email search | Matching messages are returned from Gmail. |
| T04 | Email filtering | Messages matching the supplied criteria are returned. |
| T05 | Email retrieval | The requested message details are retrieved. |
| T06 | Email sending | Gmail accepts the send request and the message is verified in the recipient mailbox. |
| T07 | Email reply | A reply is sent to the original sender and associated with the intended conversation. |
| T08 | No matching messages | The application reports that no matching results were found. |
| T09 | Error handling | Failures are surfaced without falsely reporting success. |

**Evaluation procedure**

1. Execute each test using a controlled Gmail test account.
2. Record the input, expected result, actual result, and pass/fail status.
3. Verify important outcomes against Gmail itself rather than relying only on the assistant's response.
4. Record errors, limitations, and any cases requiring manual intervention.

The table above defines the proposed test plan; individual results should be reported only after the corresponding tests have been executed and verified.

Further evaluation can measure tool-selection accuracy, parameter-extraction accuracy, task success rate, response latency, and error-handling behavior over a predefined set of test cases.

## Security and Limitations

- Gmail access is authorized through Google OAuth 2.0.
- API keys and OAuth credentials must be stored locally and excluded from Git.
- Email sending and replying are real external actions, not simulations.
- Users should verify recipients and message content before performing sensitive actions.
- The current application is intended for local development.
- LLM tool selection can be incorrect; tool arguments and operation results should be validated.
- External API availability, model capabilities, quotas, and authentication state may affect operation.

## Future Improvements

Potential extensions include:

- Automated evaluation with a larger set of test cases.
- Stronger validation of tool arguments and recipient addresses.
- Explicit user confirmation before sending or replying to emails.
- Improved error messages and structured logging.
- Unit tests and automated integration tests.
- Support for additional services through MCP tools.
- Production-ready authentication, access control, and deployment.

## Conclusion

Gmail MCP Assistant demonstrates how a conversational AI application can integrate an external email service through the Model Context Protocol. By combining an LLM, an MCP client, a dedicated MCP server, and the Gmail API, the project provides a modular foundation for natural-language email interaction.

The implementation serves as an educational demonstration of LLM tool calling, MCP-based integration, OAuth authorization, and functional evaluation.

## Author and Repository

**Project:** Gmail MCP Assistant  
**Repository:** https://github.com/Negma-Abderhman/gmail-mcp-assistant

