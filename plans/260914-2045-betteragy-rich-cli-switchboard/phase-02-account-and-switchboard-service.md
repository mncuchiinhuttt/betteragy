# Phase 02: Account Manager, OAuth Flow & Keyring Switchboard

## Overview
- **Priority**: P0 (Core Functionality)
- **Current Status**: Planned
- **Description**: Implement multi-account storage, Google OAuth 2.0 PKCE flow, platform keyring envelope read/write, rotation strategies, and cooldown handling.

## Key Insights
- `agy` reads active credentials from system keyring: `service="gemini"`, `account="antigravity"`.
- Envelope format: `go-keyring-base64:<base64-json>` with payload:
  `{"token":{"access_token":"...","token_type":"Bearer","refresh_token":"...","expiry":"ISO"},"auth_method":"consumer"}`.
- Switchboard must proactively refresh the access token before injecting into keyring to prevent immediate 401s.
- Auto-importing existing credentials from keyring on initial launch ensures seamless onboarding.

## Architecture & Data Flow
```
OAuth Flow (Browser / Loopback HTTP Server)
       │
       ▼
Account Manager (Pool of accounts in accounts.json)
       │
       ▼
Token Refresher (Google OAuth2 Token endpoint)
       │
       ▼
Keyring Service (macOS `security` / Linux `secret-tool` / fallback)
       │
       ▼
`agy` CLI reads updated credentials instantly!
```

## Related Code Files
- [NEW] `src/betteragy/services/keyring_adapter.py`
- [NEW] `src/betteragy/services/oauth_service.py`
- [NEW] `src/betteragy/services/account_service.py`
- [NEW] `src/betteragy/services/rotation_service.py`

## Implementation Steps
1. Create `keyring_adapter.py`: Read/write `go-keyring-base64` envelope on macOS via `security` CLI and Linux via `secret-tool`.
2. Create `oauth_service.py`: Local loopback HTTP server (`http://127.0.0.1:<port>/callback`), state verification, token exchange, and Google userinfo profile lookup.
3. Create `account_service.py`: Manage list of accounts, active account selection, manual token import, deletion, and token refreshing.
4. Create `rotation_service.py`: Implement strategies (`round-robin`, `least-used`, `sticky`, `random`) and cooldown management with auto-skip of rate-limited accounts.

## Todo List
- [ ] Implement cross-platform Keyring Adapter
- [ ] Implement OAuth 2.0 Loopback Service
- [ ] Implement Account CRUD & Token Refresher
- [ ] Implement Rotation Strategies & Cooldown Handler
- [ ] Add auto-import from existing keyring/antigravity-accounts.json
