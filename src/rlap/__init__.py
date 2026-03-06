"""RLAP — Reticulum LXMF App Protocol."""

__version__ = "0.1.0"

from .constants import PROTOCOL_TYPE, FIELD_CUSTOM_TYPE, FIELD_CUSTOM_META
from .errors import RlapError
from .envelope import pack_envelope, unpack_envelope, validate_envelope_size
from .session import Session, SessionStateMachine
from .app_base import AppBase
from .router import register, discover, dispatch_incoming, dispatch_outgoing, list_apps
