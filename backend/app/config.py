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
