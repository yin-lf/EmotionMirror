"""
语音情感分析示例脚本

【功能说明】
此脚本演示如何使用 voice_emotion.py 模块对音频文件进行情感分析。

【输入】
- 音频文件路径: WAV 格式的音频文件
- 示例文件: ./sample.wav (相对于脚本所在目录)

【输出】
- VoiceEmotionResult 对象，包含：
  - emotion: 主要情感标签（枚举类型）
  - emotion_name: 情感名称（字符串）
  - valence: 效价 (0-1)
  - arousal: 唤醒度 (0-1)
  - dominance: 支配度 (0-1)
  - vector: VAD 向量 [valence, arousal, dominance]
  - confidence: 置信度
  - all_emotion_scores: 所有情感的原始分数
  - all_emotion_percentages: 所有情感的百分比
  - top_emotions: 前3个情感及其百分比
"""

import os
import sys

# 添加当前目录到路径，确保能正确导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入 voice_emotion.py 中的所有函数
# 
# 函数说明:
#   analyze_voice(audio_path)          - 获取完整分析结果，返回 VoiceEmotionResult 对象
#   analyze_voice_simple(audio_path)   - 仅获取主要情感名称，返回 str
#   analyze_voice_with_probs(audio_path) - 获取情感名称和所有情感百分比，返回 Tuple[str, Dict]
#   analyze_voice_top_k(audio_path, k)  - 获取前k个情感及其百分比，返回 List[Tuple]
#   VoiceEmotionResult                  - 分析结果数据类
#   Emotion                             - 情感枚举类型（开心、悲伤、愤怒、焦虑、恐惧、平静、厌恶、惊讶）
from voice_emotion import (
    analyze_voice,
    analyze_voice_simple,
    analyze_voice_with_probs,
    analyze_voice_top_k,
    VoiceEmotionResult,
    Emotion
)


if __name__ == "__main__":
    """
    主程序入口
    
    运行此脚本将对示例音频文件进行情感分析，并展示所有可用方法的使用方式。
    
    执行命令:
    python voice_emo_example.py
    
    前提条件:
    1. 确保 voice_emotion.py 位于同一目录
    2. 确保 speech_emotion_recognition_predict 模型文件夹存在于 backend/ 目录下
    3. 确保 sample.wav 音频文件存在于当前目录
    """
    
    # 定义示例音频文件路径（相对路径）
    sample_audio_path = "sample.wav"
    
    print("=" * 60)
    print("语音情感分析示例程序")
    print("=" * 60)
    print(f"分析文件: {sample_audio_path}")
    print(f"完整路径: {os.path.abspath(sample_audio_path)}")
    print("-" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(sample_audio_path):
        print(f"错误: 示例音频文件不存在 - {sample_audio_path}")
        print(f"当前工作目录: {os.getcwd()}")
        print("请将音频文件命名为 sample.wav 并放置在当前目录下")
        sys.exit(1)
    
    try:
        # 【方法1】analyze_voice - 获取完整分析结果
        print("\n【方法1】analyze_voice - 获取完整分析结果")
        print("-" * 40)
        result = analyze_voice(sample_audio_path)
        print(f"主要情感: {result.emotion_name}")
        print(f"情感枚举: {result.emotion}")
        print(f"\nVAD 向量:")
        print(f"  Valence (效价): {result.valence:.3f}")
        print(f"  Arousal (唤醒度): {result.arousal:.3f}")
        print(f"  Dominance (支配度): {result.dominance:.3f}")
        print(f"  向量形式: {result.vector}")
        print(f"\n置信度: {result.confidence:.2%}")
        print(f"\n所有情感百分比:")
        for emotion_name, percentage in sorted(result.all_emotion_percentages.items(), key=lambda x: x[1], reverse=True):
            print(f"  {emotion_name}: {percentage:.2f}%")
        print(f"\n前3个情感:")
        for emotion_name, percentage in result.get_top_k(3):
            print(f"  {emotion_name}: {percentage:.2f}%")
        
        # 【方法2】analyze_voice_simple - 仅获取情感名称
        print("\n【方法2】analyze_voice_simple - 仅获取情感名称")
        print("-" * 40)
        emotion_name = analyze_voice_simple(sample_audio_path)
        print(f"情感名称: {emotion_name}")
        
        # 【方法3】analyze_voice_with_probs - 获取情感名称和百分比
        print("\n【方法3】analyze_voice_with_probs - 获取情感名称和百分比")
        print("-" * 40)
        emotion_name, probabilities = analyze_voice_with_probs(sample_audio_path)
        print(f"情感名称: {emotion_name}")
        print("各情感概率:")
        for name, prob in probabilities.items():
            print(f"  {name}: {prob:.2f}%")
        
        # 【方法4】analyze_voice_top_k - 获取前k个情感
        print("\n【方法4】analyze_voice_top_k - 获取前3个情感")
        print("-" * 40)
        top_emotions = analyze_voice_top_k(sample_audio_path, k=3)
        for i, (emotion_name, percentage) in enumerate(top_emotions, 1):
            print(f"  {i}. {emotion_name}: {percentage:.2f}%")
        
        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)
        
    except RuntimeError as e:
        print(f"\n警告: {e}")
        print("将使用本地特征分析方法进行演示")
        
        # 如果 LSTM 模型不可用，尝试使用本地分析方法
        try:
            from voice_emotion_local import analyze_voice as local_analyze_voice
            
            print("\n【本地分析方法】使用 librosa 特征分析")
            print("-" * 40)
            result = local_analyze_voice(sample_audio_path)
            print(f"主要情感: {result.emotion_name}")
            print(f"VAD 向量: {result.vector}")
            print(f"置信度: {result.confidence:.2%}")
        except ImportError:
            print("错误: 无法导入本地分析模块")
        except Exception as e:
            print(f"本地分析也失败: {e}")
