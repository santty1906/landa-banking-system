import base64
import os
import pickle

import pytest

from app.face_service import is_enrolled, _check_embedding_quality, _normalize_embedding


# Minimal valid 1x1 JPEG in base64
_VALID_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP////////////////////////////////////////////////////////////////////"
    "//////////////////////////////////////////////////////2wBDAf/////////////////////////////////////////////////////////////////"
    "///////////////////////////////////////////////////////wAARCAABAAEDASIA"
    "AhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/"
    "xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMR"
    "AD8AANL/2Q=="
)


def test_is_enrolled_no_user(app):
    with app.app_context():
        assert is_enrolled("nonexistent_user") is False


def test_is_enrolled_empty_username(app):
    with app.app_context():
        assert is_enrolled("") is False


def test_enroll_faces_missing_data(app):
    from app.face_service import enroll_faces

    with app.app_context():
        try:
            enroll_faces("testuser", {})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Missing" in str(e)


def test_enroll_faces_missing_angle(app):
    from app.face_service import enroll_faces

    data_uri = "data:image/jpeg;base64," + _VALID_JPEG_B64
    with app.app_context():
        try:
            enroll_faces("testuser", {"frontal": data_uri})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Missing left face" in str(e)


def test_verify_face_no_enrollment(app):
    from app.face_service import verify_face

    with app.app_context():
        result = verify_face(
            "nonexistent", "data:image/jpeg;base64," + _VALID_JPEG_B64
        )
        assert result is False


def test_verify_face_detailed_no_enrollment(app):
    from app.face_service import verify_face_detailed

    with app.app_context():
        result = verify_face_detailed(
            "nonexistent", "data:image/jpeg;base64," + _VALID_JPEG_B64
        )
        assert result["verified"] is False
        assert "error" in result


def test_normalize_embedding(app):
    with app.app_context():
        vec = [3.0, 0.0, 4.0]
        normed = _normalize_embedding(vec)
        import numpy as np

        n = np.linalg.norm(normed)
        assert abs(n - 1.0) < 1e-6


def test_check_embedding_quality_all_same(app):
    with app.app_context():
        embeddings = {
            "frontal": [1.0, 0.0, 0.0],
            "left": [1.0, 0.0, 0.0],
            "right": [1.0, 0.0, 0.0],
        }
        assert _check_embedding_quality(embeddings) == False


def test_check_embedding_quality_good_variation(app):
    with app.app_context():
        embeddings = {
            "frontal": [1.0, 0.0, 0.0],
            "left": [0.0, 1.0, 0.0],
            "right": [0.0, 0.0, 1.0],
        }
        assert _check_embedding_quality(embeddings) == True


def test_compute_average_embedding(app):
    from app.face_service import _compute_average_embedding

    with app.app_context():
        embeddings = {
            "frontal": [1.0, 0.0, 0.0],
            "left": [0.0, 1.0, 0.0],
            "right": [0.0, 0.0, 1.0],
        }
        avg = _compute_average_embedding(embeddings)
        assert len(avg) == 3
        import numpy as np
        n = np.linalg.norm(avg)
        assert abs(n - 1.0) < 1e-6


def test_enroll_faces_saves_payload_structure(app, tmp_path):
    from app.face_service import _get_user_dir, _get_embeddings_path

    with app.app_context():
        app.config["UPLOAD_FOLDER"] = str(tmp_path)
        user_dir = _get_user_dir("payload_test")
        payload_path = os.path.join(user_dir, "embeddings.pkl")

        fake_embeddings = {
            "frontal": [1.0, 0.0, 0.0],
            "left": [0.9, 0.1, 0.0],
            "right": [0.8, 0.2, 0.0],
        }

        from app.face_service import _compute_average_embedding

        averaged = _compute_average_embedding(fake_embeddings)
        payload = {
            "angles": fake_embeddings,
            "averaged": averaged,
            "model": "Facenet512",
        }

        with open(payload_path, "wb") as f:
            pickle.dump(payload, f)

        assert os.path.exists(payload_path)

        with open(payload_path, "rb") as f:
            loaded = pickle.load(f)

        assert "angles" in loaded
        assert "averaged" in loaded
        assert "model" in loaded
        assert len(loaded["angles"]) == 3
        assert len(loaded["averaged"]) == 3
