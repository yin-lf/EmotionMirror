# 架构说明

## 系统分层

```
Layer1 输入层        → 文本 / 音频 / 图片
Layer2 情感分析层    → BERT文本情绪 + 语音情绪 → Emotion Vector
Layer3 情绪反馈层    → Emotion Vector → UI主题/粒子/表情
Layer4 人机交互层    → 数字分身展示 + 视线跟随
```

## Emotion Vector 标准

所有分析模块输出统一的 8 维概率分布：

```json
{
    "happy": 0.75,
    "sad": 0.10,
    "angry": 0.05,
    "calm": 0.10,
    "fear": 0.0,
    "surprise": 0.0,
    "disgust": 0.0,
    "neutral": 0.0
}
```

值之和为 1.0。

## 融合策略

TODO: 在 `backend/services/fusion.py` 中实现多模态融合。
