from __future__ import annotations

import pytest

from app.infrastructure.face_recognition.adapters.base import NullFaceRecognitionAdapter

pytestmark = pytest.mark.face_contract


def test_null_face_adapter_raises_not_implemented():
    adapter = NullFaceRecognitionAdapter()

    with pytest.raises(NotImplementedError, match="not implemented"):
        adapter.validate_image_quality(b"image-bytes")

    with pytest.raises(NotImplementedError, match="not implemented"):
        adapter.generate_embedding(b"image-bytes")

    with pytest.raises(NotImplementedError, match="not implemented"):
        adapter.compare_embeddings([0.1], [0.1])
