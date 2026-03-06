# RLAP — Reticulum LXMF App Protocol

A client-agnostic protocol and Python reference implementation for interactive app sessions over [LXMF](https://github.com/markqvist/LXMF) / [Reticulum](https://github.com/markqvist/Reticulum).

RLAP lets any Reticulum client (Sideband, NomadNet, MeshChat, etc.) host interactive apps — games, file sharing, collaborative tools — as structured LXMF messages. Clients that don't understand RLAP see human-readable fallback text.

## Quick Start

```bash
# Install (zero dependencies for core library)
pip install -e .

# Run tests
pip install -e ".[dev]"
pytest

# Play Tic-Tac-Toe locally (no network needed)
python examples/ttt_local.py

# Check wire budget for all TTT actions
python examples/envelope_sizes.py
```

## How It Works

RLAP encodes app sessions as LXMF custom fields:

```python
fields[0xFB] = "rlap.v1"                    # protocol marker
fields[0xFD] = {                             # envelope
    "a": "ttt.1",                            # app_id.version
    "c": "move",                             # command
    "s": "a1b2c3d4e5f6g7h8",               # session_id
    "p": {"i": 4, "b": "____X____", ...},   # payload
}
```

The LXMF `content` field carries fallback text (e.g., `"[RLAP TTT] Move 3"`) for non-RLAP clients.

All envelopes are msgpack-serialized and fit within LXMF's 295-byte OPPORTUNISTIC delivery limit — no link setup needed, single encrypted packet.

## Project Structure

```
src/rlap/
  constants.py     # Protocol constants
  errors.py        # Error hierarchy
  envelope.py      # Pack/unpack/validate envelopes
  session.py       # Session state machine
  app_base.py      # Abstract base for apps
  router.py        # App registry and dispatch
  store.py         # SQLite persistence
  transport.py     # LXMF bridge (optional, requires rlap[rns])
  apps/
    tictactoe.py   # Tic-Tac-Toe — first working app
```

## Writing an App

See [docs/writing-an-app.md](docs/writing-an-app.md) for a full guide.

```python
from rlap.app_base import AppBase

class MyApp(AppBase):
    app_id = "myapp"
    version = 1
    display_name = "My App"
    session_type = "turn_based"
    validation = "both"
    actions = ["challenge", "accept", "decline", "move"]
    # ... implement abstract methods ...
```

## Protocol Spec

See [SPEC.md](SPEC.md) for the formal protocol specification — implementable without seeing the Python code.

## Network Usage

For LXMF transport (requires Reticulum):

```bash
pip install -e ".[rns]"
python examples/ttt_cli.py
```

## License

MIT
