"""
Tests for session manager and session file resolution.
"""

from pathlib import Path
from bale_mcp.session_manager import session_manager
from bale_mcp.config import config


def test_session_manager_list():
    sessions = session_manager.list_sessions()
    assert isinstance(sessions, list)
    # Both active sessions should be discovered
    if sessions:
        first = sessions[0]
        assert "session_name" in first
        assert "file_path" in first


def test_resolve_session_path():
    path = session_manager._resolve_session_path("test_session")
    assert path.name == "test_session.bale"
