import base64
import hashlib
import os
import pickle
import tempfile
import time

import cv2
import numpy as np

from flask import current_app
from cryptography.fernet import Fernet

def _derive_user_key(master_key: bytes, salt: bytes) -> bytes:
    """
    Deriva una clave Fernet específica de un usuario a partir de la clave
    maestra y un salt propio de esa persona, usando HKDF (RFC 5869).

    Si la clave maestra se filtra junto con el salt de un usuario puntual,
    solo la plantilla biométrica de esa persona queda expuesta; el resto de
    usuarios no se ven afectados, y basta con regenerar su salt para
    invalidar ("revocar") su plantilla vieja sin tocar a nadie más.

    Nota: esto no protege contra una filtración completa de la base de datos
    junto con la clave maestra (en ese caso un atacante también tendría los
    salts) — mitiga el caso de una filtración aislada, no todos los escenarios.
    """
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"landa-face-embeddings",
    )
    derived = hkdf.derive(master_key)
    return base64.urlsafe_b64encode(derived)


def _get_or_create_bio_salt(username: str) -> bytes:
    from .models import User, db

    user = User.query.filter_by(username=username).first()
    if user is None:
        raise ValueError("User not found")

    if not user.bio_salt:
        user.bio_salt = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
        db.session.commit()

    return base64.urlsafe_b64decode(user.bio_salt.encode("utf-8"))


def _get_cipher(user_salt: bytes):
    key = current_app.config.get("ENCRYPTION_KEY")

    if not key:
        raise ValueError("Missing ENCRYPTION_KEY")

    if isinstance(key, str):
        key = key.encode()

    # ENCRYPTION_KEY ya es una clave Fernet (base64 de 32 bytes); se decodifica
    # para usar esos bytes como material de entrada de la derivación HKDF.
    master_key_raw = base64.urlsafe_b64decode(key)
    derived = _derive_user_key(master_key_raw, user_salt)
    return Fernet(derived)

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


def _check_face_framing(image_path, facial_area, face_confidence, edge_margin=0.02):
    """
    Rechaza capturas donde el rostro detectado está recortado por el borde
    de la imagen (rostro parcial) o la confianza de detección es muy baja.
    """
    min_confidence = current_app.config.get("FACE_MIN_CONFIDENCE", 0.80)

    if face_confidence is not None and face_confidence < min_confidence:
        raise ValueError(
            "No se detectó el rostro con suficiente claridad; acércate "
            "más a la cámara y evita sombras fuertes o contraluz."
        )

    if not facial_area:
        return

    img = cv2.imread(image_path)
    if img is None:
        return

    img_h, img_w = img.shape[:2]
    x, y = facial_area.get("x", 0), facial_area.get("y", 0)
    w, h = facial_area.get("w", 0), facial_area.get("h", 0)

    margin_x = img_w * edge_margin
    margin_y = img_h * edge_margin

    touches_edge = (
        x <= margin_x
        or y <= margin_y
        or (x + w) >= (img_w - margin_x)
        or (y + h) >= (img_h - margin_y)
    )

    if touches_edge:
        raise ValueError(
            "El rostro aparece recortado por el borde de la imagen; "
            "centra tu cara completa dentro del círculo guía e inténtalo de nuevo."
        )


def _get_embedding(image_path: str):
    DeepFace = _get_deepface()

    t0 = time.time()

    try:
        result = DeepFace.represent(
            img_path=image_path,
            model_name=current_app.config["FACE_MODEL_NAME"],
            detector_backend=current_app.config["FACE_DETECTOR_BACKEND"],
            enforce_detection=current_app.config["FACE_ENFORCE_DETECTION"],
            anti_spoofing=current_app.config.get("FACE_ANTI_SPOOFING", True),
        )
    except ValueError as e:
        if "spoof" in str(e).lower():
            raise ValueError(
                "No se pudo confirmar que hay una persona real frente a la "
                "cámara. Evita usar fotos, pantallas o videos; intenta de "
                "nuevo con la cámara en vivo."
            ) from e
        raise
    current_app.logger.info("DeepFace.represent tardó %.2f s", time.time() - t0)

    face = result[0]
    _check_face_framing(image_path, face.get("facial_area"), face.get("face_confidence"))

    return _normalize_embedding(face["embedding"])

def _save_embeddings(username: str, embeddings: dict):
    salt = _get_or_create_bio_salt(username)
    cipher = _get_cipher(salt)
    path = _get_embeddings_path(username)

    data = pickle.dumps(embeddings)
    encrypted = cipher.encrypt(data)

    with open(path, "wb") as f:
        f.write(encrypted)


def _load_embeddings(username: str):
    path = _get_embeddings_path(username)

    if not os.path.exists(path):
        raise ValueError("User not enrolled")

    salt = _get_or_create_bio_salt(username)
    cipher = _get_cipher(salt)

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
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)

def verify_face(username: str, image_base64: str):
    result = verify_face_detailed(username, image_base64)
    return result["verified"]


def verify_face_detailed(username: str, image_base64: str):
    temp_path = None
    t_start = time.time()

    try:
        stored = _load_embeddings(username)

        temp_path = _save_temp_image(image_base64)
        temp_path = _preprocess_image(temp_path)

        new_embedding = _get_embedding(temp_path)

        distances = [_cosine_distance(new_embedding, emb) for emb in stored.values()]
        avg_distance = np.mean(distances)

        threshold = current_app.config.get("FACE_MATCH_THRESHOLD", 0.35)
        current_app.logger.info("verify_face_detailed total: %.2f s", time.time() - t_start)

        return {
            "verified": bool(avg_distance < threshold),
            "distance": float(avg_distance),
            "threshold": threshold
        }

    except ValueError as e:
        # Errores esperables y con mensaje útil: rostro no detectado,
        # recortado, baja confianza, o posible spoof.
        current_app.logger.warning("Verificación facial rechazada: %s", e)
        return {
            "verified": False,
            "error": str(e)
        }

    except Exception:
        current_app.logger.exception("Fallo en verify_face_detailed")
        return {
            "verified": False,
            "error": "Verification failed"
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                current_app.logger.warning(
                    "No se pudo eliminar el archivo temporal %s (puede seguir en uso)",
                    temp_path,
                )

def is_enrolled(username: str) -> bool:
    return os.path.exists(_get_embeddings_path(username))
