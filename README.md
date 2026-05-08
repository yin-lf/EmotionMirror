# EmotionMirror — 基于多模态情绪感知的数字分身系统

## 项目简介

本系统以"多模态情绪感知"和"数字分身动态反馈"为核心，构建一个能够通过文本、语音、图像等多模态输入感知用户情绪，并驱动虚拟数字人进行情绪化交互的系统。

系统划分为四个功能层：

| 层级 | 名称 | 职责 |
|------|------|------|
| Layer 1 | 多模态输入层 | 前端交互界面，提供文本/语音/视觉三种输入方式 |
| Layer 2 | 情感分析层 | 文本与语音的情绪识别，输出 Emotion Vector |
| Layer 3 | 情绪反馈层 | 根据 Emotion Vector 生成数字分身表情与氛围效果 |
| Layer 4 | 人机交互层 | 数字分身桌面展示，视线追踪等交互能力 |

## 分工

- **组员A**：构建系统前端交互界面（Layer 1）
- **组员B**：文本模态的情感分析（Layer 2）
- **组员C**：语音模态的情感分析（Layer 2）
- **组员D**：数字分身表情生成（Layer 3）
- **组员E**：数字分身交互与桌面展示（Layer 4）

## 项目结构

```
EmotionMirror/
├── backend/                          # 文本情感分析后端（Layer 2 / 组员B）
│   ├── app.py                        # FastAPI 入口
│   ├── text_emotion.py               # 文本情绪识别与 Emotion Vector 映射
│   └── __init__.py
├── frontend/                         # 前端工程（Layer 1）
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx                  # 应用入口
│       ├── App.jsx                   # 根组件（路由与状态管理）
│       ├── App.css                   # 全局样式与设计系统
│       ├── components/
│       │   ├── TopNav.jsx            # 顶部导航栏
│       │   ├── Sidebar.jsx           # 左侧工作流侧栏
│       │   ├── StepInput.jsx         # Step 1：文本/语音输入
│       │   ├── StepAvatar.jsx        # Step 2：数字形象上传
│       │   ├── StepAnalysis.jsx      # Step 3：情绪分析结果展示
│       │   └── StepDigitalTwin.jsx   # Step 4：数字分身（对接层）
│       └── services/
│           └── api.js                # 后端 API 接口封装
└── README.md
```

## 快速开始

### 环境要求

- Node.js >= 16
- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）

### 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
```

### 安装项目依赖

```bash
uv sync
cd frontend && npm install && cd ..
```

### 启动服务

先启动后端，再启动前端（需要两个终端）：

```bash
# 终端 1 — 后端
uv run uvicorn backend.app:app --reload --port 8000
```

```bash
# 终端 2 — 前端
cd frontend && npm run dev
```

前端通过 Vite 代理自动转发 `/api` 请求到后端，无需额外配置。启动后访问终端输出的地址即可（如 `http://localhost:5173/`）。

## 前端 API 接口

前端通过 `src/services/api.js` 统一调用后端接口。以下接口需要后端组员（B/C/D）按约定实现：

### 统一情绪输出规范（文本/语音通用）

- `emotion`：情绪标签字符串，建议在以下集合内统一：开心、悲伤、愤怒、焦虑、恐惧、平静、厌恶、惊讶。
- `vector`：长度为 3 的 V-A-D 向量，顺序为 效价(Valence)、唤醒度(Arousal)、优势度(Dominance)，范围 [0, 1]。

### 文本情感分析（对接组员B）

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

- `emotion`：情绪标签字符串
- `vector`：情绪向量，依次为 效价(Valence)、唤醒度(Arousal)、优势度(Dominance)，范围 [0, 1]

## 文本情感分析说明（组员B）

- 使用规则驱动的关键词匹配与强度调节，快速输出情绪标签与 Emotion Vector。
- 支持情绪类别：开心、悲伤、愤怒、焦虑、恐惧、平静、厌恶、惊讶。
- 输出向量遵循 V-A-D（Valence/Arousal/Dominance）三维情绪模型。

### 语音情感分析（对接组员C）

```
POST /api/voice-emotion
Content-Type: multipart/form-data

请求体：
  audio: <音频文件>（字段名 "audio"，支持 WAV/MP3/M4A）

响应体：
{
  "emotion": "平静",
  "vector": [0.45, 0.30, 0.55]
}

> 说明：语音与文本需保持相同 `emotion` 标签集合与 V-A-D 向量格式，便于前端与数字分身层统一对接。
```

### 上传数字分身形象

```
POST /api/avatar/upload
Content-Type: multipart/form-data

请求体：
  image: <图片文件>（字段名 "image"，支持 JPG/PNG/WebP）

响应体：
{
  "avatar_url": "/avatars/xxx.png",
  "message": "上传成功"
}
```

### 获取数字分身表情（对接组员D）

```
GET /api/avatar/emotions

响应体：
{
  "emotions": ["开心", "悲伤", "愤怒", ...],
  "avatar_url": "/avatars/current.png"
}
```

## 工作流程

前端采用 4 步引导式工作流：

1. **情绪输入** — 选择文本或语音模态，输入需要分析的内容
2. **数字形象** — 上传数字分身的基础形象（自拍/二次元/卡通）
3. **情绪分析** — 展示分析结果，包含情绪标签与情绪维度向量
4. **数字分身** — 展示情绪化数字分身（等待 Layer 3/4 对接）

## 技术栈

- React 18 + Vite
- Lucide React（图标）
- Axios（HTTP 请求）
- CSS Variables 设计系统

## 参考仓库

- 文本情感分析：Bert
- 语音情感识别：[Renovamen/Speech-Emotion-Recognition](https://github.com/Renovamen/Speech-Emotion-Recognition)
- 表情生成：[davidliszhou/dynamic-emoji-generator](https://github.com/davidliszhou/dynamic-emoji-generator)
- 视线追踪：[Bharati-202/Eye-Follow-Cursor](https://github.com/bharati-202/eye-follow-cursor)
