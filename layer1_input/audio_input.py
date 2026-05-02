"""
Layer1 — 音频输入处理
负责人：组员A

TODO(组员A):
- [ ] 音频格式验证
- [ ] 音频特征提取（MFCC、频谱等）
- [ ] 音频预处理（降噪、归一化等）
"""


class AudioInputProcessor:
    """音频输入预处理器"""

    def validate_file(self, filepath):
        """TODO(组员A): 验证音频文件格式"""
        raise NotImplementedError

    def preprocess(self, filepath):
        """TODO(组员A): 音频预处理，返回特征"""
        raise NotImplementedError
