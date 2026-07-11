import base64
import hashlib
import os
import pickle
import tempfile

import cv2
import numpy as np

from flask import current_app
from cryptography.fernet import Fernet

def _get_cipher():
    key = current_app.config.get("ENCRYPTION_KEY")

    if not key:
        raise ValueError("Missing ENCRYPTION_KEY")

    if isinstance(key, str):
        key = key.encode()

    return Fernet(key)

def _get_user_dir(username: str) -> str:
    base = current_app.config["UPLOAD_FOLDER"]
    # sha256 en vez de hash() nativo: hash() de strings se aleatoriza por
    # proceso (PYTHONHASHSEED), así que la ruta cambiaba en cada reinicio del
    # backend y el usuario perdía el acceso a su enrolamiento facial.
    safe_id = hashlib.sha256(username.encode("utf-8")).hexdigest()
    path = os.path.join(base, f"user_{safe_id}")
    os.makedirs(path, exist_ok=True)
    return path


def _get_embeddings_path(username: str) -> str:
    return os.path.join(_get_user_dir(username), "embeddings.enc")

def _save_temp_image(base64_str: str) -> str:
    if "," not in base64_str:
        raise ValueError("Invalid image format")

    _, encoded = base64_str.split(",", 1)

    if len(encoded) > 2_000_000:
        raise ValueError("Image too large")

    data = base64.b64decode(encoded)

    fd, path = tempfile.mkstemp(suffix=".jpg")

    with os.fdopen(fd, "wb") as f:
        f.write(data)

    return path


def _preprocess_image(image_path: str) -> str:
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Invalid image")

    return image_path

def _get_deepface():
    from deepface import DeepFace
    return DeepFace


def _normalize_embedding(embedding):
    arr = np.array(embedding, dtype=np.float64)
    norm = np.linalg.norm(arr)

    if norm > 0:
        arr = arr / norm

    return arr


def _cosine_distance(a, b):
    a = np.array(a, dtype=np.float64)
    b = np.array(b, dtype=np.float64)

    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def _check_embedding_quality(embeddings, min_distance=None):
    """
    Verifica que las capturas de los distintos ángulos no sean la misma foto
    repetida (posible intento de fraude o mala captura). Requiere que al
    menos un par de ángulos tenga una distancia coseno mínima entre sí.
    """
    if min_distance is None:
        try:
            min_distance = current_app.config.get("FACE_MIN_ANGLE_DISTANCE", 0.15)
        except RuntimeError:
            min_distance = 0.15

    keys = list(embeddings.keys())
    distances = []

    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            distances.append(_cosine_distance(embeddings[keys[i]], embeddings[keys[j]]))

    if not distances:
        return False

    return max(distances) >= min_distance


def _compute_average_embedding(embeddings):
    arrs = [np.array(v, dtype=np.float64) for v in embeddings.values()]
    avg = np.mean(arrs, axis=0)
    return _normalize_embedding(avg)


def _get_embedding(image_path: str):
    DeepFace = _get_deepface()

    result = DeepFace.represent(
        img_path=image_path,
        model_name=current_app.config["FACE_MODEL_NAME"],
        enforce_detection=current_app.config["FACE_ENFORCE_DETECTION"]
    )

    embedding = result[0]["embedding"]

    return _normalize_embedding(embedding)

def _save_embeddings(username: str, embeddings: dict):
    cipher = _get_cipher()
    path = _get_embeddings_path(username)

    data = pickle.dumps(embeddings)
    encrypted = cipher.encrypt(data)

    with open(path, "wb") as f:
        f.write(encrypted)


def _load_embeddings(username: str):
    path = _get_embeddings_path(username)

    if not os.path.exists(path):
        raise ValueError("User not enrolled")

    cipher = _get_cipher()

    with open(path, "rb") as f:
        encrypted = f.read()

    data = cipher.decrypt(encrypted)
    return pickle.loads(data)

def enroll_faces(username: str, images: dict):
    required = ("frontal", "left", "right")

    for angle in required:
        if angle not in images:
            raise ValueError(f"Missing {angle} face image")

    embeddings = {}
    temp_paths = []

    try:
        for angle, img_base64 in images.items():
            path = _save_temp_image(img_base64)
            temp_paths.append(path)
            path = _preprocess_image(path)

            embeddings[angle] = _get_embedding(path)

        if not _check_embedding_quality(embeddings):
            raise ValueError(
                "Las capturas son demasiado similares entre sí; repite el "
                "enrolamiento variando el ángulo del rostro."
            )

        _save_embeddings(username, embeddings)
    finally:
        # Se ejecuta siempre, incluso si DeepFace lanza una excepción, para no
        # dejar imágenes biométricas temporales sin cifrar en disco.
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)

def verify_face(username: str, image_base64: str):
    result = verify_face_detailed(username, image_base64)
    return result["verified"]


def verify_face_detailed(username: str, image_base64: str):
    temp_path = None

    try:
        stored = _load_embeddings(username)

        temp_path = _save_temp_image(image_base64)
        temp_path = _preprocess_image(temp_path)

        new_embedding = _get_embedding(temp_path)

        distances = [_cosine_distance(new_embedding, emb) for emb in stored.values()]
        avg_distance = np.mean(distances)

        threshold = current_app.config.get("FACE_MATCH_THRESHOLD", 0.35)

        return {
            "verified": avg_distance < threshold,
            "distance": float(avg_distance),
            "threshold": threshold
        }

    except Exception:
        return {
            "verified": False,
            "error": "Verification failed"
        }
    finally:
        # try/finally en vez de os.remove() en el "camino feliz": si
        # _get_embedding lanza excepción, el archivo temporal (biométrico)
        # quedaba huérfano y sin cifrar en disco.
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def is_enrolled(username: str) -> bool:
    return os.path.exists(_get_embeddings_path(username))
