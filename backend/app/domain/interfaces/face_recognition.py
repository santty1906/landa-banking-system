"""Domain-level face recognition contracts.

Business logic depends on these interfaces, not concrete libraries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class FaceQualityResult:
    """Represents a lightweight quality gate decision for an input face image."""

    is_valid: bool
    reason_code: str | None = None
    message: str | None = None


@dataclass(slots=True)
class FaceComparisonResult:
    """Represents the comparison outcome between two face embeddings."""

    is_match: bool
    distance: float
    threshold: float
    metric: str = "cosine"


class FaceRecognitionService(Protocol):
    """Abstraction boundary for future facial recognition providers."""

    @property
    def model_name(self) -> str:
        """Return the active facial model identifier."""

    def validate_image_quality(self, image_bytes: bytes) -> FaceQualityResult:
        """Run basic quality checks before embedding extraction."""

    def generate_embedding(self, image_bytes: bytes) -> list[float]:
        """Generate a numeric embedding from a single-face image."""

    def compare_embeddings(
        self,
        reference_embedding: list[float],
        candidate_embedding: list[float],
    ) -> FaceComparisonResult:
        """Compare two embeddings and return a structured match decision."""
