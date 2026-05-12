# EmotionMirror — 基于多模态情绪感知的数字分身系统

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Node.js-16+-green.svg" alt="Node.js Version">
  <img src="https://img.shields.io/badge/React-19.x-61DAFB.svg" alt="React Version">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688.svg" alt="FastAPI Version">
</div>

## 项目简介

EmotionMirror 是一个基于**多模态情绪感知**的数字分身系统，能够通过文本、语音等多模态输入感知用户情绪，并驱动虚拟数字人进行情绪化交互。

### 系统架构

系统采用四层架构设计：

| 层级 | 名称 | 职责 | 技术栈 |
|------|------|------|--------|
| Layer 1 | 多模态输入层 | 前端交互界面，提供文本/语音/视觉三种输入方式 | React + Vite |
| Layer 2 | 情感分析层 | 文本与语音的情绪识别，输出 Emotion Vector | FastAPI + LSTM |
| Layer 3 | 情绪反馈层 | 根据 Emotion Vector 生成数字分身表情与氛围效果 | - |
| Layer 4 | 人机交互层 | 数字分身桌面展示，视线追踪等交互能力 | - |

### 核心功能

- **文本情感分析**：基于规则驱动的关键词匹配与强度调节
- **语音情感识别**：基于 LSTM 的语音情感分类模型
- **情绪向量输出**：统一的 V-A-D（效价/唤醒度/优势度）三维情绪模型
- **数字分身展示**：支持用户自定义数字形象上传

---

## 快速开始

### 环境要求

- **前端**: Node.js >= 16
- **后端**: Python >= 3.10
- **包管理器**: [uv](https://docs.astral.sh/uv/)（Python）、npm（前端）

### 安装依赖

```bash
# 安装所有 Python 依赖（包括语音识别模块）
uv sync

# 安装前端依赖
cd frontend && npm install && cd ..
```

### 启动服务

需要两个终端分别启动后端和前端：

```bash
# 终端 1 — 启动后端服务（端口 8000）
uv run uvicorn backend.app:app --reload --port 8000
```

```bash
# 终端 2 — 启动前端开发服务器
cd frontend && npm run dev
```

启动后访问前端地址（默认 `http://localhost:5173/`）即可使用系统。

### 故障排除

**问题1**：`'vite' 不是内部或外部命令`

**解决方案**：
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**问题2**：`Form data requires "python-multipart" to be installed`

**解决方案**：确保已执行 `uv sync`，如果仍有问题：
```bash
uv pip install python-multipart
```

---

## 项目结构

```
EmotionMirror/
├── backend/                          # 后端服务
│   ├── speech_emotion_recognition_predict/  # 语音情感识别模块
│   │   ├── checkpoints/              # 模型权重文件
│   │   │   ├── LSTM_LIBROSA_IS10.h5
│   │   │   ├── LSTM_LIBROSA_IS10.json
│   │   │   └── SCALER_LIBROSA.m
│   │   ├── configs/                  # 配置文件
│   │   ├── extract_feats/            # 特征提取
│   │   ├── features/                 # 特征存储
│   │   ├── models/                   # 模型定义
│   │   ├── utils/                    # 工具函数
│   │   ├── predict.py                # 语音预测接口
│   │   └── requirements.txt
│   ├── app.py                        # FastAPI 入口
│   ├── schemas.py                    # 数据模型定义
│   ├── text_emotion.py               # 文本情感分析
│   ├── voice_emotion.py              # 语音情感分析接口
│   ├── voice_emo_example.py          # 语音情感分析示例
│   └── sample.wav                    # 示例音频
├── frontend/                         # 前端工程
│   ├── public/                       # 静态资源
│   ├── src/
│   │   ├── assets/                   # 资源文件
│   │   ├── components/               # React 组件
│   │   │   ├── TopNav.jsx            # 顶部导航栏
│   │   │   ├── Sidebar.jsx           # 工作流侧栏
│   │   │   ├── StepInput.jsx         # 情绪输入组件
│   │   │   ├── StepAvatar.jsx        # 数字形象上传
│   │   │   ├── StepAnalysis.jsx      # 情绪分析结果
│   │   │   └── StepDigitalTwin.jsx   # 数字分身展示
│   │   ├── services/
│   │   │   └── api.js                # API 接口封装
│   │   ├── App.jsx                   # 根组件
│   │   ├── App.css                   # 全局样式
│   │   └── main.jsx                  # 应用入口
│   ├── package.json
│   └── vite.config.js
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## API 接口文档

### 统一情绪输出规范

所有情感分析接口返回统一格式：

| 字段 | 类型 | 说明 |
|------|------|------|
| `emotion` | string | 情绪标签（开心、悲伤、愤怒、焦虑、恐惧、平静、厌恶、惊讶） |
| `vector` | array[3] | V-A-D 三维情绪向量，范围 [0, 1] |

**V-A-D 模型说明**：
- **Valence（效价）**：情绪的正负性，越高越积极
- **Arousal（唤醒度）**：情绪的强度/活跃度
- **Dominance（优势度）**：情绪的控制感/影响力

---

### 健康检查

```
GET /api/health

响应体：
{
  "status": "ok"
}
```

---

### 文本情感分析

```
POST /api/text-emotion
Content-Type: application/json

请求体：
{
  "text": "今天面试通过了我真的太开心了！"
}

响应体：
{
  "emotion": "开心",
  "vector": [0.85, 0.72, 0.61]
}
```

---

### 语音情感分析

```
POST /api/voice-emotion
Content-Type: multipart/form-data

请求体：
  audio: <音频文件>（支持 WAV/MP3/M4A）

响应体：
{
  "emotion": "平静",
  "vector": [0.45, 0.30, 0.55]
}
```

---

### 上传数字分身形象

```
POST /api/avatar/upload
Content-Type: multipart/form-data

请求体：
  image: <图片文件>（支持 JPG/PNG/WebP）

响应体：
{
  "avatar_url": "/avatars/xxx.png",
  "message": "上传成功"
}
```

---

### 获取数字分身表情列表

```
GET /api/avatar/emotions

响应体：
{
  "emotions": ["开心", "悲伤", "愤怒", "焦虑", "恐惧", "平静", "厌恶", "惊讶"],
  "avatar_url": "/avatars/current.png"
}
```

---

## 工作流程

前端采用 4 步引导式工作流：

1. **情绪输入** — 选择文本或语音模态，输入需要分析的内容
2. **数字形象** — 上传数字分身的基础形象（自拍/二次元/卡通）
3. **情绪分析** — 展示分析结果，包含情绪标签与情绪维度向量
4. **数字分身** — 展示情绪化数字分身（等待 Layer 3/4 对接）

---

## 技术栈

### 前端
- React 19 + Vite 8
- Lucide React（图标库）
- Axios（HTTP 请求）
- CSS Variables（设计系统）

### 后端
- FastAPI（API 框架）
- TensorFlow 2.x（语音情感识别模型）
- Librosa（音频特征提取）
- scikit-learn（数据处理）

---

## 支持的情感类别

| 标签 | 中文 | 说明 |
|------|------|------|
| happy | 开心 | 积极、愉悦的情绪 |
| sad | 悲伤 | 消极、低落的情绪 |
| angry | 愤怒 | 生气、恼怒的情绪 |
| fear | 恐惧 | 害怕、担忧的情绪 |
| surprise | 惊讶 | 意外、吃惊的情绪 |
| neutral | 平静 | 中性、无明显情绪 |
| anxious | 焦虑 | 紧张、不安的情绪 |
| disgust | 厌恶 | 反感、嫌恶的情绪 |

---

## 参考资源

- 文本情感分析：BERT
- 语音情感识别：[Renovamen/Speech-Emotion-Recognition](https://github.com/Renovamen/Speech-Emotion-Recognition)
- 表情生成：[davidliszhou/dynamic-emoji-generator](https://github.com/davidliszhou/dynamic-emoji-generator)
- 视线追踪：[Bharati-202/Eye-Follow-Cursor](https://github.com/bharati-202/eye-follow-cursor)
---

## 开发分工

| 成员 | 负责模块 | 层级 |
|------|----------|------|
| 组员A | 前端交互界面 | Layer 1 |
| 组员B | 文本情感分析 | Layer 2 |
| 组员C | 语音情感识别 | Layer 2 |
| 组员D | 数字分身表情生成 | Layer 3 |
| 组员E | 数字分身交互与桌面展示 | Layer 4 |