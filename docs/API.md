# API 接口文档

## POST /api/predict/text

**请求：**
```json
{ "text": "今天终于放假了！" }
```

**响应：**
```json
{
    "success": true,
    "emotion_vector": { "happy": 0.75, "sad": 0.10, "angry": 0.05, "calm": 0.10 },
    "dominant_emotion": "happy",
    "confidence": 0.75,
    "model": "bert-base-chinese"
}
```

## POST /api/predict/speech

**请求：** `multipart/form-data`，字段 `audio`

**响应：** 同上格式

## POST /api/predict/multimodal

**请求：**
```json
{
    "text": "今天终于放假了！",
    "text_emotion": { "happy": 0.8, "sad": 0.1, "angry": 0.05, "calm": 0.05 },
    "speech_emotion": { "happy": 0.6, "sad": 0.2, "angry": 0.1, "calm": 0.1 },
    "weights": { "text": 0.6, "speech": 0.4 }
}
```

## POST /api/upload/avatar

**请求：** `multipart/form-data`，字段 `avatar`

**响应：**
```json
{ "success": true, "url": "/static/avatars/xxx.png" }
```

## POST /api/upload/audio

**请求：** `multipart/form-data`，字段 `audio`

**响应：**
```json
{ "success": true, "url": "/static/audio/xxx.wav" }
```

## GET /api/health

**响应：**
```json
{ "status": "ok", "service": "EmotionMirror Backend", "version": "1.0.0" }
```
