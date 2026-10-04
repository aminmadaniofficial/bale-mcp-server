"""
Configuration module for Bale MCP Server.
"""

from pathlib import Path
import os


class Config:
    """Server configuration loaded from environment or defaults."""

    # Base directory for the MCP server
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Directory where .bale session files are stored
    SESSIONS_DIR: Path = Path(
        os.getenv("BALE_SESSIONS_DIR", str(BASE_DIR / "sessions"))
    ).resolve()

    # Preselected session name or phone number
    ACTIVE_SESSION: str = os.getenv("BALE_ACTIVE_SESSION", "")

    # Auto connect to the first available session if active session is not specified
    AUTO_CONNECT: bool = os.getenv("BALE_AUTO_CONNECT", "true").lower() in ("true", "1", "yes")

    # Logging level
    LOG_LEVEL: str = os.getenv("BALE_LOG_LEVEL", "INFO").upper()

    @classmethod
    def ensure_sessions_dir(cls) -> Path:
        """Ensure the sessions directory exists and return its path."""
        cls.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        return cls.SESSIONS_DIR


config = Config()
