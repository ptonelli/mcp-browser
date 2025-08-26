import os
import aiohttp
import mcp
import asyncio
from bs4 import BeautifulSoup
from typing import List
import mcp.types as types
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 8000))

LOG_LEVEL: str = "info"
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)
REQUEST_TIMEOUT: int = 30
MAX_RETRIES: int = 3

# Create an MCP server with environment variable configuration
mcp = FastMCP("browser", stateless_http=True)

@mcp.tool()
async def browse_webpage(url: str, selectors: dict = None) -> List[types.TextContent]:
    """
    Browse a webpage and extract its content.

    Args:
        url (str): The URL of the webpage to browse
        selectors (dict, optional): CSS selectors for extracting specific content

    Returns:
        List[types.TextContent]: The extracted webpage content or error message

    The function performs the following steps:
    1. Fetches the webpage content with configured timeout and user agent
    2. Parses the HTML using BeautifulSoup
    3. Extracts basic page information (title, text, links)
    4. Applies any provided CSS selectors for specific content
    5. Handles various error conditions (timeout, HTTP errors, etc.)
    """
    if selectors is None:
        selectors = {}

    async with aiohttp.ClientSession() as session:
        try:
            headers = {"User-Agent": USER_AGENT}
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status >= 400:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Error: HTTP {response.status} - Failed to fetch webpage",
                        )
                    ]

                # Fix for encoding issues - let aiohttp auto-detect encoding
                try:
                    # First try with auto-detected encoding
                    html = await response.text()
                except UnicodeDecodeError:
                    # If that fails, try with common encodings
                    try:
                        # Get raw bytes first
                        content = await response.read()
                        # Try common encodings
                        for encoding in ['utf-8', 'iso-8859-1', 'windows-1252', 'cp1252']:
                            try:
                                html = content.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # If all encodings fail, use errors='replace' to avoid crashes
                            html = content.decode('utf-8', errors='replace')
                    except Exception:
                        return [types.TextContent(type="text", text="Error: Could not decode webpage content")]

                soup = BeautifulSoup(html, "html.parser")

                # Extract basic page information
                result = {
                    "title": soup.title.string if soup.title else None,
                    "text": soup.get_text(strip=True),
                    "links": [
                        {"text": link.text.strip(), "href": link.get("href")}
                        for link in soup.find_all("a", href=True)
                    ],
                }

                # Extract content using provided selectors
                if selectors:
                    for key, selector in selectors.items():
                        elements = soup.select(selector)
                        result[key] = [elem.get_text(strip=True) for elem in elements]

                return [types.TextContent(type="text", text=str(result))]

        except asyncio.TimeoutError:
            return [
                types.TextContent(
                    type="text", text="Error: Request timed out while fetching webpage"
                )
            ]
        except aiohttp.ClientError as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

if __name__ == "__main__":
    try:
        # Log startup information
        print(f"Log level is {LOG_LEVEL}")

        print(f"Starting MCP server on {HOST}:{PORT}")
        mcp.run(transport="http", host=HOST, port=PORT, path="/browser")
    except KeyboardInterrupt:
        print("\nShutting down MCP server...")
        print("system", "shutdown", True)
        sys.exit(0)
