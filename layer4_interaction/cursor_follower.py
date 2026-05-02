"""
Layer4 — 鼠标视线跟随
负责人：组员E

TODO(组员E):
- [ ] 实现 Eye-Follow-Cursor 效果
- [ ] 数字分身眼球跟随鼠标移动
- [ ] 支持平滑动画
"""


def update_eye_position(cursor_x, cursor_y, avatar_bounds):
    """
    TODO(组员E): 计算眼球朝向

    Args:
        cursor_x, cursor_y: 鼠标位置
        avatar_bounds: 数字分身的边界框

    Returns:
        {"eye_x": offset, "eye_y": offset}
    """
    raise NotImplementedError("TODO(组员E): 实现视线跟随逻辑")
