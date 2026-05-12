# 语音情感识别 - 预测模块

基于 LSTM 的语音情感识别预测模块，支持对输入音频进行情感分类。

## 环境要求

- Python 3.8+
- TensorFlow 2.x
- librosa
- numpy
- scikit-learn
- joblib
- pyyaml

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行方式

```bash
python predict.py --audio path/to/your/audio.wav
```

### Python API 方式

```python
from predict import SpeechEmotionRecognizer

# 初始化识别器
recognizer = SpeechEmotionRecognizer()

# 预测音频情感
audio_path = "path/to/audio.wav"
emotion, probabilities = recognizer.predict(audio_path)

print(f"识别结果: {emotion}")
print("各类情感概率:")
for label, prob in zip(recognizer.get_emotion_labels(), probabilities):
    print(f"  {label}: {prob:.4f}")
```

## 支持的情感类别

- angry (愤怒)
- fear (恐惧)
- happy (开心)
- neutral (中性)
- sad (悲伤)
- surprise (惊讶)

## 项目结构

```
speech_emotion_recognition_predict/
├── configs/
│   └── predict.yaml      # 配置文件
├── checkpoints/
│   ├── LSTM_LIBROSA_IS10.h5    # 模型权重
│   ├── LSTM_LIBROSA_IS10.json  # 模型结构
│   └── SCALER_LIBROSA.m        # 标准化模型
├── extract_feats/
│   └── librosa.py       # 特征提取
├── models/
│   ├── base.py          # 模型基类
│   ├── __init__.py
│   └── dnn/
│       ├── dnn.py       # DNN基类
│       └── lstm.py      # LSTM模型
├── utils/
│   ├── __init__.py
│   └── opts.py          # 配置解析
├── predict.py           # 主预测接口
├── requirements.txt     # 依赖列表
└── README.md
```

## 配置说明

修改 `configs/predict.yaml` 可以调整配置：

```yaml
model: lstm                              # 使用的模型类型
class_labels: ["angry", "fear", ...]     # 情感标签列表
feature_folder: features/                # 特征临时存储目录
feature_method: l                        # 特征提取方式 (l: librosa)
checkpoint_path: checkpoints/            # 模型文件路径
checkpoint_name: LSTM_LIBROSA_IS10       # 模型文件名
```