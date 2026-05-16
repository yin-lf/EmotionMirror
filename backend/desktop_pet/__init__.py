"""Desktop floating avatar (PySide6). Supports multi-emotion GIF display.

Run:
    python -m backend.desktop_pet --api http://127.0.0.1:8000

Ports the frameless transparent window with toolbar, resize, and multi-sprite
display from Rachel/Shinsekai ChatUIWindow.
"""

from backend.desktop_pet.window import DesktopAvatarWindow
from backend.desktop_pet.components import CrossFadeGifSlot, GifPanel

__all__ = ["DesktopAvatarWindow", "CrossFadeGifSlot", "GifPanel"]
