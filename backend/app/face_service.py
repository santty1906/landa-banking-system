import base64
import os
import pickle
import tempfile

import cv2
import numpy as np
from flask import current_app


def _get_deepface():
    from deepface import DeepFace
    return DeepFace


def _save_temp_image(base64_str: str) -> str:
    _, encoded = base64_str.split(",", 1)
    data = base64.b64decode(encoded)
    fd, path = tempfile.mkstemp(suffix=".jpg")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path


def _get_user_dir(username: str) -> str:
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], username)
    os.makedirs(path, exist_ok=True)
    return path


def _get_embeddings_path(username: str) -> str:
    return os.path.join(_get_user_dir(username), "embeddings.pkl")


def _preprocess_image(image_path: str) -> str:
    img = cv2.imread(image_path)
    if img is None:
        return image_path

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    target_size = current_app.config.get("FACE_TARGET_SIZE", 224)
    h, w = normalized.shape[:2]
    if h != target_size or w != target_size:
        normalized = cv2.resize(normalized, (target_size, target_size))

    preprocessed_path = image_path.replace(".jpg", "_pp.jpg")
    cv2.imwrite(preprocessed_path, normalized, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return preprocessed_path


def _normalize_embedding(embedding):
    arr = np.array(embedding, dtype=np.float64)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr


def _get_embedding(image_path: str) -> list:
    DeepFace = _get_deepface()
    preprocessed_path = _preprocess_image(image_path)

    try:
        result = DeepFace.represent(
            img_path=preprocessed_path,
            model_name=current_app.config["FACE_MODEL_NAME"],
            detector_backend=current_app.config["FACE_DETECTOR_BACKEND"],
            enforce_detection=current_app.config.get("FACE_ENFORCE_DETECTION", True),
        )
        embedding = _normalize_embedding(result[0]["embedding"])
        return embedding.tolist()
    finally:
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)


def _compute_average_embedding(embeddings: dict) -> list:
    vectors = [np.array(v, dtype=np.float64) for v in embeddings.values()]
    avg = np.mean(vectors, axis=0)
    norm = np.linalg.norm(avg)
    if norm > 0:
        avg = avg / norm
    return avg.tolist()


def _check_embedding_quality(embeddings: dict) -> bool:
    vectors = [np.array(v, dtype=np.float64) for v in embeddings.values()]
    distances = []
    keys = list(embeddings.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            d = float(np.linalg.norm(vectors[i] - vectors[j]))
            distances.append(d)
    if not distances:
        return False
    mean_dist = np.mean(distances)
    min_quality = current_app.config.get("FACE_MIN_ANGLE_DISTANCE", 0.15)
    return mean_dist >= min_quality


def enroll_faces(username: str, images: dict) -> None:
    for angle in ("frontal", "left", "right"):
        if angle not in images:
            raise ValueError(f"Missing {angle} face image")

    temp_paths = {}
    try:
        embeddings = {}
        for angle in ("frontal", "left", "right"):
            temp_path = _save_temp_image(images[angle])
            temp_paths[angle] = temp_path
            embedding = _get_embedding(temp_path)
            embeddings[angle] = embedding

        if not _check_embedding_quality(embeddings):
            raise ValueError(
                "Face captures lack sufficient variation. "
                "Please ensure different angles as instructed."
            )

        averaged = _compute_average_embedding(embeddings)

        payload = {
            "angles": embeddings,
            "averaged": averaged,
            "model": current_app.config["FACE_MODEL_NAME"],
        }

        user_dir = _get_user_dir(username)
        with open(os.path.join(user_dir, "embeddings.pkl"), "wb") as f:
            pickle.dump(payload, f)
    finally:
        for path in temp_paths.values():
            if os.path.exists(path):
                os.remove(path)


def verify_face(
    username: str, image_base64: str, threshold: float = None
) -> bool:
    result = verify_face_detailed(username, image_base64, threshold)
    return result["verified"]


def verify_face_detailed(
    username: str, image_base64: str, threshold: float = None
) -> dict:
    temp_path = None
    try:
        threshold = threshold or current_app.config["FACE_MATCH_THRESHOLD"]
        embeddings_path = _get_embeddings_path(username)

        if not os.path.exists(embeddings_path):
            return {"verified": False, "error": "No enrollment found"}

        with open(embeddings_path, "rb") as f:
            payload = pickle.load(f)

        if isinstance(payload, dict) and "averaged" in payload:
            enrolled = payload["averaged"]
        elif isinstance(payload, dict) and "angles" in payload:
            enrolled = payload["angles"]
        else:
            enrolled = payload

        temp_path = _save_temp_image(image_base64)
        embedding = _get_embedding(temp_path)
        probe = _normalize_embedding(embedding)

        if isinstance(enrolled, dict):
            distances = {
                angle: float(np.linalg.norm(probe - _normalize_embedding(ref)))
                for angle, ref in enrolled.items()
            }
            best_distance = min(distances.values())
            best_angle = min(distances, key=distances.get)
        else:
            best_distance = float(np.linalg.norm(probe - _normalize_embedding(enrolled)))
            best_angle = "averaged"

        verified = bool(best_distance < threshold)

        return {
            "verified": verified,
            "distance": round(best_distance, 4),
            "threshold": threshold,
            "best_angle": best_angle,
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def is_enrolled(username: str) -> bool:
    return os.path.exists(_get_embeddings_path(username))
