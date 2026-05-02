"""
Flask 应用入口 — 工厂函数
"""

from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import get_config


def create_app(config_class=None):
    app = Flask(__name__, static_folder="../static", static_url_path="/static")

    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    CORS(app, origins=app.config["CORS_ORIGINS"])

    # TODO: 注册蓝图路由
    # from backend.routes.emotion import emotion_bp
    # from backend.routes.upload import upload_bp
    # from backend.routes.health import health_bp
    # app.register_blueprint(health_bp, url_prefix="/api")
    # app.register_blueprint(emotion_bp, url_prefix="/api")
    # app.register_blueprint(upload_bp, url_prefix="/api")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found", "code": 404}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal error", "code": 500}), 500

    return app
