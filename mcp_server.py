"""stdio MCP adapter to an existing Joker HTTP API."""

from mcp.server.fastmcp import FastMCP

from http_client import request_joke

mcp = FastMCP("joker")


@mcp.tool()
def find_joke(context: str) -> dict:
    """Find a joke related to the given short topic or situation.

    Use when the user wants humor. This tool retrieves a joke, not a solution.
    """
    return request_joke(context)


if __name__ == "__main__":
    mcp.run(transport="stdio")
