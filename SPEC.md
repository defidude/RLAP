# RLAP Specification v0.1

**Reticulum LXMF App Protocol**

This document is the normative reference for RLAP. It is implementable without seeing the Python reference code.

---

## 1. Overview

RLAP defines how interactive app sessions (games, tools, etc.) are encoded as LXMF messages over Reticulum. Clients that don't understand RLAP see human-readable fallback text in the standard LXMF content field.

RLAP v1 is **2-player only**. All sessions have exactly one initiator and one responder.

---

## 2. LXMF Field Allocation

RLAP uses two LXMF custom extension fields:

| Field | ID | Value |
|-------|----|-------|
| `FIELD_CUSTOM_TYPE` | `0xFB` (251) | `"rlap.v1"` |
| `FIELD_CUSTOM_META` | `0xFD` (253) | Envelope dict (see Section 3) |

All fields are serialized via **msgpack** (not JSON).

---

## 3. Envelope Schema

The envelope is a msgpack dict stored in `fields[0xFD]`:

```
{
    "a": "<app_id>.<version>",    # e.g. "ttt.1"
    "c": "<command>",             # e.g. "move"
    "s": "<session_id>",         # 16-char hex (8 random bytes)
    "p": { <payload> }           # app-specific, short keys
}
```

All keys are single characters to minimize wire size. The `app_id` and `version` are combined into a single string to save one key-value pair.

### Required Fields

All four keys (`a`, `c`, `s`, `p`) MUST be present in every envelope.

### Session ID

Session IDs are 8 random bytes encoded as 16 hexadecimal characters. The challenger generates the session ID.

---

## 4. Size Constraints

| Limit | Value | Source |
|-------|-------|--------|
| Envelope (packed) | max **200 bytes** | RLAP budget rule |
| OPPORTUNISTIC content | max **295 bytes** | `LXMessage.ENCRYPTED_PACKET_MAX_CONTENT` |
| DIRECT packet content | max **319 bytes** | `LXMessage.LINK_PACKET_MAX_CONTENT` |
| LXMF overhead | **112 bytes** | 16B dest + 16B src + 64B sig + 8B ts + 8B structure |

LXMF content is packed as `[timestamp, title, content, fields_dict]`.

If content exceeds 295 bytes, LXMF silently escalates from OPPORTUNISTIC to DIRECT delivery, which requires a full Reticulum link handshake. RLAP envelopes MUST be designed to fit within OPPORTUNISTIC limits.

---

## 5. Fallback Text

The LXMF `content` field IS the fallback text. There is no separate fallback key in the envelope.

Format: `[RLAP <AppName>] <description>`

Examples:
- `[RLAP TTT] Sent a challenge!`
- `[RLAP TTT] Move 3`
- `[RLAP TTT] X wins!`

Non-RLAP clients display this as a regular message.

---

## 6. Session Lifecycle

### State Machine

```
challenge --> accept --> action* --> end
    |                      |
    +-> decline            +-> resign
    |                      +-> draw_offer --> draw_accept
    +-> expire (local)     |               +-> draw_decline
                           +-> error (receiver -> sender)
```

### Commands

| Command | Description |
|---------|-------------|
| `challenge` | Initiate a new session |
| `accept` | Accept a challenge |
| `decline` | Decline a challenge |
| `move` | App-specific action (e.g., place a piece) |
| `resign` | Voluntary forfeit |
| `draw_offer` | Propose a draw |
| `draw_accept` | Accept a draw proposal |
| `draw_decline` | Decline a draw proposal |
| `error` | Reject an invalid action |

### Status Transitions

| From | Command | To |
|------|---------|-----|
| `pending` | `accept` | `active` |
| `pending` | `decline` | `declined` |
| `active` | `move` (terminal) | `completed` |
| `active` | `resign` | `completed` |
| `active` | `draw_accept` | `completed` |
| `active` | `move` (normal) | `active` |
| `active` | `draw_offer` | `active` |
| `active` | `draw_decline` | `active` |
| `active` | `error` | `active` |

---

## 7. Session Types

| Type | Description |
|------|-------------|
| `turn_based` | Players alternate turns (e.g., Tic-Tac-Toe, Chess) |
| `real_time` | Both players can act at any time |
| `one_shot` | Single action per player (e.g., coin flip) |

---

## 8. Validation Models

| Model | Description | Error Behavior |
|-------|-------------|----------------|
| `sender` | Sender validates before sending; receiver trusts | No error actions sent |
| `receiver` | Receiver validates on receipt; rejects invalid | Sends `error` action |
| `both` | Both sides validate independently | Receiver sends `error` if validation disagrees |

---

## 9. Error Actions

When a receiver rejects an action:

```
{
    "a": "<app_id>.<version>",
    "c": "error",
    "s": "<session_id>",
    "p": {
        "code": "<error_code>",
        "msg": "<human-readable message>",
        "ref": "<command that caused the error>"
    }
}
```

### Standard Error Codes

| Code | Meaning |
|------|---------|
| `unsupported_app` | Receiver doesn't have this app |
| `invalid_move` | Action failed validation |
| `not_your_turn` | Out-of-turn action |
| `session_expired` | Session timed out on receiver |
| `protocol_error` | Malformed envelope or unknown command |

Error actions are best-effort. If the error itself fails to deliver, the sender sees no response.

---

## 10. Session Expiry

| Status | Default TTL | Meaning |
|--------|-------------|---------|
| `pending` | 24 hours | Unanswered challenges expire |
| `active` | 7 days | Inactive sessions expire |
| `completed` | N/A | Preserved indefinitely |

Enforcement is **local-only**: each peer expires sessions independently based on its own clock. No LXMF message is sent on expiry.

A 1-hour grace period is applied to account for clock skew between peers.

Apps MAY override default TTLs via their manifest.

---

## 11. Delivery Method Guidelines

Apps declare preferred delivery per command. LXMF auto-escalates if content exceeds limits, so these are preferences, not guarantees.

| Action | Preferred | Rationale |
|--------|-----------|-----------|
| `challenge` | OPPORTUNISTIC | Small, fire-and-forget |
| `accept` | OPPORTUNISTIC | Small, includes initial state |
| `decline` | OPPORTUNISTIC | Minimal payload |
| `move` | OPPORTUNISTIC | Must fit in 295B |
| `resign` | DIRECT | Delivery confirmation important |
| `draw_offer` | OPPORTUNISTIC | Small |
| `draw_accept` / `draw_decline` | DIRECT | State-changing |
| `error` | OPPORTUNISTIC | Informational |

---

## 12. App Manifest

Each app declares a manifest:

```
{
    "app_id": "<string>",
    "version": <int>,
    "display_name": "<string>",
    "icon": "<string>",
    "session_type": "turn_based" | "real_time" | "one_shot",
    "max_players": 2,
    "validation": "sender" | "receiver" | "both",
    "actions": [<list of command strings>],
    "preferred_delivery": {<command: method>},
    "ttl": {"pending": <seconds>, "active": <seconds>}
}
```

---

## 13. Large Payloads

Most RLAP actions fit in a single packet. For larger data:

**Strategy A**: LXMF Resource auto-escalation. If DIRECT content exceeds 319 bytes, LXMF transfers as a Resource over the link (up to ~3.2 MB). Transparent to the app layer.

**Strategy B**: `FIELD_FILE_ATTACHMENTS` (`0x05`). For explicit bulk data, use the standard LXMF file attachment field alongside the RLAP envelope.

---

## 14. Backward Compatibility

Messages with `fields[0xFB] = "ratspeak.game"` are legacy v0. Implementations SHOULD translate them to RLAP v1 format on receipt via `migrate_legacy()`.

Legacy translation is receive-only. All outbound messages use RLAP v1.

---

## 15. Cross-Client Adoption Levels

| Level | Description |
|-------|-------------|
| **None** | Client ignores RLAP fields; shows fallback text |
| **Basic** | Client recognizes RLAP fields; shows enhanced notification |
| **Full** | Client renders interactive app UI |

Any LXMF client achieves "None" level by default — fallback text appears as a regular message.

---

## 16. Serialization

All RLAP data MUST be serialized with msgpack. JSON is NOT supported on the wire. This is a hard constraint — every byte matters on LoRa links.

Implementations SHOULD use `u-msgpack-python` (MIT licensed, pure Python) for compatibility with the Reticulum ecosystem.

---

## 17. Session Storage Schema

### app_sessions

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | TEXT | 16-char hex, part of composite PK |
| `identity_id` | TEXT | Local identity, part of composite PK |
| `app_id` | TEXT | App identifier |
| `app_version` | INTEGER | Protocol version |
| `contact_hash` | TEXT | Remote peer's identity hash |
| `initiator` | TEXT | Who sent the challenge |
| `status` | TEXT | pending/active/completed/expired/declined |
| `metadata` | TEXT (JSON) | App-specific state blob |
| `unread` | INTEGER | 0 or 1 |
| `created_at` | REAL | Unix timestamp |
| `updated_at` | REAL | Unix timestamp |
| `last_action_at` | REAL | Unix timestamp (used for TTL) |

Primary key: `(session_id, identity_id)`

### app_actions (optional)

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | TEXT | Session reference |
| `identity_id` | TEXT | Local identity |
| `action_num` | INTEGER | Sequence number |
| `command` | TEXT | RLAP command |
| `payload_json` | TEXT | Serialized payload |
| `sender` | TEXT | Who sent this action |
| `timestamp` | REAL | Unix timestamp |

Unique constraint: `(session_id, identity_id, action_num)`
