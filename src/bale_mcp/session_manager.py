"""
Session Manager for Bale MCP Server.
Handles discovery, parsing, connecting, and lifecycle management for aiobale Client sessions.
"""

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import asyncio
import logging

from aiobale import Client
from aiobale.enums import AuthErrors
from bale_mcp.config import config
from bale_mcp.utils import serialize_entity

logger = logging.getLogger("bale_mcp.session_manager")


class SessionManager:
    """Manages Bale user sessions and the active aiobale Client instance."""

    def __init__(self):
        self._active_client: Optional[Client] = None
        self._active_session_name: Optional[str] = None
        self._pending_auth_transaction: Optional[str] = None
        self._pending_auth_phone: Optional[int] = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Returns True if a client is connected and active."""
        return self._active_client is not None and getattr(self._active_client, "session", None) is not None

    @property
    def active_session_name(self) -> Optional[str]:
        return self._active_session_name

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        Scans sessions directory and returns metadata for all available .bale session files.
        """
        sessions_dir = config.ensure_sessions_dir()
        found_files: List[Path] = list(sessions_dir.glob("*.bale"))

        # Also inspect fallback directory if primary sessions dir has no files
        fallback_dir = Path("/home/aminmadani/projects/aiobale-pkg/sessions")
        if not found_files and fallback_dir.exists():
            found_files.extend(list(fallback_dir.glob("*.bale")))

        sessions: List[Dict[str, Any]] = []
        for file_path in sorted(found_files):
            try:
                temp_client = Client(session_file=str(file_path))
                me_data = getattr(temp_client, "me", None)
                user_obj = getattr(me_data, "user", None) if me_data else None

                name = getattr(user_obj, "name", "") or ""
                username_val = getattr(user_obj, "username", None)
                username = getattr(username_val, "value", str(username_val)) if username_val else ""

                phone = file_path.stem
                is_active = self._active_session_name == file_path.stem

                sessions.append({
                    "session_name": file_path.stem,
                    "file_path": str(file_path),
                    "user_id": temp_client.id,
                    "name": name,
                    "username": username,
                    "phone": phone,
                    "is_active": is_active,
                })
            except Exception as e:
                logger.warning(f"Failed to parse session {file_path}: {e}")
                sessions.append({
                    "session_name": file_path.stem,
                    "file_path": str(file_path),
                    "error": str(e),
                    "is_active": False,
                })

        return sessions

    def _resolve_session_path(self, session_identifier: str) -> Path:
        """
        Resolves session file path by exact path, phone number, or session name.
        """
        # If user passed a full or relative path that exists
        path = Path(session_identifier)
        if path.exists() and path.is_file():
            return path.resolve()

        if path.with_suffix(".bale").exists():
            return path.with_suffix(".bale").resolve()

        # Check in config.SESSIONS_DIR
        sessions_dir = config.ensure_sessions_dir()
        candidate = sessions_dir / f"{session_identifier}.bale"
        if candidate.exists():
            return candidate

        candidate_raw = sessions_dir / session_identifier
        if candidate_raw.exists() and candidate_raw.is_file():
            return candidate_raw

        # Check fallback directory
        fallback_dir = Path("/home/aminmadani/projects/aiobale-pkg/sessions")
        if fallback_dir.exists():
            fb_candidate = fallback_dir / f"{session_identifier}.bale"
            if fb_candidate.exists():
                return fb_candidate
            fb_candidate_raw = fallback_dir / session_identifier
            if fb_candidate_raw.exists() and fb_candidate_raw.is_file():
                return fb_candidate_raw

        # If not found anywhere, default to sessions_dir with .bale suffix for creation
        return sessions_dir / f"{session_identifier}.bale"

    async def connect(self, session_identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        Connects to a specified session or the default/first available session.
        """
        async with self._lock:
            # If already connected to the same session, return current status
            if session_identifier and self._active_session_name == session_identifier and self._active_client:
                return await self.get_me_summary()

            # Determine which session to connect to
            target_path: Optional[Path] = None
            if session_identifier:
                target_path = self._resolve_session_path(session_identifier)
            elif config.ACTIVE_SESSION:
                target_path = self._resolve_session_path(config.ACTIVE_SESSION)
            else:
                available = self.list_sessions()
                if available:
                    target_path = Path(available[0]["file_path"])

            if not target_path or not target_path.exists():
                raise FileNotFoundError(
                    f"Session file not found. Please provide a valid session or start authentication. "
                    f"Checked path: {target_path}"
                )

            # Disconnect existing client if any
            if self._active_client:
                try:
                    await self._active_client.stop()
                except Exception as e:
                    logger.warning(f"Error stopping previous client: {e}")
                self._active_client = None
                self._active_session_name = None

            logger.info(f"Initializing aiobale Client with session: {target_path}")
            client = Client(session_file=str(target_path))

            # Start client in background without signal handling (to avoid interfering with MCP runner)
            await client.start(run_in_background=True, signal_handling=False)

            self._active_client = client
            self._active_session_name = target_path.stem

            return await self.get_me_summary()

    async def ensure_connected(self) -> Client:
        """
        Ensures the client is connected with an active, open WebSocket.
        If connection was lost, reset, or closed due to collision, automatically reconnects.
        """
        if self._active_client is None:
            if config.AUTO_CONNECT:
                await self.connect()
            else:
                raise RuntimeError("No active Bale session connected. Use bale_connect_session first.")

        session = getattr(self._active_client, "session", None)
        ws = getattr(session, "ws", None)
        is_closed = ws is None or ws.closed or not getattr(session, "_running", False)

        if is_closed:
            logger.info(f"Session '{self._active_session_name}' connection dropped or closed by server. Auto-reconnecting...")
            target_name = self._active_session_name
            try:
                await self._active_client.stop()
            except Exception:
                pass
            self._active_client = None
            await self.connect(target_name)

        return self._active_client

    async def get_client(self) -> Client:
        """
        Returns the active connected client, ensuring the connection is healthy.
        """
        return await self.ensure_connected()

    async def execute_with_retry(self, operation) -> Any:
        """
        Executes an API operation against the active client.
        If a connection error or socket collision occurs, attempts one automatic reconnection.
        """
        client = await self.ensure_connected()
        try:
            return await operation(client)
        except Exception as e:
            err_msg = str(e).lower()
            is_conn_error = any(kw in err_msg for kw in (
                "closed", "closing transport", "reset", "connection reset", "not connected", "broken pipe"
            ))
            if is_conn_error:
                logger.warning(f"Connection error detected ({e}). Reconnecting and retrying operation...")
                target_name = self._active_session_name
                if self._active_client:
                    try:
                        await self._active_client.stop()
                    except Exception:
                        pass
                    self._active_client = None
                await self.connect(target_name)
                client = self._active_client

                return await operation(client)
            raise

    async def get_me_summary(self) -> Dict[str, Any]:
        """
        Fetches current account information from the active client.
        """
        client = await self.get_client()

        me_data = getattr(client, "me", None)
        user_auth = getattr(me_data, "user", None) if me_data else None

        name = getattr(user_auth, "name", "") or ""
        username_val = getattr(user_auth, "username", None)
        username = getattr(username_val, "value", str(username_val)) if username_val else ""

        summary = {
            "status": "connected",
            "session_name": self._active_session_name,
            "user_id": client.id,
            "name": name,
            "username": username,
            "phone": self._active_session_name,
        }

        # Try to enrich with get_me call if possible
        try:
            full_me = await client.get_me()
            summary["about"] = getattr(full_me, "about", "")
            if getattr(full_me, "username", None):
                summary["username"] = str(full_me.username)
        except Exception as e:
            logger.debug(f"Could not fetch full user profile: {e}")

        return summary

    async def start_phone_auth(self, phone_number: int) -> Dict[str, Any]:
        """
        Requests an SMS/Bale verification code for the given phone number.
        """
        async with self._lock:
            sessions_dir = config.ensure_sessions_dir()
            session_file = sessions_dir / f"{phone_number}.bale"

            temp_client = Client(session_file=str(session_file))
            res = await temp_client.start_phone_auth(phone_number=phone_number)

            if isinstance(res, AuthErrors):
                return {
                    "success": False,
                    "error": str(res.name),
                    "message": f"Authentication failed with error: {res.name}"
                }

            self._pending_auth_transaction = res.transaction_hash
            self._pending_auth_phone = phone_number

            return {
                "success": True,
                "phone_number": phone_number,
                "transaction_hash": res.transaction_hash,
                "message": "Verification code has been sent. Call bale_auth_verify_code to complete login."
            }

    async def verify_code(self, code: str, transaction_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates the received authentication code.
        """
        async with self._lock:
            tx_hash = transaction_hash or self._pending_auth_transaction
            phone = self._pending_auth_phone

            if not tx_hash or not phone:
                return {
                    "success": False,
                    "error": "NO_PENDING_AUTH",
                    "message": "No pending authentication request found. Please call bale_auth_request_code first."
                }

            sessions_dir = config.ensure_sessions_dir()
            session_file = sessions_dir / f"{phone}.bale"

            temp_client = Client(session_file=str(session_file))
            res = await temp_client.validate_code(code=str(code).strip(), transaction_hash=tx_hash)

            if isinstance(res, AuthErrors):
                if res == AuthErrors.PASSWORD_NEEDED:
                    return {
                        "success": False,
                        "status": "PASSWORD_NEEDED",
                        "transaction_hash": tx_hash,
                        "message": "Two-Factor Authentication (2FA) password is required. Call bale_auth_verify_password."
                    }
                return {
                    "success": False,
                    "error": str(res.name),
                    "message": f"Code validation failed: {res.name}"
                }

            # Verification successful, connect client
            await temp_client.start(run_in_background=True, signal_handling=False)
            self._active_client = temp_client
            self._active_session_name = str(phone)
            self._pending_auth_transaction = None
            self._pending_auth_phone = None

            return {
                "success": True,
                "status": "authenticated",
                "session_name": str(phone),
                "user_id": temp_client.id,
                "message": "Successfully authenticated and connected!"
            }

    async def verify_password(self, password: str, transaction_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates the 2FA password.
        """
        async with self._lock:
            tx_hash = transaction_hash or self._pending_auth_transaction
            phone = self._pending_auth_phone

            if not tx_hash or not phone:
                return {
                    "success": False,
                    "error": "NO_PENDING_AUTH",
                    "message": "No pending authentication request found."
                }

            sessions_dir = config.ensure_sessions_dir()
            session_file = sessions_dir / f"{phone}.bale"

            temp_client = Client(session_file=str(session_file))
            res = await temp_client.validate_password(password=password, transaction_hash=tx_hash)

            if isinstance(res, AuthErrors):
                return {
                    "success": False,
                    "error": str(res.name),
                    "message": f"Password validation failed: {res.name}"
                }

            await temp_client.start(run_in_background=True, signal_handling=False)
            self._active_client = temp_client
            self._active_session_name = str(phone)
            self._pending_auth_transaction = None
            self._pending_auth_phone = None

            return {
                "success": True,
                "status": "authenticated",
                "session_name": str(phone),
                "user_id": temp_client.id,
                "message": "2FA verified successfully. Session connected!"
            }

    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnects the active client session.
        """
        async with self._lock:
            if not self._active_client:
                return {"success": True, "message": "No active session to disconnect."}

            session_name = self._active_session_name
            try:
                await self._active_client.stop()
            except Exception as e:
                logger.warning(f"Error stopping client: {e}")

            self._active_client = None
            self._active_session_name = None

            return {"success": True, "message": f"Session '{session_name}' disconnected."}


# Global singleton manager instance
session_manager = SessionManager()
