"""
Layer4 — 数字分身展示
负责人：组员E

TODO(组员E):
- [ ] 数字分身渲染
- [ ] 表情动画驱动
- [ ] 头像加载与切换
"""


class AvatarDisplay:
    """数字分身管理器"""

    def load_avatar(self, image_path):
        """TODO(组员E): 加载数字分身头像"""
        raise NotImplementedError

    def update_expression(self, emotion):
        """TODO(组员E): 根据情绪更新表情"""
        raise NotImplementedError
