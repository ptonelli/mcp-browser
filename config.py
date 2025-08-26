"""
Configuration Settings for Web Browser MCP Server
==============================================

This module defines the settings and configuration options for the web browser MCP server
using pydantic for settings management and validation.

Settings include:
- Application name and version
- Logging level
- User agent string for HTTP requests
- Request timeout duration
- Maximum number of retries
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """
    Application settings class using pydantic_settings.

    Attributes:
        APP_NAME (str): Name of the application
        APP_VERSION (str): Current version of the application
        LOG_LEVEL (str): Logging level (default: "info")
        USER_AGENT (str): User agent string for HTTP requests
        REQUEST_TIMEOUT (int): Timeout for HTTP requests in seconds
        MAX_RETRIES (int): Maximum number of retry attempts for failed requests
    """

    APP_NAME: str = "web-browser-mcp-server"
    APP_VERSION: str = "0.2.0"
    LOG_LEVEL: str = "info"
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
