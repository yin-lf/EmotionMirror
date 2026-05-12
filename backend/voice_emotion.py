from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import os
import logging
import sys

logger = logging.getLogger(__name__)


class Emotion(Enum):
    HAPPY = "开心"
    SAD = "悲伤"
    ANGRY = "愤怒"
    ANXIOUS = "焦虑"
    FEARFUL = "恐惧"
    CALM = "平静"
    DISGUSTED = "厌恶"
    SURPRISED = "惊讶"


@dataclass(frozen=True)
class VoiceEmotionResult:
    emotion: Emotion
    valence: float
    arousal: float
    dominance: float
    confidence: float = 1.0
    all_emotion_scores: Dict[str, float] = field(default_factory=dict)
    all_emotion_percentages: Dict[str, float] = field(default_factory=dict)
    top_emotions: List[Tuple[str, float]] = field(default_factory=list)

    @property
    def vector(self) -> List[float]:
        return [round(self.valence, 3), round(self.arousal, 3), round(self.dominance, 3)]

    @property
    def emotion_name(self) -> str:
        return self.emotion.value

    def get_top_k(self, k: int = 3) -> List[Tuple[str, float]]:
        return self.top_emotions[:k]

    def get_percentage(self, emotion_name: str) -> float:
        return self.all_emotion_percentages.get(emotion_name, 0.0)


class VADGenerator:
    """V-A-D 值生成器"""

    def __init__(self):
        self.vad_map = {
            'happy': (0.86, 0.72, 0.62),
            'sad': (0.18, 0.32, 0.38),
            'angry': (0.12, 0.78, 0.67),
            'fear': (0.18, 0.86, 0.25),
            'neutral': (0.52, 0.22, 0.55),
            'surprise': (0.63, 0.74, 0.48)
        }

    def generate(self, emotion_label: str, probabilities: List[float]) -> Tuple[float, float, float, float]:
        valence, arousal, dominance = self.vad_map.get(emotion_label, (0.5, 0.5, 0.5))

        max_prob = max(probabilities)
        confidence = float(max_prob)

        return valence, arousal, dominance, confidence


class VoiceEmotionAnalyzer:
    def __init__(self):
        self.recognizer = self._load_model()
        self.vad_generator = VADGenerator()
        self.label_mapping = {
            'angry': Emotion.ANGRY,
            'fear': Emotion.FEARFUL,
            'happy': Emotion.HAPPY,
            'neutral': Emotion.CALM,
            'sad': Emotion.SAD,
            'surprise': Emotion.SURPRISED
        }

    def _load_model(self):
        """加载 LSTM 模型"""
        lstm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'speech_emotion_recognition_predict'))

        if lstm_path not in sys.path:
            sys.path.insert(0, lstm_path)

        try:
            from predict import SpeechEmotionRecognizer

            config_path = os.path.join(lstm_path, 'configs', 'predict.yaml')

            old_cwd = os.getcwd()
            os.chdir(lstm_path)

            try:
                logger.info(f"Loading LSTM model from: {config_path}")
                logger.info(f"Working directory: {os.getcwd()}")
                recognizer = SpeechEmotionRecognizer(config_path)

                if hasattr(recognizer.config, 'checkpoint_path'):
                    recognizer.config.checkpoint_path = os.path.join(lstm_path, 'checkpoints')
                if hasattr(recognizer.config, 'feature_folder'):
                    recognizer.config.feature_folder = os.path.join(lstm_path, 'features')

                return recognizer
            finally:
                os.chdir(old_cwd)

        except Exception as e:
            logger.error(f"Failed to load LSTM model: {e}")
            raise RuntimeError(f"无法加载 LSTM 模型: {e}")

    def analyze(self, audio_path: str) -> VoiceEmotionResult:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        try:
            emotion_label, probabilities = self.recognizer.predict(audio_path)

            if not hasattr(probabilities, '__iter__') or isinstance(probabilities, (float, int)):
                probabilities = [probabilities]
            elif hasattr(probabilities, 'shape') and len(probabilities.shape) == 0:
                probabilities = [float(probabilities)]
            elif hasattr(probabilities, 'tolist'):
                probabilities = probabilities.tolist()

            labels = self.recognizer.get_emotion_labels()

            percentages = {}
            all_scores = {}

            for label, prob in zip(labels, probabilities):
                emotion_enum = self.label_mapping.get(label)
                if emotion_enum:
                    percentages[emotion_enum.value] = float(prob * 100)
                    all_scores[emotion_enum.value] = float(prob * 100)

            for emotion in Emotion:
                if emotion.value not in percentages:
                    percentages[emotion.value] = 0.0
                    all_scores[emotion.value] = 0.0

            emotion = self.label_mapping.get(emotion_label, Emotion.CALM)

            valence, arousal, dominance, confidence = self.vad_generator.generate(emotion_label, probabilities)

            top_emotions = sorted(percentages.items(), key=lambda x: x[1], reverse=True)[:3]

            return VoiceEmotionResult(
                emotion=emotion,
                valence=valence,
                arousal=arousal,
                dominance=dominance,
                confidence=confidence,
                all_emotion_scores=all_scores,
                all_emotion_percentages=percentages,
                top_emotions=top_emotions
            )

        except Exception as e:
            logger.error(f"音频分析失败: {e}")
            raise


_analyzer = None


def _get_analyzer() -> VoiceEmotionAnalyzer:
    """懒加载获取分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = VoiceEmotionAnalyzer()
    return _analyzer


def analyze_voice(audio_path: str) -> VoiceEmotionResult:
    """分析语音情感，返回完整结果（包含多情感概率）"""
    return _get_analyzer().analyze(audio_path)


def analyze_voice_simple(audio_path: str) -> str:
    """简化版：只返回主要情感名称"""
    result = _get_analyzer().analyze(audio_path)
    return result.emotion_name


def analyze_voice_with_probs(audio_path: str) -> Tuple[str, Dict[str, float]]:
    """分析语音情感，返回主要情感和所有情感百分比"""
    result = _get_analyzer().analyze(audio_path)
    return result.emotion_name, result.all_emotion_percentages


def analyze_voice_top_k(audio_path: str, k: int = 3) -> List[Tuple[str, float]]:
    """分析语音情感，返回前k个情感及其百分比"""
    result = _get_analyzer().analyze(audio_path)
    return result.get_top_k(k)


__all__ = [
    'VoiceEmotionResult',
    'VoiceEmotionAnalyzer',
    'analyze_voice',
    'analyze_voice_simple',
    'analyze_voice_with_probs',
    'analyze_voice_top_k',
    'Emotion'
]
