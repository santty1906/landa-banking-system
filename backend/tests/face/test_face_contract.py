from __future__ import annotations

import pytest

from app.infrastructure.face_recognition.adapters.base import NullFaceRecognitionAdapter

pytestmark = pytest.mark.face_contract


def test_null_face_adapter_raises_not_implemented():
    adapter = NullFaceRecognitionAdapter()

    with pytest.raises(NotImplementedError, match="not implemented"):
        adapter.verify_faces("ref.jpg", "candidate.jpg")
