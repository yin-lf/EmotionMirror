from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class EmotionResult:
    emotion: str
    vector: List[float]


EMOTION_VAD: Dict[str, Tuple[float, float, float]] = {
    "开心": (0.86, 0.72, 0.62),
    "悲伤": (0.18, 0.32, 0.38),
    "愤怒": (0.12, 0.78, 0.67),
    "焦虑": (0.25, 0.82, 0.35),
    "恐惧": (0.18, 0.86, 0.25),
    "平静": (0.52, 0.22, 0.55),
    "厌恶": (0.10, 0.55, 0.42),
    "惊讶": (0.63, 0.74, 0.48),
}


EMOTION_KEYWORDS: Dict[str, Iterable[str]] = {
    "开心": [
        "开心",
        "高兴",
        "快乐",
        "喜悦",
        "幸福",
        "欣喜",
        "满意",
        "喜欢",
        "爱",
        "笑",
        "太棒了",
        "成功",
        "通过",
        "好消息",
    ],
    "悲伤": [
        "难过",
        "伤心",
        "悲伤",
        "失落",
        "沮丧",
        "心碎",
        "后悔",
        "遗憾",
        "哭",
        "失望",
        "孤独",
    ],
    "愤怒": [
        "生气",
        "愤怒",
        "恼火",
        "气炸了",
        "火大",
        "烦躁",
        "抓狂",
        "讨厌",
        "气愤",
    ],
    "焦虑": [
        "焦虑",
        "紧张",
        "担心",
        "不安",
        "忐忑",
        "压力",
        "害怕",
        "恐慌",
        "忧虑",
    ],
    "恐惧": [
        "恐惧",
        "害怕",
        "恐怖",
        "吓人",
        "惊恐",
        "畏惧",
    ],
    "平静": [
        "平静",
        "冷静",
        "放松",
        "安心",
        "舒缓",
        "淡定",
        "宁静",
        "稳定",
    ],
    "厌恶": [
        "恶心",
        "厌恶",
        "反感",
        "嫌弃",
        "讨厌",
        "恶感",
        "作呕",
    ],
    "惊讶": [
        "惊讶",
        "震惊",
        "惊喜",
        "意外",
        "不可思议",
        "哇",
        "天哪",
    ],
}

POSITIVE_WORDS = [
    "好",
    "棒",
    "优秀",
    "成功",
    "通过",
    "喜欢",
    "满意",
    "幸福",
    "开心",
    "值得",
    "顺利",
]

NEGATIVE_WORDS = [
    "差",
    "糟",
    "失败",
    "难",
    "失望",
    "难过",
    "讨厌",
    "烦",
    "压力",
    "恐惧",
]

INTENSIFIERS = ["非常", "特别", "超级", "太", "很", "极其", "真", "好"]
NEGATIONS = ["不", "没", "没有", "别", "无"]


def analyze_text(text: str) -> EmotionResult:
    cleaned = text.strip()
    if not cleaned:
        return EmotionResult("平静", list(EMOTION_VAD["平静"]))

    scores = _score_emotions(cleaned)
    emotion = _select_emotion(cleaned, scores)
    vector = _apply_intensity(cleaned, emotion)
    return EmotionResult(emotion, vector)


def _score_emotions(text: str) -> Dict[str, float]:
    scores = {emotion: 0.0 for emotion in EMOTION_VAD}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[emotion] += 1.0

    exclaim_count = text.count("!") + text.count("！")
    if exclaim_count:
        scores["惊讶"] += 0.4 * exclaim_count
        scores["开心"] += 0.2 * exclaim_count
        scores["愤怒"] += 0.2 * exclaim_count

    if any(neg in text for neg in NEGATIONS):
        scores["开心"] -= 0.4
        scores["悲伤"] += 0.3

    return scores


def _select_emotion(text: str, scores: Dict[str, float]) -> str:
    max_score = max(scores.values())
    if max_score <= 0.0:
        pos_count = _count_words(text, POSITIVE_WORDS)
        neg_count = _count_words(text, NEGATIVE_WORDS)
        if pos_count > neg_count:
            return "开心"
        if neg_count > pos_count:
            return "悲伤"
        if text.count("?") + text.count("？") > 0:
            return "焦虑"
        return "平静"

    top_emotions = [emotion for emotion, score in scores.items() if score == max_score]
    if len(top_emotions) == 1:
        return top_emotions[0]

    priority = ["愤怒", "焦虑", "恐惧", "悲伤", "厌恶", "惊讶", "开心", "平静"]
    for emotion in priority:
        if emotion in top_emotions:
            return emotion
    return top_emotions[0]


def _apply_intensity(text: str, emotion: str) -> List[float]:
    base_valence, base_arousal, base_dominance = EMOTION_VAD[emotion]
    intensifier_count = _count_words(text, INTENSIFIERS)
    exclaim_count = text.count("!") + text.count("！")
    intensity = min(1.0, 0.6 + 0.08 * intensifier_count + 0.05 * exclaim_count)

    arousal = _clamp(base_arousal * (1.0 + 0.35 * intensity))

    if emotion in {"开心", "惊讶"}:
        valence = _clamp(base_valence + 0.15 * intensity)
    elif emotion in {"悲伤", "愤怒", "恐惧", "厌恶", "焦虑"}:
        valence = _clamp(base_valence - 0.1 * intensity)
    else:
        valence = base_valence

    dominance = _clamp(base_dominance + 0.08 * intensity)

    return [round(valence, 3), round(arousal, 3), round(dominance, 3)]


def _count_words(text: str, words: Iterable[str]) -> int:
    return sum(1 for word in words if word in text)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))