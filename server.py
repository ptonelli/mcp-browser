import os
import base64
import aiohttp
import mcp
import asyncio
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import mcp.types as types
from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from PIL import Image
from io import BytesIO

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 8000))

LOG_LEVEL: str = "info"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
REQUEST_TIMEOUT: int = 30
MAX_RETRIES: int = 3

# Create an MCP server with environment variable configuration
mcp = FastMCP("browser", stateless_http=True)


def get_image_dimensions(image_data: bytes) -> Tuple[int, int]:
    """
    Get image dimensions from image data.

    Args:
        image_data: Raw image bytes

    Returns:
        Tuple[int, int]: (width, height) or (0, 0) if unable to determine
    """
    try:
        with Image.open(BytesIO(image_data)) as img:
            return img.size  # Returns (width, height)
    except Exception:
        return (0, 0)

async def fetch_images_from_soup(session: aiohttp.ClientSession, soup: BeautifulSoup, base_url: str, max_images: int = 5) -> List[types.ImageContent]:
    """
    Extract and fetch images from a BeautifulSoup object, sorted by resolution (largest first).

    Args:
        session: The aiohttp session to use for requests
        soup: BeautifulSoup object of the parsed HTML
        base_url: Base URL to resolve relative image URLs
        max_images: Maximum number of images to fetch

    Returns:
        List[types.ImageContent]: List of fetched images sorted by size (largest first)
    """
    images = soup.find_all("img", src=True)
    headers = {"User-Agent": USER_AGENT}

    # List to store image data with dimensions for sorting
    image_data_list = []

    for img in images:
        img_src = img.get("src")
        if not img_src:
            continue

        # Convert relative URLs to absolute
        img_url = urljoin(base_url, img_src)

        try:
            # Fetch the image with shorter timeout for individual images
            async with session.get(img_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as img_response:
                if img_response.status == 200:
                    img_data = await img_response.read()

                    # Get image dimensions
                    width, height = get_image_dimensions(img_data)
                    pixel_count = width * height

                    # Get content type, default to jpeg if not specified
                    content_type = img_response.headers.get('content-type', 'image/jpeg')

                    # Store image info for sorting
                    image_info = {
                        'data': img_data,
                        'content_type': content_type,
                        'width': width,
                        'height': height,
                        'pixel_count': pixel_count,
                        'url': img_url
                    }
                    image_data_list.append(image_info)

        except Exception as e:
            # If individual image fails, continue with others
            continue

    # Sort images by pixel count (largest first)
    image_data_list.sort(key=lambda x: x['pixel_count'], reverse=True)

    # Convert to ImageContent objects, limiting to max_images
    image_content_list = []
    for i, img_info in enumerate(image_data_list[:max_images]):
        image_content = types.ImageContent(
            type="image",
            data=base64.b64encode(img_info['data']).decode('utf-8'),
            mimeType=img_info['content_type']
        )
        image_content_list.append(image_content)

    return image_content_list

@mcp.tool()
async def browse_webpage(url: str, selectors: dict = None, capture_images: bool = True, max_images: int = 5) -> List[types.Content]:
    """
    Browse a webpage and extract its content including images.

    Args:
        url (str): The URL of the webpage to browse
        selectors (dict, optional): CSS selectors for extracting specific content
        capture_images (bool): Whether to capture and return images from the page
        max_images (int): Maximum number of images to capture (default: 5)

    Returns:
        List[types.Content]: The extracted webpage content including text and images (sorted by size)
    """
    if selectors is None:
        selectors = {}

    async with aiohttp.ClientSession() as session:
        try:
            headers = {"User-Agent": USER_AGENT}
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

            # Fetch the main page
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status >= 400:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Error: HTTP {response.status} - Failed to fetch webpage",
                        )
                    ]

                # Handle encoding issues
                try:
                    html = await response.text()
                except UnicodeDecodeError:
                    try:
                        content = await response.read()
                        for encoding in ['utf-8', 'iso-8859-1', 'windows-1252', 'cp1252']:
                            try:
                                html = content.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
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

                # Start with text content
                content_list = [types.TextContent(type="text", text=str(result))]

                # Fetch images if requested (now sorted by size)
                if capture_images:
                    image_contents = await fetch_images_from_soup(session, soup, url, max_images)
                    content_list.extend(image_contents)

                return content_list

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
