"""RLAP AppBase abstract class."""

from abc import ABC, abstractmethod


class AppBase(ABC):
    """Abstract base for RLAP apps.

    Subclasses must set class attributes and implement abstract methods.
    """

    # --- Class attributes (override in subclass) ---
    app_id = ""
    version = 1
    display_name = ""
    icon = ""
    session_type = "turn_based"
    max_players = 2
    validation = "sender"
    actions = []
    preferred_delivery = {}
    ttl = {"pending": 86400, "active": 604800}

    # --- Required methods ---

    @abstractmethod
    def handle_incoming(self, session_id, command, payload, sender_hash,
                        identity_id):
        """Process an incoming RLAP action.

        Returns:
            dict with keys: "session", "emit", "error"
        """

    @abstractmethod
    def handle_outgoing(self, session_id, command, payload, identity_id):
        """Prepare an outgoing RLAP action.

        Returns:
            tuple: (enriched_payload: dict, fallback_text: str)
        """

    @abstractmethod
    def validate_action(self, session_id, command, payload, sender_hash):
        """Validate an action.

        Returns:
            tuple: (valid: bool, error_message: str or None)
        """

    @abstractmethod
    def get_session_state(self, session_id, identity_id):
        """Return current session state for rendering."""

    @abstractmethod
    def render_fallback(self, command, payload):
        """Generate human-readable fallback text for LXMF content field."""

    # --- Optional methods ---

    def get_delivery_method(self, command):
        """Return preferred delivery method for this command."""
        return self.preferred_delivery.get(command, "opportunistic")

    def get_manifest(self):
        """Build manifest dict from class attributes."""
        return {
            "app_id": self.app_id,
            "version": self.version,
            "display_name": self.display_name,
            "icon": self.icon,
            "session_type": self.session_type,
            "max_players": self.max_players,
            "validation": self.validation,
            "actions": list(self.actions),
            "preferred_delivery": dict(self.preferred_delivery),
            "ttl": dict(self.ttl),
        }

    def migrate_legacy(self, envelope):
        """Translate a legacy v0 envelope to RLAP v1 format.

        Return None if this app doesn't recognize the legacy message.
        """
        return None
