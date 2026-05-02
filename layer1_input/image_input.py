"""
Layer1 — 图片输入处理（数字分身头像）
负责人：组员A

TODO(组员A):
- [ ] 图片格式验证
- [ ] 图片预处理（裁剪、缩放）
- [ ] 人脸检测（可选）
"""


class ImageInputProcessor:
    """图片输入预处理器"""

    def validate_file(self, filepath):
        """TODO(组员A): 验证图片文件"""
        raise NotImplementedError

    def preprocess(self, filepath):
        """TODO(组员A): 图片预处理"""
        raise NotImplementedError
