import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI

from mcp import Client, StdioServerParameters


# ============================================================
# Load environment variables
# ============================================================

load_dotenv()


# ============================================================
# Project paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "app" / "static"

MCP_SERVER = Path(
    os.getenv(
        "MCP_SERVER_PATH",
        str(BASE_DIR / "gmail_mcp_server" / "server.py")
    )
).resolve()


# ============================================================
# OpenRouter configuration
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)


# OpenRouter is OpenAI-compatible.
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(title="Gmail MCP Assistant")

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# ============================================================
# Request model
# ============================================================

class ChatRequest(BaseModel):
    message: str


# ============================================================
# MCP tool -> OpenAI/OpenRouter tool format
# ============================================================

def mcp_tool_to_openrouter(tool: Any) -> dict[str, Any]:
    """
    Convert an MCP tool definition to the OpenAI-compatible
    tool format expected by OpenRouter Chat Completions.
    """

    schema = getattr(tool, "inputSchema", None)

    if schema is None:
        schema = getattr(tool, "input_schema", None)

    if schema is None:
        schema = {
            "type": "object",
            "properties": {}
        }

    # MCP SDK may return a Pydantic model.
    if hasattr(schema, "model_dump"):
        schema = schema.model_dump(
            by_alias=True,
            exclude_none=True
        )

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        },
    }


# ============================================================
# Convert MCP result to text
# ============================================================

def result_to_text(result: Any) -> str:

    structured = getattr(
        result,
        "structured_content",
        None
    )

    if structured is not None:
        return json.dumps(
            structured,
            ensure_ascii=False,
            default=str
        )

    content = getattr(
        result,
        "content",
        None
    ) or []

    parts = []

    for item in content:

        if getattr(item, "type", None) == "text":
            parts.append(
                getattr(item, "text", "")
            )
        else:
            parts.append(str(item))

    return "\n".join(parts)


# ============================================================
# Main AI + MCP Agent
# ============================================================

async def run_agent(user_message: str) -> dict[str, Any]:

    # --------------------------------------------------------
    # Check OpenRouter key
    # --------------------------------------------------------

    if not OPENROUTER_API_KEY:
        return {
            "answer": (
                "Missing OPENROUTER_API_KEY in .env"
            ),
            "tools_used": [],
        }


    # --------------------------------------------------------
    # Start Gmail MCP server
    # --------------------------------------------------------

    server_params = StdioServerParameters(
        command=sys.executable,

        args=[
            str(MCP_SERVER)
        ],

        env={
            "PATH": os.getenv("PATH", ""),
            "HOME": os.getenv("HOME", ""),
        },

        cwd=str(BASE_DIR),
    )


    # --------------------------------------------------------
    # Connect MCP client to MCP server
    # --------------------------------------------------------

    async with Client(server_params) as mcp_client:

        # ----------------------------------------------------
        # Get available MCP tools
        # ----------------------------------------------------

        listed = await mcp_client.list_tools()

        tools = [
            mcp_tool_to_openrouter(tool)
            for tool in listed.tools
        ]


        # ----------------------------------------------------
        # System instructions
        # ----------------------------------------------------

        instructions = """
You are Gmail MCP Assistant for a university MCP assignment.

You have access to Gmail through an MCP client and Gmail MCP server.

Available operations include:
- search emails
- filter emails
- read a specific email
- send an email
- reply to an email

IMPORTANT RULES:

1. Always use MCP tools to perform Gmail operations.
2. Never pretend that an email operation happened if the MCP tool was not called.
3. For requests about an existing email, search for the email first.
4. Never invent a Gmail message ID.
5. Never invent email addresses.
6. For sending or replying, only perform the action when the user explicitly asks.
7. Sending and replying are real external side effects.
8. After using a tool, explain the actual result briefly.
9. Keep normal answers concise.
10. If no matching email is found, clearly tell the user.
"""


        # ----------------------------------------------------
        # Conversation messages
        # ----------------------------------------------------

        messages = [
            {
                "role": "system",
                "content": instructions,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]


        # ----------------------------------------------------
        # Keep track of MCP tools used
        # ----------------------------------------------------

        tools_used = []


        # ----------------------------------------------------
        # Tool calling loop
        # ----------------------------------------------------

        for _ in range(6):

            # -----------------------------------------------
            # Ask OpenRouter
            # -----------------------------------------------

            response = await asyncio.to_thread(
                client.chat.completions.create,

                model=OPENROUTER_MODEL,

                messages=messages,

                tools=tools,

                tool_choice="auto",
            )


            # -----------------------------------------------
            # Get assistant message
            # -----------------------------------------------

            assistant_message = response.choices[0].message


            # -----------------------------------------------
            # No tool call -> final answer
            # -----------------------------------------------

            if not assistant_message.tool_calls:

                answer = assistant_message.content or ""

                return {
                    "answer": answer,
                    "tools_used": tools_used,
                }


            # -----------------------------------------------
            # Add assistant message to conversation
            # -----------------------------------------------

            assistant_dict = {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [],
            }


            for tool_call in assistant_message.tool_calls:

                assistant_dict["tool_calls"].append(
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                )


            messages.append(assistant_dict)


            # -----------------------------------------------
            # Execute each requested MCP tool
            # -----------------------------------------------

            for tool_call in assistant_message.tool_calls:

                tool_name = tool_call.function.name

                arguments_text = (
                    tool_call.function.arguments
                    or "{}"
                )


                try:

                    arguments = json.loads(
                        arguments_text
                    )

                except json.JSONDecodeError:

                    arguments = {}


                # -------------------------------------------
                # Call actual MCP tool
                # -------------------------------------------

                result = await mcp_client.call_tool(
                    tool_name,
                    arguments
                )


                output_text = result_to_text(result)


                # -------------------------------------------
                # Save tool name
                # -------------------------------------------

                if tool_name not in tools_used:
                    tools_used.append(tool_name)


                # -------------------------------------------
                # Return tool result to the LLM
                # -------------------------------------------

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": output_text,
                    }
                )


        # ----------------------------------------------------
        # Safety limit
        # ----------------------------------------------------

        return {
            "answer": (
                "The tool loop reached its safety limit."
            ),
            "tools_used": tools_used,
        }


# ============================================================
# Home page
# ============================================================

@app.get("/")
async def index():

    return FileResponse(
        STATIC_DIR / "index.html"
    )


# ============================================================
# Chat endpoint
# ============================================================

@app.post("/api/chat")
async def chat(request: ChatRequest):

    if not OPENROUTER_API_KEY:

        return {
            "answer": (
                "Missing OPENROUTER_API_KEY in .env"
            ),
            "tools_used": [],
        }


    try:

        return await run_agent(
            request.message
        )

    except Exception as exc:

        return {
            "answer": (
                f"Error: {type(exc).__name__}: {exc}"
            ),
            "tools_used": [],
        }