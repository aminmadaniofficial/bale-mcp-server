# Bale MCP Server 🚀

<div align="center">

[![CI Test Suite](https://github.com/aminmadaniofficial/bale-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/aminmadaniofficial/bale-mcp-server/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard-purple.svg)](https://modelcontextprotocol.io/)

**Production-grade Model Context Protocol (MCP) server for Bale Messenger.**  
Empowers Large Language Models (LLMs) to authenticate, inspect dialogs, read histories, send messages, interact with groups, and manage contacts on Bale user accounts.

</div>

---

## 🌟 Key Highlights

- ⚡ **Native Async Performance:** Powered by [`aiobale-py`](https://github.com/aminmadaniofficial/aiobale) and official Python MCP SDK (`mcp.server.mcpserver`).
- 🔐 **Multi-Account Sessions:** Auto-discovers and switches between `.bale` sessions on disk with zero credentials re-prompting.
- 📱 **Interactive & Tool-based Auth:** Support for interactive phone SMS login via CLI (`bale-mcp login`) or programmatically via MCP tools (`bale_auth_request_code`, `bale_auth_verify_code`, `bale_auth_verify_password`).
- 💬 **Complete Messaging Ecosystem:** Send, reply, edit, delete, forward, pin, and mark read across private chats, groups, and channels.
- 👥 **Contacts & Profile Search:** Query users by `@username` or phone number, fetch full profiles, manage contacts, and block/unblock.
- 📢 **Groups & Channels Management:** Inspect settings, member counts, invite users, generate invite URLs, and manage participant states.
- ⚡ **Reactions & Presence:** Send and remove emoji reactions (`👍`, `❤️`, `🔥`) and broadcast typing indicators.
- 🛡️ **Zero Data Leakage:** Session keys and `.bale` tokens remain strictly local and are protected by `.gitignore`.

---

## 📦 Architecture

```
LLM Client (Claude Desktop / Cursor / Antigravity / Cline)
                        │
                        │ JSON-RPC (STDIO / SSE / Streamable HTTP)
                        ▼
                Bale MCP Server
                        │
               Session Connection Pool
                        │
           aiobale Async Client (WebSockets / Protobuf)
                        ▼
              Bale Messenger Network
```

---

## 🛠️ Complete MCP Tools Catalog (31 Tools)

### 🔐 Authentication & Session Management
| Tool Name | Description |
| :--- | :--- |
| `bale_list_sessions` | List all available Bale user sessions/accounts stored locally on disk. |
| `bale_connect_session` | Connect or switch to a specific Bale account using session name or phone. |
| `bale_get_me` | Get profile information and connection status of the active account. |
| `bale_auth_request_code` | Request an SMS/Bale verification code for a new account login. |
| `bale_auth_verify_code` | Verify SMS/Bale authentication code to save a new `.bale` session. |
| `bale_auth_verify_password` | Submit Two-Factor Authentication (2FA) cloud password if required. |
| `bale_disconnect` | Disconnect the active account session. |

### 💬 Messaging & Dialogs
| Tool Name | Description |
| :--- | :--- |
| `bale_get_dialogs` | Retrieve recent chats, groups, and channels with unread counts and last message previews. |
| `bale_get_chat_history` | Fetch recent message history from a chat, group, or channel. |
| `bale_send_message` | Send a text message to a user, group, or channel with optional reply support. |
| `bale_edit_message` | Edit an existing text message sent previously in a chat. |
| `bale_delete_message` | Delete a message from a chat (for self or everyone). |
| `bale_forward_message` | Forward an existing message to another chat or user. |
| `bale_mark_chat_read` | Mark all messages in a chat or group as read. |
| `bale_pin_message` | Pin a message in a private chat or group. |

### 👥 Contacts & Users
| Tool Name | Description |
| :--- | :--- |
| `bale_get_contacts` | Retrieve the saved contact list from the active account. |
| `bale_search_user` | Search for a user, bot, group, or channel by username or phone number. |
| `bale_get_user_info` | Get detailed profile information (name, about, username) by user ID. |
| `bale_import_contacts` | Import one or more contacts by phone number and name into the address book. |
| `bale_block_user` | Block a user by user ID. |
| `bale_unblock_user` | Unblock a previously blocked user by user ID. |
| `bale_get_blocked_users` | List all users currently blocked by the active account. |

### 📢 Groups & Channels
| Tool Name | Description |
| :--- | :--- |
| `bale_get_group_info` | Retrieve full information, settings, member count, and permissions for a group. |
| `bale_get_group_members` | Retrieve the list of members in a group or channel. |
| `bale_create_group` | Create a new group or broadcast channel with initial members. |
| `bale_invite_to_group` | Invite one or more users to an existing group or channel. |
| `bale_get_group_invite_url`| Get the permanent invitation link (URL) for a group or channel. |
| `bale_leave_group` | Leave a group or channel. |

### ⚡ Reactions & Presence
| Tool Name | Description |
| :--- | :--- |
| `bale_send_reaction` | Add an emoji reaction (`👍`, `❤️`, `🔥`) to a specific message. |
| `bale_remove_reaction` | Remove an emoji reaction from a message. |
| `bale_send_typing` | Send a typing indicator to a chat or group. |

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- [`uv`](https://docs.astral.sh/uv/) (recommended) or standard `pip`

### 2. Install from Repository
```bash
git clone https://github.com/aminmadaniofficial/bale-mcp-server.git
cd bale-mcp-server

uv venv
source .venv/bin/activate
uv pip install -e .
```

### 3. Log In to Your Bale Account

You can authenticate directly using the built-in CLI:

```bash
bale-mcp login --phone 989XXXXXXXXX
```
This requests an SMS code and saves the session securely in `./sessions/<phone>.bale`.

To view existing sessions:
```bash
bale-mcp list-sessions
```

---

## 🔌 MCP Client Configuration

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "bale": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/bale-mcp-server",
        "run",
        "bale-mcp",
        "run"
      ],
      "env": {
        "BALE_SESSIONS_DIR": "/absolute/path/to/bale-mcp-server/sessions"
      }
    }
  }
}
```

### Antigravity IDE (`mcp_config.json`)
```json
{
  "mcpServers": {
    "bale": {
      "command": "/absolute/path/to/bale-mcp-server/.venv/bin/bale-mcp",
      "args": ["run"],
      "env": {
        "BALE_SESSIONS_DIR": "/absolute/path/to/bale-mcp-server/sessions"
      }
    }
  }
}
```

---

## 🧪 Testing

Run the automated test suite:
```bash
pytest -v
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
