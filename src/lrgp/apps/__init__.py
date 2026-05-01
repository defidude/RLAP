from .tictactoe import TicTacToeApp

__all__ = ["TicTacToeApp"]

# Chess is gated behind the [chess] extra to keep the core lib zero-deps.
# Importing lrgp.apps.chess directly raises a clear ImportError when the
# extra isn't installed.
