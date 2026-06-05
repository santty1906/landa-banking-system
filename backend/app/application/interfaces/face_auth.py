"""Application-level contracts for facial authentication workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class EncryptedEmbeddingPayload:
    """Encrypted payload to persist a biometric embedding safely."""

    ciphertext: str
    metadata: dict[str, str]


@dataclass(slots=True)
class StoredFaceEmbedding:
    """Stored face template required for authentication."""

    user_id: str
    encrypted_embedding: str
    encryption_metadata: dict[str, str]
    model_name: str


class FaceEmbeddingRepository(Protocol):
    """Persistence contract for encrypted facial templates."""

    def upsert_embedding(
        self,
        *,
        user_id: str,
        encrypted_embedding: str,
        encryption_metadata: dict[str, str],
        model_name: str,
    ) -> None:
        """Create or update the active encrypted embedding for a user."""

    def get_embedding_by_user_id(self, user_id: str) -> StoredFaceEmbedding | None:
        """Fetch a stored embedding for authentication."""


class AuthAuditRepository(Protocol):
    """Persistence contract for authentication audit records."""

    def create_log(
        self,
        *,
        method: str,
        outcome: str,
        reason_code: str,
        request_id: str,
        user_id: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Write an authentication audit event."""


class EmbeddingCipher(Protocol):
    """Contract for encrypting/decrypting numeric embeddings."""

    def encrypt_embedding(self, embedding: list[float]) -> EncryptedEmbeddingPayload:
        """Encrypt an embedding and return payload + metadata."""

    def decrypt_embedding(self, ciphertext: str, metadata: dict[str, str]) -> list[float]:
        """Decrypt persisted embedding payload into numeric vector."""
