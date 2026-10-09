import asyncio
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters

BASE_DIR = Path(__file__).resolve().parent
SERVER = BASE_DIR / "gmail_mcp_server" / "server.py"

async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        cwd=str(BASE_DIR),
    )

    async with Client(params) as client:
        print("MCP CONNECTED!")

        result = await client.call_tool(
            "search_emails",
            {
                "query": "in:anywhere",
                "max_results": 5
            }
        )

        print("GMAIL RESULT:")
        print(result)

asyncio.run(main())