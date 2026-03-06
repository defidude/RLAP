"""RLAP error hierarchy."""


class RlapError(Exception):
    """Base error for all RLAP operations."""


class EnvelopeTooLarge(RlapError):
    """Packed envelope exceeds ENVELOPE_MAX_PACKED bytes."""


class InvalidEnvelope(RlapError):
    """Envelope is malformed or missing required fields."""


class IllegalTransition(RlapError):
    """Session state transition is not allowed."""


class UnknownApp(RlapError):
    """No registered handler for the given app_id."""


class ValidationError(RlapError):
    """Action failed validation (invalid move, not your turn, etc.)."""

    def __init__(self, code, message=""):
        self.code = code
        super().__init__(message or code)
