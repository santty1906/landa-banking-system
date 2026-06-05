"""Encryption utilities for biometric embeddings at rest."""

from __future__ import annotations

import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken

from app.application.interfaces.face_auth import EmbeddingCipher, EncryptedEmbeddingPayload
from app.core.config import Settings, get_settings
from app.core.exceptions import InfrastructureError


class FernetEmbeddingCipher(EmbeddingCipher):
    """Encrypt/decrypt embeddings with a key derived from environment settings."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._fernet = Fernet(self._derive_fernet_key(self._settings.face_embedding_encryption_key))

    def encrypt_embedding(self, embedding: list[float]) -> EncryptedEmbeddingPayload:
        payload = json.dumps(embedding).encode("utf-8")
        encrypted = self._fernet.encrypt(payload)
        return EncryptedEmbeddingPayload(
            ciphertext=encrypted.decode("utf-8"),
            metadata={"key_version": self._settings.face_embedding_key_version},
        )

    def decrypt_embedding(self, ciphertext: str, metadata: dict[str, str]) -> list[float]:
        key_version = metadata.get("key_version")
        if key_version != self._settings.face_embedding_key_version:
            raise InfrastructureError("Unsupported embedding key version")

        try:
            plaintext = self._fernet.decrypt(ciphertext.encode("utf-8"))
        except InvalidToken as exc:
            raise InfrastructureError("Unable to decrypt stored facial embedding") from exc

        values = json.loads(plaintext.decode("utf-8"))
        if not isinstance(values, list):
            raise InfrastructureError("Stored embedding payload is invalid")
        return [float(item) for item in values]

    @staticmethod
    def _derive_fernet_key(secret: str) -> bytes:
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)
