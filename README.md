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
pip install -r backend/LivePortrait/requirements.txt
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

前端采用 4 步引导式工作流：

1. **情绪输入** — 选择文本或语音模态，输入需要分析的内容
2. **数字形象** — 上传数字分身的基础形象（自拍/二次元/卡通）
3. **情绪分析** — 展示分析结果，包含情绪标签与情绪维度向量
4. **数字分身** — 展示情绪化数字分身
5. 桌宠生成 —（等待 Layer 4 对接）

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
