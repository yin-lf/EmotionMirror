import os
import numpy as np
import extract_feats.librosa as lf
import models
import utils

class SpeechEmotionRecognizer:
    def __init__(self, config_path: str = 'configs/predict.yaml'):
        self.config = utils.parse_opt() if config_path is None else self._load_config(config_path)
        self.model = models.load(self.config)

    def _load_config(self, config_path: str) -> object:
        import yaml
        class Config:
            def __init__(self, entries: dict={}):
                for k, v in entries.items():
                    if k != 'params' and isinstance(v, dict):
                        self.__dict__[k] = Config(v)
                    else:
                        self.__dict__[k] = v

        f = open(config_path, 'r', encoding='utf-8')
        config_dict = yaml.load(f.read(), Loader=yaml.FullLoader)
        return Config(config_dict)

    def predict(self, audio_path: str) -> tuple:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        test_feature = lf.get_data(self.config, audio_path)
        result = self.model.predict(test_feature)
        result_prob = self.model.predict_proba(test_feature)

        emotion_label = self.config.class_labels[int(result)]

        return emotion_label, result_prob

    def get_emotion_labels(self) -> list:
        return self.config.class_labels

def main():
    import argparse

    parser = argparse.ArgumentParser(description='语音情感识别预测')
    parser.add_argument('--audio', required=True, help='音频文件路径')
    parser.add_argument('--config', default='configs/predict.yaml', help='配置文件路径')
    args = parser.parse_args()

    recognizer = SpeechEmotionRecognizer(args.config)
    emotion, probabilities = recognizer.predict(args.audio)

    print(f"识别结果: {emotion}")
    print("各类情感概率:")
    for label, prob in zip(recognizer.get_emotion_labels(), probabilities):
        print(f"  {label}: {prob:.4f}")

if __name__ == '__main__':
    main()