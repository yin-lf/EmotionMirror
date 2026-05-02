# EmotionMirror — 基于多模态情绪感知的数字分身系统

## 项目简介

EmotionMirror 是一个通过**文本、语音、图像**等多模态输入感知用户情绪，并驱动虚拟数字人进行情绪化交互的系统。

**核心流程：**

```
文本/语音输入 → 情绪识别 → Emotion Vector → 数字分身情绪反馈 → UI 动态交互
```

## 项目结构

```
EmotionMirror/
├── backend/                    # Flask 后端
│   ├── app.py                  # 应用入口（工厂函数）
│   ├── config.py               # 配置文件
│   ├── routes/                 # API 路由
│   │   ├── health.py           #   健康检查
│   │   ├── emotion.py          #   情绪分析 API（TODO: 组员B/C）
│   │   └── upload.py           #   文件上传（TODO: 组员A）
│   ├── services/
│   │   └── fusion.py           #   Emotion Vector 融合（TODO）
│   └── utils/
│       └── response.py         #   响应工具
├── layer1_input/               # Layer1: 多模态输入层 — 组员A
│   ├── text_input.py           #   文本输入处理
│   ├── audio_input.py          #   音频输入处理
│   └── image_input.py          #   图片输入处理
├── layer2_text_emotion/        # Layer2: 文本情绪识别 — 组员B
│   ├── bert_emotion.py         #   BERT 情绪分类（TODO）
│   └── text_preprocess.py      #   文本预处理
├── layer2_speech_emotion/      # Layer2: 语音情绪识别 — 组员C
│   ├── speech_emotion.py       #   语音情绪识别（TODO）
│   └── audio_preprocess.py     #   音频预处理
├── layer3_emotion_feedback/    # Layer3: 情绪反馈层 — 组员D
│   ├── emotion_mapper.py       #   情绪→UI 映射（TODO）
│   ├── dynamic_emoji.py        #   动态表情生成
│   └── theme_engine.py         #   主题引擎
├── layer4_interaction/         # Layer4: 人机交互层 — 组员E
│   ├── avatar_display.py       #   数字分身展示
│   └── cursor_follower.py      #   鼠标视线跟随
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── App.jsx             #   主入口
│   │   ├── api/emotion.js      #   API 封装
│   │   ├── components/         #   组件
│   │   │   ├── InputPanel.jsx  #     输入面板 — 组员A
│   │   │   ├── EmotionRadar.jsx#     情绪雷达 — 组员D
│   │   │   ├── AvatarDisplay.jsx#    数字分身 — 组员E
│   │   │   ├── CursorFollower.jsx#   视线跟随 — 组员E
│   │   │   ├── ParticleBackground.jsx # 粒子背景 — 组员D
│   │   │   ├── DynamicTheme.jsx#     动态主题 — 组员D
│   │   │   └── Layout.jsx      #     布局
│   │   ├── hooks/              #   自定义 Hooks
│   │   │   ├── useEmotion.js
│   │   │   └── useCursorPosition.js
│   │   └── utils/
│   │       └── emotionUtils.js #   情绪工具函数
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
├── static/                     # 静态资源
│   ├── avatars/                #   头像存储
│   └── audio/                  #   音频存储
├── docs/                       # 文档
├── models/                     # 模型缓存
├── run_backend.py              # 后端启动
├── run_frontend.sh             # 前端启动
├── requirements.txt            # Python 依赖
└── README.md
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Vite + TailwindCSS + Framer Motion |
| 后端 | Flask + Python |
| 文本情绪 | BERT (Transformers) |
| 语音情绪 | Speech Emotion Recognition |
| 动态效果 | Dynamic Emoji + Eye-Follow-Cursor |

## Emotion Vector 格式

所有情绪分析模块统一输出以下格式：

```json
{
    "happy": 0.75,
    "sad": 0.10,
    "angry": 0.05,
    "calm": 0.10
}
```

## API 接口

| 方法 | 路径 | 说明 | 负责人 |
|------|------|------|--------|
| GET | /api/health | 健康检查 | — |
| POST | /api/predict/text | 文本情绪识别 | 组员B |
| POST | /api/predict/speech | 语音情绪识别 | 组员C |
| POST | /api/predict/multimodal | 多模态融合 | — |
| POST | /api/upload/avatar | 上传头像 | 组员A |
| POST | /api/upload/audio | 上传音频 | 组员A |

## 安装与运行

### 后端

```bash
pip install -r requirements.txt
python run_backend.py
```

### 前端

```bash
bash run_frontend.sh
# 或
cd frontend && npm install && npm run dev
```

## 分工

| 组员 | 负责模块 | 关键文件 |
|------|----------|----------|
| 组员A | Layer1 输入层 | `layer1_input/*`, `backend/routes/upload.py`, `InputPanel.jsx` |
| 组员B | 文本情绪识别 | `layer2_text_emotion/*`, `backend/routes/emotion.py`(text) |
| 组员C | 语音情绪识别 | `layer2_speech_emotion/*`, `backend/routes/emotion.py`(speech) |
| 组员D | 情绪反馈与表情 | `layer3_emotion_feedback/*`, `EmotionRadar.jsx`, `ParticleBackground.jsx` |
| 组员E | 数字分身交互 | `layer4_interaction/*`, `AvatarDisplay.jsx`, `CursorFollower.jsx` |

## 开发约定

- 所有 TODO 用 `# TODO(组员X):` 标注，方便搜索
- Emotion Vector 格式必须统一（8 个情绪维度）
- API 响应格式统一：`{"success": bool, ...}`
- 前端组件 Props 接口已在注释中预留
