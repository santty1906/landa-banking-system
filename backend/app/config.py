import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    FACE_MATCH_THRESHOLD = float(os.environ.get("FACE_MATCH_THRESHOLD", "0.35"))
    FACE_MODEL_NAME = os.environ.get("FACE_MODEL_NAME", "Facenet512")
    FACE_DETECTOR_BACKEND = os.environ.get("FACE_DETECTOR_BACKEND", "opencv")
    FACE_ENFORCE_DETECTION = os.environ.get("FACE_ENFORCE_DETECTION", "true").lower() == "true"
    FACE_TARGET_SIZE = int(os.environ.get("FACE_TARGET_SIZE", "224"))
    FACE_MIN_ANGLE_DISTANCE = float(os.environ.get("FACE_MIN_ANGLE_DISTANCE", "0.15"))
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "http")
