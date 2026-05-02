"""
情绪分析 API 路由
TODO: 组员B / 组员C 实现后对接

预留接口：
  POST /api/predict/text      — 文本情绪识别（组员B）
  POST /api/predict/speech    — 语音情绪识别（组员C）
  POST /api/predict/multimodal — 多模态融合
"""

from flask import Blueprint

emotion_bp = Blueprint("emotion", __name__)


# TODO(组员B): POST /api/predict/text
# 接收 {"text": "..."}，调用 layer2_text_emotion，返回 Emotion Vector


# TODO(组员C): POST /api/predict/speech
# 接收音频文件，调用 layer2_speech_emotion，返回 Emotion Vector


# TODO: POST /api/predict/multimodal
# 接收文本+音频，调用 fusion 服务，返回融合 Emotion Vector
