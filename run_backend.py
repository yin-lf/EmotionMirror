"""
后端启动脚本
使用方式：python run_backend.py
"""

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 50)
    print("  EmotionMirror Backend")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
