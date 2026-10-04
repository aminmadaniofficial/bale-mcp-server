"""
Authentication and account management tools for Bale MCP Server.
"""

from typing import Any, Dict, List, Optional
from mcp.server.mcpserver import MCPServer
from bale_mcp.session_manager import session_manager


def register_auth_tools(server: MCPServer) -> None:
    """Registers authentication and account management tools on the MCP server."""

    @server.tool(
        name="bale_list_sessions",
        description="List all available Bale user sessions/accounts stored locally on disk.",
    )
    def bale_list_sessions() -> List[Dict[str, Any]]:
        """
        Retrieves a list of all local session files (.bale) along with user ID, name, username,
        and whether the session is currently active.
        """
        return session_manager.list_sessions()

    @server.tool(
        name="bale_connect_session",
        description="Connect to or switch to a specific Bale user account using session name or phone number.",
    )
    async def bale_connect_session(session_name: str) -> Dict[str, Any]:
        """
        Switches the active client connection to the specified account session.

        Args:
            session_name: Name of the session, phone number (e.g. '989302359914'), or session file path.
        """
        try:
            return await session_manager.connect(session_identifier=session_name)
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_get_me",
        description="Get profile information and connection status of the currently active Bale account.",
    )
    async def bale_get_me() -> Dict[str, Any]:
        """
        Returns account metadata including user ID, display name, username, and bio for the currently active user.
        """
        try:
            return await session_manager.get_me_summary()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @server.tool(
        name="bale_auth_request_code",
        description="Initiate interactive phone login by requesting an SMS/Bale verification code for a new account.",
    )
    async def bale_auth_request_code(phone_number: int) -> Dict[str, Any]:
        """
        Sends an authentication code to the specified phone number.

        Args:
            phone_number: Phone number in international format without plus, e.g. 989123456789.
        """
        try:
            return await session_manager.start_phone_auth(phone_number=phone_number)
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_auth_verify_code",
        description="Verify the authentication code received via SMS/Bale to complete login and save session.",
    )
    async def bale_auth_verify_code(
        code: str,
        transaction_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifies the code sent during phone authentication.

        Args:
            code: The verification code received via SMS or Bale.
            transaction_hash: Optional transaction hash returned by bale_auth_request_code.
        """
        try:
            return await session_manager.verify_code(code=code, transaction_hash=transaction_hash)
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_auth_verify_password",
        description="Submit Two-Factor Authentication (2FA) cloud password if required during login.",
    )
    async def bale_auth_verify_password(
        password: str,
        transaction_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submits the 2FA password to complete authentication.

        Args:
            password: The Two-Factor Authentication password.
            transaction_hash: Optional transaction hash from previous authentication step.
        """
        try:
            return await session_manager.verify_password(password=password, transaction_hash=transaction_hash)
        except Exception as e:
            return {"success": False, "error": str(e)}

    @server.tool(
        name="bale_disconnect",
        description="Disconnect the currently active Bale user account.",
    )
    async def bale_disconnect() -> Dict[str, Any]:
        """
        Disconnects the active account session.
        """
        return await session_manager.disconnect()
