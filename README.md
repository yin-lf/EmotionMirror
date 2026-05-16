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


| 层级    | 名称         | 职责                                           | 技术栈         |
| ------- | ------------ | ---------------------------------------------- | -------------- |
| Layer 1 | 多模态输入层 | 前端交互界面，提供文本/语音/视觉三种输入方式   | React + Vite   |
| Layer 2 | 情感分析层   | 文本与语音的情绪识别，输出 Emotion Vector      | FastAPI + LSTM |
| Layer 3 | 情绪反馈层   | 根据 Emotion Vector 生成数字分身表情与氛围效果 | -              |
| Layer 4 | 人机交互层   | 数字分身桌面展示，视线追踪等交互能力           | -              |

### 核心功能

- **文本情感分析**：基于规则驱动的关键词匹配与强度调节
- **语音情感识别**：基于 LSTM 的语音情感分类模型
- **情绪向量输出**：统一的 V-A-D（效价/唤醒度/优势度）三维情绪模型
- **数字分身展示**：支持用户自定义数字形象上传
- **表情动画 GIF**：基于 LivePortrait 生成无缝循环表情动画，含头部微摆伪 3D 效果

---

## 快速开始

### 环境要求

- **前端**: Node.js >= 16
- **后端**: Python 3.10（Conda 环境名为 `emotion`）
- **GPU**: NVIDIA GPU（推荐，表情合成需要 CUDA）
- **包管理器**: Conda（后端）、npm（前端）

### 1. 创建 Conda 环境并安装依赖

```bash
# 创建 Python 3.10 环境
conda create -n emotion python=3.10 -y
conda activate emotion

# 安装后端依赖（所有依赖已声明在 pyproject.toml 中）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r <(grep '^	' pyproject.toml | sed 's/^[[:space:]]*"//;s/".*//' | grep -v torch)

# 或逐条安装核心依赖：
pip install fastapi uvicorn python-multipart pydantic
pip install tensorflow librosa scikit-learn joblib pyyaml soundfile
pip install -r backend/expression/LivePortrait/requirements.txt
pip install rembg imageio imageio-ffmpeg pillow scikit-image albumentations

# 安装前端依赖
cd frontend && npm install && cd ..
```

### 2. 下载 LivePortrait 预训练权重

```bash
# 下载权重到 backend/pretrained_weights/
huggingface-cli download KlingTeam/LivePortrait --local-dir pretrained_weights
```

### 3. 下载 rembg 背景去除模型(自动识别提取前景人物)

```bash
wget -O ~/.u2net/u2net.onnx https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

#windows
curl -o $env:USERPROFILE/.u2net/u2net.onnx https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx
```

### 4. 启动服务

需要两个终端分别启动后端和前端：

```bash
# 终端 1 — 启动后端服务（必须用 emotion 环境）
conda activate emotion
cd ~/EmotionMirror
uvicorn backend.app:app --reload --port 8000
```

```bash
# 终端 2 — 启动前端开发服务器
cd ~/EmotionMirror/frontend && npm run dev
```

启动后访问 `http://localhost:5173/` 即可使用系统。

---

## 桌宠（Desktop Pet）使用说明

EmotionMirror 支持将数字分身的表情动画以**浮窗桌宠**的形式展示在桌面上，基于 PySide6 实现。

### 环境准备

```bash
# 安装 PySide6（如尚未安装）
pip install PySide6
```

### 启动桌宠

确保后端已启动，然后在新终端中执行：

```bash
conda activate emotion
cd ~/EmotionMirror
python -m backend.desktop_pet --api http://127.0.0.1:8000
```

参数说明：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--api` | `http://127.0.0.1:8000` | FastAPI 后端地址 |
| `--poll-interval` | `2.5` | 轮询新表情的间隔（秒） |
| `--max-slots` | `6` | 最大缓存表情数 |

### 同步表情到桌宠

在前端完成情绪分析与表情生成后：

1. 在 **Step 4 数字分身** 页面点击 **「在桌面显示」** 按钮
2. 桌宠窗口会自动加载该表情，显示为带有透明背景的循环动画

### 窗口操作

| 操作 | 方式 |
|------|------|
| **拖拽移动** | 鼠标左键按住窗口任意位置拖动 |
| **缩放大小** | 拖拽窗口右下角/左下角调整大小 |
| **最小化** | 点击工具栏 `－` 按钮 |
| **关闭** | 点击工具栏 `×` 按钮 |
| **设置菜单** | 点击工具栏 `⚙` 按钮 |

### 右键菜单

在桌宠窗口上右键可打开菜单：

- **置顶显示** — 切换窗口是否始终在最前方
- **刷新表情** — 手动重新拉取后端表情数据
- **清除所有表情** — 清空当前显示的所有表情
- **退出** — 关闭桌宠

### 键盘快捷键

| 按键 | 功能 |
|------|------|
| `←` / `→` | 切换上一个/下一个表情 |

### 聊天交互与情绪反馈

桌宠内置了聊天对话框，实现情绪感知反馈闭环：

1. 在对话框输入文字，按回车或点击「发送」
2. 后端自动进行文本情绪分析
3. 使用预设的 **soyo.jpg** 照片自动生成对应情绪的表情 GIF
4. 桌宠立即切换显示该表情，同时在 **GIF 面板顶部弹出半透明对话气泡**（6 秒自动消失），对话框中保留历史记录
5. 无需前端操作即可在桌宠端完成完整的「输入→感知→表达」闭环

### 大模型接口与预设回复（Mock 模式）

回复生成支持两种模式：**LLM 模式**（调用 OpenAI 兼容 API）和 **Mock 模式**（使用预设文档），通过配置文件切换。

#### Mock 模式（预设回复）

默认开启。Soyo 根据情绪分析结果从 `backend/presets/chat_presets.json` 中随机选取预设回复，不依赖外部 API。

配置文件：

```json
{
  "mock_enabled": true,
  "replies": {
    "开心": ["哇，感受到你的快乐了！", "开心最好了～", "嘻嘻，你开心我就开心 🎉"],
    "悲伤": ["别难过，我在这儿陪着你呢 🌸", "抱抱你，一切都会好起来的 💕"],
    "愤怒": ["消消气，深呼吸～", "生气伤身体，先喝口水冷静一下～"],
    "焦虑": ["放轻松，一步一步来，一切都会好的 🌿", "深呼吸～跟我一起，呼……吸……"],
    "恐惧": ["别怕，有我在呢，你很安全 🤝", "我会一直守护你的。"],
    "平静": ["嗯，宁静的感觉真好～", "平静的时光最珍贵了。"],
    "厌恶": ["看来你不太喜欢这个呢，换个心情吧 🍃", "嗯嗯，我懂的，那就不提它了。"],
    "惊讶": ["哇，这可真让人意外！😮", "天哪，没想到会这样！"]
  },
  "fallback": "嗯嗯，我在听，你继续说～",
  "system_prompt": "你是一个名为 Soyo 的桌面宠物..."
}
```

| 配置项 | 说明 |
|--------|------|
| `mock_enabled` | `true` 时跳过 LLM，仅用预设回复；`false` 时优先调用 LLM，失败回退到预设 |
| `replies` | 按情绪分类的预设回复列表（每条情绪可配置多条，随机选取） |
| `fallback` | 情绪未匹配时的兜底回复 |
| `system_prompt` | LLM 模式下使用的系统提示词（默认：`你是一个名为 Soyo 的桌面宠物，正在和朋友聊天...`） |

可通过环境变量 `PRESETS_PATH` 指定自定义配置文件路径。

#### LLM 模式

回复生成支持 OpenAI 兼容 API，通过环境变量配置：

```bash
# 启动后端前设置（以 OpenAI 为例）
set LLM_API_URL=https://api.openai.com/v1/chat/completions
set LLM_API_KEY=sk-your-key-here
set LLM_MODEL=gpt-4o-mini    # 可选，默认 gpt-4o-mini

# 或使用本地模型（如 Ollama）
set LLM_BASE_URL=http://localhost:11434/v1
set LLM_API_KEY=ollama
set LLM_MODEL=qwen2.5:7b

# SiliconFlow / 其他兼容服务
set LLM_BASE_URL=https://api.siliconflow.cn/v1
set LLM_API_KEY=sk-your-key-here
set LLM_MODEL=deepseek-ai/DeepSeek-V2.5

# 然后正常启动后端
uvicorn backend.app:app --reload --port 8000
```

**LLM 调用增强**：

- **自动补全路径** — 环境变量支持 `LLM_API_URL`（完整端点）或 `LLM_BASE_URL`（基础路径），代码自动补全 `/chat/completions`
- **对话历史** — 保留最近 10 轮对话记录，每次请求携带历史上下文，回答更连贯
- **情绪标注** — 每条用户消息自动添加 `[情绪: 开心/悲伤/...]` 前缀，让大模型感知情绪状态
- **超时回退** — LLM 调用超时或失败时自动回退到预设回复，不影响功能

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `LLM_API_URL` / `LLM_BASE_URL` | OpenAI 兼容的聊天补全 API 地址 | 空 |
| `LLM_API_KEY` | API 密钥 | 空 |
| `LLM_MODEL` | 模型名称 | `gpt-4o-mini` |
| `PRESETS_PATH` | 预设回复配置文件路径 | `backend/presets/chat_presets.json` |

在 `chat_presets.json` 中将 `mock_enabled` 设为 `false` 即可启用 LLM 模式。不配置 LLM 环境变量时自动回退到预设回复，不影响功能。

### 配置方法

后端启动时会自动读取项目根目录下的 `.env` 文件（参考 `.env.example` 修改）：

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 填入你的 API Key
# 然后正常启动，无需手动 set 变量
uvicorn backend.app:app --reload --port 8000
```

### 功能特性

- **多表情切换** — 支持多种情绪表情在同一个窗口中轮播
- **聊天交互** — 内置对话框，输入文字即可驱动 Soyo 的表情变化与文字回应
- **情绪反馈闭环** — 输入→情绪分析→表情生成→展示+回复，全自动完成
- **交叉淡入淡出** — 表情切换时有平滑的过渡动画
- **透明背景** — 自动去除图片背景，只保留人物主体
- **自适应比例** — 表情图片保持原始宽高比显示，不变形
- **无缝循环** — 表情动画首尾帧一致，循环播放无跳帧

### 注意事项

- 后端**必须用 `emotion` conda 环境启动**，`uv run` 使用的是 `.venv`，缺少 LivePortrait 依赖
- TensorFlow 与 CUDA 驱动版本不兼容时，语音情感识别会自动回退到 CPU 运行
- 首次调用表情合成接口时会加载 LivePortrait 模型（约 10 秒），之后会缓存
- `libcudnn.so.8: cannot open shared object file` 是 ONNX runtime 的警告，不影响功能。如需消除：

```bash
conda install -c conda-forge cudnn
```

---

## 项目结构

```
EmotionMirror/
├── backend/                                          # 后端服务
│   ├── app.py                                        # FastAPI 入口 & 路由定义
│   ├── schemas.py                                    # 请求/响应数据模型
│   │
│   ├── text_emotion/                                 # 文本情感分析模块
│   │   ├── __init__.py
│   │   └── analyzer.py                              # 基于规则驱动的关键词匹配
│   │
│   ├── voice_emotion/                                # 语音情感识别模块
│   │   ├── __init__.py
│   │   ├── analyzer.py                              # 语音情感分析 API（VAD 输出）
│   │   ├── sample.wav                               # 示例音频
│   │   └── speech_emotion_recognition_predict/      # LSTM 语音情感识别子模块
│   │       ├── predict.py                           # 预测入口
│   │       ├── configs/predict.yaml                 # 推理配置
│   │       ├── checkpoints/                         # LSTM 模型权重 & 标准化器
│   │       ├── extract_feats/librosa.py             # Librosa 音频特征提取
│   │       ├── models/                              # 模型定义（LSTM / DNN）
│   │       ├── features/                            # 特征缓存
│   │       └── utils/                               # 工具函数
│   │
│   ├── expression/                                   # 数字分身表情生成模块
│   │   ├── __init__.py
│   │   ├── synthesis.py                            # 表情合成（单帧 & GIF 动画 + 头部微摆）
│   │   ├── LivePortrait/                            # LivePortrait 表情驱动引擎
│   │   │   ├── src/
│   │   │   │   ├── gradio_pipeline.py               # 推理管线入口
│   │   │   │   ├── live_portrait_pipeline.py        # 表情驱动主流程
│   │   │   │   ├── live_portrait_wrapper.py         # 模型加载与封装
│   │   │   │   ├── config/                          # 推理 / 裁剪 / 参数配置
│   │   │   │   ├── modules/                         # 外观特征提取 / 运动提取 / 生成网络
│   │   │   │   └── utils/                           # 人脸检测 / 裁剪 / 相机工具
│   │   │   ├── requirements.txt
│   │   │   └── requirements_base.txt
│   │   └── dynamic-emoji-generator/                 # 动态表情资源页面
│   │
│   ├── pretrained_weights/                          # LivePortrait 预训练权重（huggingface）
│   └── __init__.py
│
├── frontend/                                         # 前端工程（React + Vite）
│   ├── src/
│   │   ├── components/                               # 工作流 UI 组件
│   │   │   ├── TopNav.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── StepInput.jsx                         # 情绪输入
│   │   │   ├── StepAvatar.jsx                        # 数字形象上传
│   │   │   ├── StepAnalysis.jsx                      # 情绪分析结果
│   │   │   └── StepDigitalTwin.jsx                   # 数字分身展示
│   │   ├── services/api.js                           # 后端接口封装
│   │   ├── assets/                                   # 图片与图标资源
│   │   ├── App.jsx / App.css
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
│
├── pyproject.toml                                    # 项目依赖声明
├── TESTING.md                                        # 测试说明
└── README.md
```

---

## API 接口文档

### 统一情绪输出规范

所有情感分析接口返回统一格式：


| 字段      | 类型     | 说明                                                       |
| --------- | -------- | ---------------------------------------------------------- |
| `emotion` | string   | 情绪标签（开心、悲伤、愤怒、焦虑、恐惧、平静、厌恶、惊讶） |
| `vector`  | array[3] | V-A-D 三维情绪向量，范围 [0, 1]                            |

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

前端采用 5 步引导式工作流：

1. **情绪输入** — 选择文本或语音模态，输入需要分析的内容
2. **数字形象** — 上传数字分身的基础形象（自拍/二次元/卡通）
3. **情绪分析** — 展示分析结果，包含情绪标签与情绪维度向量
4. **数字分身** — 展示情绪化数字分身，支持生成动态表情 GIF
5. **桌面桌宠** — 将表情同步到桌面浮窗展示

---

## 技术栈

### 前端

- React 19 + Vite 8
- Lucide React（图标库）
- Axios（HTTP 请求）
- CSS Variables（设计系统）

### 后端

- FastAPI（API 框架）
- TensorFlow 2.x（语音情感识别模型，CPU 推理）
- PyTorch + LivePortrait（人脸表情驱动与动画生成）
- Librosa（音频特征提取）
- scikit-learn（数据处理）
- rembg（背景去除）

---

## 支持的情感类别


| 标签     | 中文 | 说明             |
| -------- | ---- | ---------------- |
| happy    | 开心 | 积极、愉悦的情绪 |
| sad      | 悲伤 | 消极、低落的情绪 |
| angry    | 愤怒 | 生气、恼怒的情绪 |
| fear     | 恐惧 | 害怕、担忧的情绪 |
| surprise | 惊讶 | 意外、吃惊的情绪 |
| neutral  | 平静 | 中性、无明显情绪 |
| anxious  | 焦虑 | 紧张、不安的情绪 |
| disgust  | 厌恶 | 反感、嫌恶的情绪 |

---

## 参考资源

- 文本情感分析：BERT
- 语音情感识别：[Renovamen/Speech-Emotion-Recognition](https://github.com/Renovamen/Speech-Emotion-Recognition)
- 表情生成：[KlingAIResearch/LivePortrait: Bring portraits to life!](https://github.com/KlingAIResearch/LivePortrait)
- 视线追踪：[Bharati-202/Eye-Follow-Cursor](https://github.com/bharati-202/eye-follow-cursor)

---

## 开发分工


| 成员  | 负责模块               | 层级    |
| ----- | ---------------------- | ------- |
| 组员A | 前端交互界面           | Layer 1 |
| 组员B | 文本情感分析           | Layer 2 |
| 组员C | 语音情感识别           | Layer 2 |
| 组员D | 数字分身表情生成       | Layer 3 |
| 组员E | 数字分身交互与桌面展示 | Layer 4 |
