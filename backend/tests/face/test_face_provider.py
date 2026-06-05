from __future__ import annotations

import os

import pytest

pytestmark = [
    pytest.mark.face_provider,
    pytest.mark.skipif(
        os.getenv("RUN_FACE_PROVIDER_TESTS") != "1",
        reason="Provider tests are reserved for manual/nightly workflows.",
    ),
]


def test_face_provider_pipeline_placeholder():
    assert True
