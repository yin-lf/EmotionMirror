"""
后端配置文件
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = "emotionmirror-dev-key"
    DEBUG = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static")
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
    EMOTION_LABELS = ["happy", "sad", "angry", "calm", "fear", "surprise", "disgust", "neutral"]


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
