"""
Layer1 — 文本输入处理
负责人：组员A

TODO(组员A):
- [ ] 文本清洗与预处理
- [ ] 文本长度限制
- [ ] 输入验证
"""


class TextInputProcessor:
    """文本输入预处理器"""

    def preprocess(self, text):
        """TODO(组员A): 实现文本预处理，返回清洗后的文本"""
        raise NotImplementedError

    def validate(self, text):
        """TODO(组员A): 实现文本验证"""
        raise NotImplementedError
