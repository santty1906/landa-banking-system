"""Domain-level face recognition contract.

Business logic should depend on this interface, not concrete libraries.
"""

from __future__ import annotations

from typing import Protocol


class FaceRecognitionService(Protocol):
    """Abstraction boundary for future facial recognition providers."""

    def verify_faces(self, reference_image_path: str, candidate_image_path: str) -> bool:
        """Return whether two faces are considered a match."""
