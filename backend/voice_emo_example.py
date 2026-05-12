# voice_emotion.py - 语音情感分析模块（增强版，支持多情感概率）

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Emotion(Enum):
    """情感枚举"""
    HAPPY = "开心"
    SAD = "悲伤"
    ANGRY = "愤怒"
    ANXIOUS = "焦虑"
    FEARFUL = "恐惧"
    CALM = "平静"
    DISGUSTED = "厌恶"
    SURPRISED = "惊讶"


@dataclass(frozen=True)
class VoiceEmotionResult:
    """语音情感分析结果"""
    emotion: Emotion
    valence: float
    arousal: float
    dominance: float
    confidence: float = 1.0
    # 新增：所有情感的分数和百分比
    all_emotion_scores: Dict[str, float] = field(default_factory=dict)
    all_emotion_percentages: Dict[str, float] = field(default_factory=dict)
    top_emotions: List[Tuple[str, float]] = field(default_factory=list)
    
    @property
    def vector(self) -> List[float]:
        return [round(self.valence, 3), round(self.arousal, 3), round(self.dominance, 3)]
    
    @property
    def emotion_name(self) -> str:
        return self.emotion.value
    
    def get_top_k(self, k: int = 3) -> List[Tuple[str, float]]:
        """获取前 k 个情感及其百分比"""
        return self.top_emotions[:k]
    
    def get_percentage(self, emotion_name: str) -> float:
        """获取指定情感的百分比"""
        return self.all_emotion_percentages.get(emotion_name, 0.0)


@dataclass
class AudioFeatures:
    """音频特征数据容器"""
    duration: float = 0.0
    rms_mean: float = 0.0
    rms_std: float = 0.0
    rms_max: float = 0.0
    rms_percentile_90: float = 0.0
    zcr_mean: float = 0.0
    zcr_std: float = 0.0
    spectral_centroid_mean: float = 0.0
    spectral_centroid_std: float = 0.0
    spectral_bandwidth_mean: float = 0.0
    spectral_contrast_mean: float = 0.0
    spectral_contrast_std: float = 0.0
    rolloff_mean: float = 0.0
    rolloff_std: float = 0.0
    spectral_flatness_mean: float = 0.0
    tempo: float = 60.0
    tempo_confidence: float = 0.0
    mfcc_means: List[float] = field(default_factory=list)
    mfcc_stds: List[float] = field(default_factory=list)
    pitch_mean: float = 0.0
    pitch_std: float = 0.0
    pitch_max: float = 0.0
    pitch_min: float = 0.0
    pitch_range: float = 0.0
    pitch_slope: float = 0.0
    shimmer: float = 0.0
    jitter: float = 0.0
    hnr_mean: float = 0.0
    energy_entropy: float = 0.0
    spectral_flux_mean: float = 0.0
    spectral_flux_std: float = 0.0
    formant_f1: float = 0.0
    formant_f2: float = 0.0
    formant_f3: float = 0.0
    speaking_rate: float = 0.0


class FeatureExtractor:
    """鲁棒的特征提取器"""
    
    def __init__(self, sr: int = 22050, frame_length: int = 2048, hop_length: int = 512):
        self.sr = sr
        self.frame_length = frame_length
        self.hop_length = hop_length
    
    def extract(self, audio_path: str) -> Optional[AudioFeatures]:
        """提取音频特征"""
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(audio_path, sr=self.sr)
            
            # 去除静音
            y_trimmed, _ = librosa.effects.trim(y, top_db=25)
            if len(y_trimmed) > int(0.5 * sr):
                y = y_trimmed
            
            features = AudioFeatures()
            features.duration = len(y) / sr
            
            # 能量特征
            rms = librosa.feature.rms(y=y, frame_length=self.frame_length, hop_length=self.hop_length)[0]
            features.rms_mean = float(np.mean(rms))
            features.rms_std = float(np.std(rms))
            features.rms_max = float(np.max(rms))
            features.rms_percentile_90 = float(np.percentile(rms, 90))
            
            # 过零率
            zcr = librosa.feature.zero_crossing_rate(y=y, frame_length=self.frame_length, hop_length=self.hop_length)[0]
            features.zcr_mean = float(np.mean(zcr))
            features.zcr_std = float(np.std(zcr))
            
            # 频谱特征
            sc = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=self.frame_length, hop_length=self.hop_length)[0]
            features.spectral_centroid_mean = float(np.mean(sc))
            features.spectral_centroid_std = float(np.std(sc))
            
            sb = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=self.frame_length, hop_length=self.hop_length)[0]
            features.spectral_bandwidth_mean = float(np.mean(sb))
            
            contrast = librosa.feature.spectral_contrast(y=y, sr=sr, n_fft=self.frame_length, hop_length=self.hop_length)
            features.spectral_contrast_mean = float(np.mean(contrast))
            features.spectral_contrast_std = float(np.std(contrast))
            
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=self.frame_length, hop_length=self.hop_length)[0]
            features.rolloff_mean = float(np.mean(rolloff))
            features.rolloff_std = float(np.std(rolloff))
            
            flatness = librosa.feature.spectral_flatness(y=y, n_fft=self.frame_length, hop_length=self.hop_length)[0]
            features.spectral_flatness_mean = float(np.mean(flatness))
            
            # MFCC
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=self.frame_length, hop_length=self.hop_length)
            features.mfcc_means = [float(np.mean(mfcc[i])) for i in range(min(13, len(mfcc)))]
            features.mfcc_stds = [float(np.std(mfcc[i])) for i in range(min(13, len(mfcc)))]
            
            # 节奏
            try:
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                features.tempo = float(tempo) if hasattr(tempo, '__float__') else float(tempo[0])
                features.tempo_confidence = 0.7
            except:
                features.tempo = 60.0
                features.tempo_confidence = 0.5
            
            # 音高特征
            f0, voiced_flag, _ = librosa.pyin(y, fmin=80, fmax=450, sr=sr, 
                                               frame_length=self.frame_length, hop_length=self.hop_length)
            f0_voiced = f0[voiced_flag]
            if len(f0_voiced) > 5:
                features.pitch_mean = float(np.mean(f0_voiced))
                features.pitch_std = float(np.std(f0_voiced))
                features.pitch_max = float(np.max(f0_voiced))
                features.pitch_min = float(np.min(f0_voiced))
                features.pitch_range = features.pitch_max - features.pitch_min
                if len(f0_voiced) > 1:
                    x = np.arange(len(f0_voiced))
                    features.pitch_slope = float(np.polyfit(x, f0_voiced, 1)[0])
            
            # 声音质量
            features.shimmer = features.rms_std / (features.rms_mean + 1e-8)
            features.jitter = features.pitch_std / (features.pitch_mean + 1e-8)
            
            # 动态特征
            stft = np.abs(librosa.stft(y, n_fft=self.frame_length, hop_length=self.hop_length))
            spectral_flux = np.sqrt(np.sum(np.diff(stft, axis=1)**2, axis=0))
            if len(spectral_flux) > 0:
                features.spectral_flux_mean = float(np.mean(spectral_flux))
                features.spectral_flux_std = float(np.std(spectral_flux))
            
            energy = np.sum(stft**2, axis=0)
            energy_norm = energy / (np.sum(energy) + 1e-10)
            features.energy_entropy = -float(np.sum(energy_norm * np.log2(energy_norm + 1e-10)))
            
            harmonic = librosa.effects.harmonic(y)
            features.hnr_mean = float(np.mean(np.abs(harmonic)))
            
            # 共振峰
            try:
                n_coeffs = 12
                lpc_coeffs = librosa.lpc(y, order=n_coeffs)
                roots = np.roots(lpc_coeffs)
                roots = [r for r in roots if np.imag(r) >= 0]
                angles = np.arctan2(np.imag(roots), np.real(roots))
                freqs = angles * (sr / (2 * np.pi))
                formants = sorted([f for f in freqs if 0 < f < 5000])[:3]
                features.formant_f1 = formants[0] if len(formants) > 0 else 500.0
                features.formant_f2 = formants[1] if len(formants) > 1 else 1500.0
                features.formant_f3 = formants[2] if len(formants) > 2 else 2500.0
            except:
                features.formant_f1, features.formant_f2, features.formant_f3 = 500.0, 1500.0, 2500.0
            
            # 语速
            try:
                voice_activity = (rms > np.percentile(rms, 20)) & (zcr > 0.02)
                syllable_count = max(1, np.sum(voice_activity) // 5)
                features.speaking_rate = syllable_count / max(0.5, features.duration)
            except:
                features.speaking_rate = 3.0
            
            return features
            
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return None


class EmotionClassifier:
    """情感分类器 - 返回所有情感的概率"""
    
    def __init__(self):
        # 动态调整的权重参数
        self.weights = self._init_weights()
    
    def _init_weights(self):
        return {
            'angry': {'rms': 3.2, 'pitch': 3.2, 'tempo': 2.5, 'zcr': 2.0, 'contrast': 2.0, 'flux': 1.8},
            'fearful': {'pitch': 2.0, 'pitch_std': 2.0, 'zcr': 1.5, 'entropy': 1.5, 'rms': 1.0, 'flux': 1.0},
            'happy': {'tempo': 3.5, 'pitch': 3.2, 'pitch_std': 2.5, 'centroid': 2.5, 'rms': 2.2, 'formant': 2.2},
            'sad': {'rms': 3.5, 'pitch': 3.5, 'tempo': 3.0, 'pitch_std': 2.5, 'centroid': 2.2, 'hnr': 2.0},
            'calm': {'rms': 3.5, 'pitch_std': 3.8, 'tempo': 3.2, 'zcr': 2.5, 'centroid': 2.0, 'hnr': 2.2},
            'surprised': {'pitch': 3.0, 'pitch_std': 3.0, 'tempo': 2.2, 'rms': 2.0, 'flux': 2.2}
        }
    
    def classify(self, features: AudioFeatures) -> Tuple[Emotion, Dict[Emotion, float]]:
        """分类情感 - 返回所有情感的原始分数"""
        scores = {emotion: 0.0 for emotion in Emotion}
        
        # 计算各情感得分
        self._score_angry(features, scores)
        self._score_fearful(features, scores)
        self._score_happy(features, scores)
        self._score_sad(features, scores)
        self._score_calm(features, scores)
        self._score_surprised(features, scores)
        
        # MFCC 特征加分
        self._apply_mfcc_scores(features, scores)
        
        # 共振峰加分
        self._apply_formant_scores(features, scores)
        
        # 选择情感
        emotion = self._select_emotion(scores, features)
        
        return emotion, scores
    
    def _select_emotion(self, scores: Dict[Emotion, float], features: AudioFeatures) -> Emotion:
        """选择最佳情感"""
        if not scores:
            return Emotion.CALM
        
        max_score = max(scores.values())
        
        if max_score < 1.0:
            return Emotion.CALM
        
        # 获取 top 2
        sorted_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_emotions) == 1:
            return sorted_emotions[0][0]
        
        top1, top1_score = sorted_emotions[0]
        top2, top2_score = sorted_emotions[1]
        
        # 消歧逻辑
        if top2_score > top1_score * 0.75:
            # 区分愤怒和恐惧
            if {top1, top2} == {Emotion.ANGRY, Emotion.FEARFUL}:
                return Emotion.ANGRY if features.rms_mean > 0.10 else Emotion.FEARFUL
            
            # 区分开心和惊讶
            if {top1, top2} == {Emotion.HAPPY, Emotion.SURPRISED}:
                return Emotion.SURPRISED if features.pitch_std > 38 else Emotion.HAPPY
            
            # 区分悲伤和平静
            if {top1, top2} == {Emotion.SAD, Emotion.CALM}:
                return Emotion.SAD if features.rms_mean < 0.06 else Emotion.CALM
            
            # 区分恐惧和惊讶
            if {top1, top2} == {Emotion.FEARFUL, Emotion.SURPRISED}:
                return Emotion.SURPRISED if features.pitch_mean > 280 else Emotion.FEARFUL
        
        return top1
    
    def _score_angry(self, f: AudioFeatures, scores: Dict[Emotion, float]):
        score = 0
        w = self.weights['angry']
        
        if f.rms_mean > 0.11: score += w['rms'] * min(1.0, (f.rms_mean - 0.11) / 0.05)
        if f.pitch_mean > 250: score += w['pitch'] * min(1.0, (f.pitch_mean - 250) / 60)
        if f.tempo > 130: score += w['tempo'] * min(1.0, (f.tempo - 130) / 35)
        if f.zcr_mean > 0.12: score += w['zcr'] * min(1.0, (f.zcr_mean - 0.12) / 0.05)
        if f.spectral_contrast_mean > 12: score += w['contrast'] * min(1.0, (f.spectral_contrast_mean - 12) / 6)
        if f.spectral_flux_mean > 0.7: score += w['flux'] * min(1.0, (f.spectral_flux_mean - 0.7) / 0.3)
        
        if f.rms_mean > 0.13 and f.pitch_mean > 270:
            score += 2
        if f.rms_mean > 0.12 and f.tempo > 135:
            score += 1
        
        scores[Emotion.ANGRY] += score
    
    def _score_fearful(self, f: AudioFeatures, scores: Dict[Emotion, float]):
        score = 0
        w = self.weights['fearful']
        
        if f.pitch_mean > 220: score += w['pitch'] * min(1.0, (f.pitch_mean - 220) / 100)
        if f.pitch_std > 35: score += w['pitch_std'] * min(1.0, (f.pitch_std - 35) / 25)
        if f.zcr_mean > 0.10: score += w['zcr'] * min(1.0, (f.zcr_mean - 0.10) / 0.06)
        if f.energy_entropy > 3.5: score += w['entropy'] * min(1.0, (f.energy_entropy - 3.5) / 2.0)
        if f.spectral_flux_mean > 0.5: score += w['flux'] * min(1.0, (f.spectral_flux_mean - 0.5) / 0.4)
        
        if 0.06 < f.rms_mean < 0.11:
            score += w['rms'] * ((f.rms_mean - 0.06) / 0.05)
        
        if f.pitch_std > 40 and 0.07 < f.rms_mean < 0.10:
            score += 2
        if f.pitch_mean > 240 and f.pitch_std > 38:
            score += 1
        
        scores[Emotion.FEARFUL] += score
    
    def _score_happy(self, f: AudioFeatures, scores: Dict[Emotion, float]):
        score = 0
        w = self.weights['happy']
        
        if f.tempo > 100: score += w['tempo'] * min(1.5, (f.tempo - 100) / 50)
        if f.pitch_mean > 200: score += w['pitch'] * min(1.5, (f.pitch_mean - 200) / 80)
        if f.pitch_std > 25: score += w['pitch_std'] * min(1.5, (f.pitch_std - 25) / 35)
        if f.spectral_centroid_mean > 2500: score += w['centroid'] * min(1.5, (f.spectral_centroid_mean - 2500) / 1500)
        if f.rms_mean > 0.08: score += w['rms'] * min(1.5, (f.rms_mean - 0.08) / 0.06)
        
        if f.rms_mean > 0.09 and f.pitch_mean > 220:
            score += 3
        if f.tempo > 115 and f.spectral_centroid_mean > 2800:
            score += 2
        
        if f.formant_f2 > 1800:
            score += w['formant'] * 1.0
        
        scores[Emotion.HAPPY] += score
    
    def _score_sad(self, f: AudioFeatures, scores: Dict[Emotion, float]):
        score = 0
        w = self.weights['sad']
        
        if f.rms_mean < 0.08: score += w['rms'] * min(1.8, (0.08 - f.rms_mean) / 0.06)
        if f.pitch_mean < 195: score += w['pitch'] * min(1.8, (195 - f.pitch_mean) / 95)
        if f.tempo < 100: score += w['tempo'] * min(1.8, (100 - f.tempo) / 50)
        if f.pitch_std < 28: score += w['pitch_std'] * min(1.8, (28 - f.pitch_std) / 25)
        if f.spectral_centroid_mean < 2400: score += w['centroid'] * min(1.8, (2400 - f.spectral_centroid_mean) / 1200)
        if f.zcr_mean < 0.07: score += w['rms'] * 0.8
        
        if f.rms_mean < 0.065 and f.pitch_mean < 185:
            score += 4
        if f.rms_mean < 0.07 and f.tempo < 90:
            score += 3
        if f.pitch_std < 20 and f.rms_mean < 0.07:
            score += 2
        
        if f.hnr_mean < 0.12:
            score += w['hnr'] * min(1.5, (0.12 - f.hnr_mean) / 0.1)
        
        scores[Emotion.SAD] += score
    
    def _score_calm(self, f: AudioFeatures, scores: Dict[Emotion, float]):
        score = 0
        w = self.weights['calm']
        
        if f.rms_mean < 0.07: score += w['rms'] * min(2.0, (0.07 - f.rms_mean) / 0.05)
        if f.pitch_std < 22: score += w['pitch_std'] * min(2.0, (22 - f.pitch_std) / 18)
        if 65 < f.tempo < 110: 
            tempo_score = 1.2 if 75 <= f.tempo <= 105 else 0.8
            score += w['tempo'] * tempo_score
        if f.zcr_mean < 0.06: score += w['zcr'] * min(2.0, (0.06 - f.zcr_mean) / 0.04)
        if f.spectral_centroid_mean < 2200: score += w['centroid'] * min(2.0, (2200 - f.spectral_centroid_mean) / 1000)
        
        if f.pitch_std < 18 and f.rms_std < 0.018:
            score += 4
        if f.pitch_mean > 150 and f.pitch_mean < 230 and f.rms_mean < 0.06:
            score += 3
        if f.tempo > 70 and f.tempo < 105 and f.pitch_std < 20:
            score += 2
        
        if f.hnr_mean > 0.12:
            score += w['hnr'] * min(1.5, (f.hnr_mean - 0.12) / 0.12)
        
        scores[Emotion.CALM] += score
    
    def _score_surprised(self, f: AudioFeatures, scores: Dict[Emotion, float]):
        score = 0
        w = self.weights['surprised']
        
        if f.pitch_mean > 260: score += w['pitch'] * min(1.2, (f.pitch_mean - 260) / 90)
        if f.pitch_std > 35: score += w['pitch_std'] * min(1.2, (f.pitch_std - 35) / 35)
        if f.tempo > 115: score += w['tempo'] * min(1.2, (f.tempo - 115) / 45)
        if f.rms_mean > 0.09: score += w['rms'] * min(1.2, (f.rms_mean - 0.09) / 0.07)
        if f.spectral_flux_mean > 0.5: score += w['flux'] * min(1.2, (f.spectral_flux_mean - 0.5) / 0.5)
        
        if f.spectral_flux_mean > 0.6 and f.pitch_mean > 280:
            score += 2.5
        if f.pitch_std > 40 and f.rms_mean > 0.10:
            score += 1.5
        
        scores[Emotion.SURPRISED] += score
    
    def _apply_mfcc_scores(self, f: AudioFeatures, scores: Dict[Emotion, float]):
        """基于 MFCC 特征调整分数"""
        if len(f.mfcc_means) >= 3:
            mfcc1 = f.mfcc_means[1]
            mfcc2 = f.mfcc_means[2]
            mfcc3 = f.mfcc_means[0] if len(f.mfcc_means) > 0 else 0
            
            if mfcc1 > 4:
                scores[Emotion.ANGRY] += 1.2
            elif mfcc1 < -4:
                scores[Emotion.HAPPY] += 1.5
            
            if mfcc2 < -2:
                scores[Emotion.SAD] += 1.2
            elif mfcc2 > 2:
                scores[Emotion.HAPPY] += 1.2
                scores[Emotion.SURPRISED] += 0.8
            
            if mfcc3 < -10:
                scores[Emotion.FEARFUL] += 1.5
    
    def _apply_formant_scores(self, f: AudioFeatures, scores: Dict[Emotion, float]):
        """基于共振峰特征调整分数"""
        if f.formant_f2 > 1700:
            scores[Emotion.HAPPY] += 1.5
            scores[Emotion.SURPRISED] += 1.2
        elif f.formant_f2 < 1300:
            scores[Emotion.SAD] += 1.5
            scores[Emotion.CALM] += 0.8
        
        if f.formant_f3 - f.formant_f2 > 800:
            scores[Emotion.SURPRISED] += 1


class VADGenerator:
    """VAD 向量生成器"""
    
    def generate(self, emotion: Emotion, features: AudioFeatures) -> Tuple[float, float, float, float]:
        vad_map = {
            Emotion.HAPPY: (0.86, 0.72, 0.62),
            Emotion.SAD: (0.18, 0.32, 0.38),
            Emotion.ANGRY: (0.12, 0.78, 0.67),
            Emotion.FEARFUL: (0.18, 0.86, 0.25),
            Emotion.CALM: (0.52, 0.22, 0.55),
            Emotion.SURPRISED: (0.63, 0.74, 0.48),
            Emotion.ANXIOUS: (0.25, 0.82, 0.35),
            Emotion.DISGUSTED: (0.10, 0.55, 0.42)
        }
        
        valence, arousal, dominance = vad_map.get(emotion, (0.5, 0.5, 0.5))
        
        intensity = (min(1.0, features.rms_mean * 8) + 
                    min(1.0, (features.pitch_mean - 100) / 300) + 
                    min(1.0, features.tempo / 180)) / 3
        
        confidence = max(0.4, min(0.95, intensity))
        
        return valence, arousal, dominance, confidence


class VoiceEmotionAnalyzer:
    """语音情感分析器主类 - 支持多情感概率输出"""
    
    def __init__(self):
        self.extractor = FeatureExtractor()
        self.classifier = EmotionClassifier()
        self.vad_generator = VADGenerator()
    
    def analyze(self, audio_path: str) -> VoiceEmotionResult:
        """分析语音情感，返回包含多情感概率的结果"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        try:
            features = self.extractor.extract(audio_path)
            
            if features is None:
                return self._get_default_result()
            
            # 获取原始分数
            emotion, raw_scores = self.classifier.classify(features)
            
            # 转换为百分比（Softmax风格）
            percentages, top_emotions = self._calculate_percentages(raw_scores)
            
            # 生成VAD值
            valence, arousal, dominance, confidence = self.vad_generator.generate(emotion, features)
            
            # 构建情感名称到分数的映射
            all_scores = {e.value: s for e, s in raw_scores.items()}
            
            return VoiceEmotionResult(
                emotion=emotion,
                valence=valence,
                arousal=arousal,
                dominance=dominance,
                confidence=confidence,
                all_emotion_scores=all_scores,
                all_emotion_percentages=percentages,
                top_emotions=top_emotions
            )
            
        except Exception as e:
            logger.error(f"音频分析失败: {e}")
            return self._get_default_result()
    
    def _calculate_percentages(self, scores: Dict[Emotion, float]) -> Tuple[Dict[str, float], List[Tuple[str, float]]]:
        """将原始分数转换为百分比（使用指数归一化）"""
        # 获取非负分数
        positive_scores = {e: max(0, s) for e, s in scores.items()}
        
        # 计算总分
        total = sum(positive_scores.values())
        
        if total > 0:
            # 计算百分比
            percentages = {e.value: (s / total) * 100 for e, s in positive_scores.items()}
        else:
            # 所有分数都为0，均匀分布
            equal_prob = 100.0 / len(scores)
            percentages = {e.value: equal_prob for e in scores}
        
        # 按百分比排序，获取前3
        sorted_emotions = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
        top_emotions = sorted_emotions[:3]
        
        return percentages, top_emotions
    
    def analyze_with_details(self, audio_path: str) -> Tuple[VoiceEmotionResult, Dict[str, float]]:
        """分析语音情感，返回结果和原始分数"""
        result = self.analyze(audio_path)
        return result, result.all_emotion_scores
    
    def _get_default_result(self) -> VoiceEmotionResult:
        default_percentages = {e.value: 0.0 for e in Emotion}
        default_percentages["平静"] = 100.0
        return VoiceEmotionResult(
            emotion=Emotion.CALM,
            valence=0.52,
            arousal=0.22,
            dominance=0.55,
            confidence=0.5,
            all_emotion_scores={e.value: 0.0 for e in Emotion},
            all_emotion_percentages=default_percentages,
            top_emotions=[("平静", 100.0)]
        )


# 便捷函数
_analyzer = VoiceEmotionAnalyzer()


def analyze_voice(audio_path: str) -> VoiceEmotionResult:
    """分析语音情感，返回完整结果（包含多情感概率）"""
    return _analyzer.analyze(audio_path)


def analyze_voice_simple(audio_path: str) -> str:
    """简化版：只返回主要情感名称"""
    result = _analyzer.analyze(audio_path)
    return result.emotion_name


def analyze_voice_with_probs(audio_path: str) -> Tuple[str, Dict[str, float]]:
    """分析语音情感，返回主要情感和所有情感百分比"""
    result = _analyzer.analyze(audio_path)
    return result.emotion_name, result.all_emotion_percentages


def analyze_voice_top_k(audio_path: str, k: int = 3) -> List[Tuple[str, float]]:
    """分析语音情感，返回前k个情感及其百分比"""
    result = _analyzer.analyze(audio_path)
    return result.get_top_k(k)


__all__ = [
    'VoiceEmotionResult', 'VoiceEmotionAnalyzer', 'analyze_voice',
    'analyze_voice_simple', 'analyze_voice_with_probs', 'analyze_voice_top_k',
    'Emotion'
]