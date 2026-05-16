from __future__ import annotations

import ctypes
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QAction, QMouseEvent, QCursor, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from backend.desktop_pet.components import ChatDialog, GifPanel


def _apply_dwm_hacks(w: QWidget) -> None:
    """Suppress the 1px grey border on Windows frameless translucent windows."""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(w.winId())
    except (TypeError, ValueError, AttributeError):
        return
    if hwnd == 0:
        return
    try:
        dwm = ctypes.windll.dwmapi
    except OSError:
        return
    from ctypes import wintypes

    h = wintypes.HWND(hwnd)
    p_nc = wintypes.DWORD(1)
    p_imm = wintypes.BOOL(1)
    DWMWA_COLOR_NONE = 0xFFFFFFFE

    attrs = [
        (2, p_nc),
        (20, p_imm),
        (34, wintypes.DWORD(DWMWA_COLOR_NONE)),
    ]
    for attr, ref in attrs:
        try:
            dwm.DwmSetWindowAttribute(h, attr, ctypes.byref(ref), ctypes.sizeof(ref))
        except (OSError, ValueError, ctypes.ArgumentError):
            pass


class DesktopAvatarWindow(QWidget):
    """Floating desktop pet window with multi-emotion GIF display.

    Ported from Rachel/Shinsekai ChatUIWindow - supports:
    - Frameless translucent always-on-top window
    - Multi-sprite (multi-GIF) display panel with cross-fade transitions
    - Toolbar (minimize, close, settings menu)
    - Window resize with corner grips
    - Drag-to-move
    - Context menu
    - HTTP polling for emotion GIF updates from the FastAPI backend
    """

    def __init__(
        self,
        api_base: str,
        poll_interval: float = 2.5,
        max_slots: int = 6,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._api_base = api_base.rstrip("/")
        self._poll_ms = int(max(1.0, poll_interval) * 1000)
        self._drag_pos: Optional[QPoint] = None
        self._known_emotions: dict[str, str] = {}  # emotion_key -> etag
        self._gif_temp_files: dict[str, str] = {}  # emotion_key -> temp file path

        # Resize state (from Rachel)
        self._resizing = False
        self._resize_mask = Qt.Edge(0)
        self._resize_start_global = QPoint()
        self._resize_start_geom = QRect()
        self._resize_margin = 8
        self._window_corner_grip_px = 28

        self._setup_window()
        self._setup_ui()
        self._setup_resize_grips()

        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        x = avail.left() + (avail.width() - self.width()) // 2
        y = avail.top() + (avail.height() - self.height()) // 2
        self.move(x, y)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(self._poll_ms)
        self._poll()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
            | Qt.WindowType.NoDropShadowWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("EmotionMirrorDesktopPet")
        self.setStyleSheet(
            "#EmotionMirrorDesktopPet { background: transparent; border: none; }"
        )
        self.setMinimumSize(200, 180)
        self.resize(640, 620)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not getattr(self, "_dwm_applied", False):
            self._dwm_applied = True
            _apply_dwm_hacks(self)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # GIF panel (single-slot with navigation)
        self._gif_panel = GifPanel(
            panel_width=self.width(),
            panel_height=self.height() - 48,
            parent=self,
        )
        self._gif_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._gif_panel, 1)

        # Speech bubble overlay on the GIF panel
        self._speech_bubble = QLabel(self._gif_panel)
        self._speech_bubble.setWordWrap(True)
        self._speech_bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._speech_bubble.setStyleSheet(
            "background: rgba(30,30,40,200);"
            "color: white;"
            "border-radius: 12px;"
            "padding: 10px 16px;"
            "font-size: 13px;"
        )
        self._speech_bubble.setMaximumWidth(320)
        self._speech_bubble.adjustSize()
        self._speech_bubble.hide()
        self._speech_timer = QTimer(self)
        self._speech_timer.setSingleShot(True)
        self._speech_timer.timeout.connect(self._speech_bubble.hide)

        # Chat dialog
        self._chat = ChatDialog(api_base=self._api_base, parent=self)
        self._chat.on_chat_response = self._on_chat_response
        layout.addWidget(self._chat)

        # Emotion status bar at bottom
        self._status_label = QLabel("连接中…")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(
            "color: rgba(255,255,255,180);"
            "background: rgba(0,0,0,80);"
            "padding: 4px 12px;"
            "border-radius: 6px;"
            "font-size: 11px;"
        )
        self._status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        layout.addWidget(self._status_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Toolbar (ported from Rachel DesktopToolbarMixin)
        self._setup_toolbar()

        # Load soyo's static photo initially
        self._load_soyo_photo()

    def _setup_toolbar(self) -> None:
        self._toolbar = QWidget(self)
        self._toolbar.setStyleSheet(
            "background: transparent; border: none;"
        )
        tb_layout = QHBoxLayout(self._toolbar)
        tb_layout.setContentsMargins(0, 6, 12, 0)
        tb_layout.setSpacing(4)
        tb_layout.addStretch(1)

        btn_style = (
            "QPushButton {"
            "  background: rgba(0,0,0,80);"
            "  color: rgba(255,255,255,200);"
            "  border: none;"
            "  border-radius: 14px;"
            "  font-size: 16px;"
            "  padding: 0;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(0,0,0,140);"
            "  color: white;"
            "}"
        )

        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setFixedSize(28, 28)
        self._settings_btn.setStyleSheet(btn_style)
        self._settings_btn.clicked.connect(self._show_settings_menu)

        self._minimize_btn = QPushButton("－")
        self._minimize_btn.setFixedSize(28, 28)
        self._minimize_btn.setStyleSheet(btn_style)
        self._minimize_btn.clicked.connect(self.showMinimized)

        self._close_btn = QPushButton("×")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.setStyleSheet(btn_style)
        self._close_btn.clicked.connect(self.close)

        tb_layout.addWidget(self._settings_btn)
        tb_layout.addWidget(self._minimize_btn)
        tb_layout.addWidget(self._close_btn)

        self._layout_toolbar()

    def _layout_toolbar(self) -> None:
        tb_w = 28 * 3 + 12 + 4 * 2
        self._toolbar.setFixedSize(tb_w, 34)
        self._toolbar.move(self.width() - tb_w - 4, 4)

    # ------------------------------------------------------------------
    # Soyo initial photo & chat response
    # ------------------------------------------------------------------

    def _load_soyo_photo(self) -> None:
        soyo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "soyo.jpg")
        if os.path.isfile(soyo_path):
            pixmap = QPixmap(soyo_path)
            if not pixmap.isNull():
                self._gif_panel._slot.show_static_pixmap(pixmap)
                self._status_label.setText("Soyo 已上线 · 在对话框中聊天吧")

    def _on_chat_response(self, result: dict) -> None:
        emotion = result.get("emotion", "")
        reply = result.get("reply", "")
        gif_published = result.get("gif_published", False)

        # Show speech bubble overlay on the GIF panel
        self._speech_bubble.setText(reply)
        self._speech_bubble.adjustSize()
        self._layout_speech_bubble()
        self._speech_bubble.show()
        self._speech_timer.start(6000)

        if gif_published:
            self._status_label.setText(f"Soyo · {emotion} 😊")
            self._poll()
        else:
            self._status_label.setText(f"Soyo · {emotion}")

    def _layout_speech_bubble(self) -> None:
        pw = self._gif_panel.width()
        bw = min(self._speech_bubble.width(), 320)
        x = (pw - bw) // 2
        self._speech_bubble.move(x, 12)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_toolbar()
        self._layout_resize_grips()
        self._layout_speech_bubble()

    # ------------------------------------------------------------------
    # Resize corner grips (ported from Rachel)
    # ------------------------------------------------------------------

    def _setup_resize_grips(self) -> None:
        self._resize_grip_bl = QWidget(self)
        self._resize_grip_br = QWidget(self)
        self._resize_grip_bl.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        self._resize_grip_br.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        for gw in (self._resize_grip_bl, self._resize_grip_br):
            gw.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            gw.setStyleSheet("background: rgba(255,255,255,20); border: none;")
            gw.setMouseTracking(True)
        self._layout_resize_grips()

    def _layout_resize_grips(self) -> None:
        if not hasattr(self, "_resize_grip_bl"):
            return
        g = self._window_corner_grip_px
        w, h = max(1, self.width()), max(1, self.height())
        self._resize_grip_bl.setGeometry(0, max(0, h - g), g, g)
        self._resize_grip_br.setGeometry(max(0, w - g), max(0, h - g), g, g)
        self._resize_grip_bl.raise_()
        self._resize_grip_br.raise_()

    def _edges_at(self, pos: QPoint) -> Qt.Edge:
        m = self._resize_margin
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return Qt.Edge(0)
        edges = Qt.Edge(0)
        if pos.x() <= m:
            edges |= Qt.Edge.LeftEdge
        if pos.x() >= w - m:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= m:
            edges |= Qt.Edge.TopEdge
        if pos.y() >= h - m:
            edges |= Qt.Edge.BottomEdge
        return edges

    def _cursor_for_edges(self, edges: Qt.Edge) -> QCursor:
        le, ri = Qt.Edge.LeftEdge, Qt.Edge.RightEdge
        tp, bt = Qt.Edge.TopEdge, Qt.Edge.BottomEdge
        if edges in (le | tp, ri | bt):
            return QCursor(Qt.CursorShape.SizeFDiagCursor)
        if edges in (ri | tp, le | bt):
            return QCursor(Qt.CursorShape.SizeBDiagCursor)
        if edges & (le | ri):
            return QCursor(Qt.CursorShape.SizeHorCursor)
        if edges & (tp | bt):
            return QCursor(Qt.CursorShape.SizeVerCursor)
        return QCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            lp = event.position().toPoint()
            edges = self._edges_at(lp)
            if edges != Qt.Edge(0):
                self._begin_resize(edges, event.globalPosition().toPoint())
                return
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._resizing and event.buttons() == Qt.MouseButton.LeftButton:
            self._apply_resize_step(event.globalPosition().toPoint())
            return
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        else:
            lp = event.position().toPoint()
            edges = self._edges_at(lp)
            if edges != Qt.Edge(0):
                self.setCursor(self._cursor_for_edges(edges))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._resizing:
            self._end_resize()
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Right:
            self._gif_panel.navigate_next()
        elif event.key() == Qt.Key.Key_Left:
            self._gif_panel.navigate_prev()
        super().keyPressEvent(event)

    def _begin_resize(self, edges: Qt.Edge, global_pos: QPoint) -> None:
        self._resizing = True
        self._resize_mask = edges
        self._resize_start_global = QPoint(global_pos)
        self._resize_start_geom = QRect(self.geometry())
        self._drag_pos = None
        self.grabMouse()

    def _end_resize(self) -> None:
        self._resizing = False
        self._resize_mask = Qt.Edge(0)
        if QWidget.mouseGrabber() is self:
            self.releaseMouse()
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def _apply_resize_step(self, global_pos: QPoint) -> None:
        dg = global_pos - self._resize_start_global
        g = QRect(self._resize_start_geom)
        min_w = max(1, self.minimumWidth())
        min_h = max(1, self.minimumHeight())
        e = self._resize_mask
        if e & Qt.Edge.LeftEdge:
            new_w = g.width() - dg.x()
            if new_w >= min_w:
                g.setLeft(g.left() + dg.x())
                g.setWidth(new_w)
        if e & Qt.Edge.RightEdge:
            g.setWidth(max(min_w, g.width() + dg.x()))
        if e & Qt.Edge.TopEdge:
            new_h = g.height() - dg.y()
            if new_h >= min_h:
                g.setTop(g.top() + dg.y())
                g.setHeight(new_h)
        if e & Qt.Edge.BottomEdge:
            g.setHeight(max(min_h, g.height() + dg.y()))
        self.setGeometry(g)

    # ------------------------------------------------------------------
    # Context menu (ported from Rachel DesktopMenuMixin)
    # ------------------------------------------------------------------

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu {"
            "  background: rgba(30,30,30,220);"
            "  color: white;"
            "  border: 1px solid rgba(255,255,255,30);"
            "  border-radius: 4px;"
            "  padding: 2px;"
            "}"
            "QMenu::item {"
            "  padding: 3px 14px;"
            "  border-radius: 3px;"
            "  font-size: 11px;"
            "}"
            "QMenu::item:selected {"
            "  background: rgba(76,175,80,160);"
            "}"
            "QMenu::separator {"
            "  height: 1px;"
            "  background: rgba(255,255,255,25);"
            "  margin: 2px 6px;"
            "}"
        )

        pin_action = QAction("置顶显示", self)
        pin_action.setCheckable(True)
        pin_action.setChecked(bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        pin_action.triggered.connect(self._toggle_pin_top)

        refresh_action = QAction("刷新表情", self)
        refresh_action.triggered.connect(self._poll)

        clear_action = QAction("清除所有表情", self)
        clear_action.triggered.connect(self._clear_all)

        menu.addAction(pin_action)
        menu.addAction(refresh_action)
        menu.addSeparator()
        menu.addAction(clear_action)
        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

        menu.exec(event.globalPos())

    def _toggle_pin_top(self, checked: bool) -> None:
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    # ------------------------------------------------------------------
    # Settings menu (from toolbar)
    # ------------------------------------------------------------------

    def _show_settings_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu {"
            "  background: rgba(30,30,30,220);"
            "  color: white;"
            "  border: 1px solid rgba(255,255,255,30);"
            "  border-radius: 4px;"
            "  padding: 2px;"
            "}"
            "QMenu::item {"
            "  padding: 3px 14px;"
            "  border-radius: 3px;"
            "  font-size: 11px;"
            "}"
            "QMenu::item:selected {"
            "  background: rgba(76,175,80,160);"
            "}"
            "QMenu::separator {"
            "  height: 1px;"
            "  background: rgba(255,255,255,25);"
            "  margin: 2px 6px;"
            "}"
        )

        pin_action = QAction("置顶显示", self)
        pin_action.setCheckable(True)
        pin_action.setChecked(bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        pin_action.triggered.connect(self._toggle_pin_top)

        refresh_action = QAction("刷新表情", self)
        refresh_action.triggered.connect(self._poll)

        clear_action = QAction("清除所有表情", self)
        clear_action.triggered.connect(self._clear_all)

        # Emotion selection submenu
        emotion_keys = self._gif_panel.emotion_keys()
        current_key = self._gif_panel.current_key()
        if emotion_keys:
            menu.addSeparator()
            emotion_menu = menu.addMenu("切换表情")
            for k in emotion_keys:
                label = next(
                    (e["label"] for e in self._gif_panel._entries if e["key"] == k),
                    k
                )
                act = QAction(label, self)
                act.setCheckable(True)
                act.setChecked(k == current_key)
                act.triggered.connect(lambda checked, key=k: self._gif_panel.select_by_key(key))
                emotion_menu.addAction(act)

        about_action = QAction(f"EmotionMirror 桌宠 v0.1.0", self)
        about_action.setEnabled(False)

        menu.addAction(pin_action)
        menu.addAction(refresh_action)
        menu.addSeparator()
        menu.addAction(clear_action)
        menu.addSeparator()
        menu.addAction(about_action)

        menu.exec(
            self._settings_btn.mapToGlobal(
                self._settings_btn.rect().bottomLeft()
            )
        )

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _fetch_json(self, url: str) -> Optional[dict]:
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
            return None

    def _fetch_gif(self, url: str) -> Optional[bytes]:
        try:
            req = urllib.request.Request(url, headers={"Accept": "image/gif"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            return None

    def _save_temp_gif(self, raw: bytes) -> Optional[str]:
        if len(raw) < 64:
            return None
        fd, tmp = tempfile.mkstemp(suffix=".gif")
        try:
            os.write(fd, raw)
        finally:
            os.close(fd)
        return tmp

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def _poll(self) -> None:
        data = self._fetch_json(f"{self._api_base}/api/desktop/emotions")
        if not data or "emotions" not in data:
            self._status_label.setText("无法连接后端")
            return

        emotions = data["emotions"]
        if not emotions:
            self._status_label.setText("暂无表情数据")
            self._gif_panel.clear_all()
            self._known_emotions.clear()
            return

        self._status_label.setText(f"已加载 {len(emotions)} 个表情")
        current_keys = set()

        for entry in emotions:
            key = entry.get("key", "")
            label = entry.get("emotion", key)
            etag = entry.get("etag", "")
            current_keys.add(key)

            # Check if already up-to-date
            if key in self._known_emotions and self._known_emotions[key] == etag:
                continue

            # Download GIF
            gif_url = f"{self._api_base}/api/desktop/widget.gif?emotion={urllib.parse.quote(key)}&t={etag}"
            raw = self._fetch_gif(gif_url)
            if raw is None or len(raw) < 64:
                continue

            tmp_path = self._save_temp_gif(raw)
            if tmp_path is None:
                continue

            # Clean up old temp file
            if key in self._gif_temp_files:
                old = self._gif_temp_files[key]
                if os.path.isfile(old):
                    try:
                        os.unlink(old)
                    except OSError:
                        pass

            self._gif_temp_files[key] = tmp_path
            self._known_emotions[key] = etag

            # Update the panel slot
            self._gif_panel.update_slot(key, tmp_path, label, etag)

        # Remove stale emotions
        stale = set(self._known_emotions.keys()) - current_keys
        for key in stale:
            self._gif_panel.remove_slot(key)
            if key in self._gif_temp_files:
                old = self._gif_temp_files.pop(key, None)
                if old and os.path.isfile(old):
                    try:
                        os.unlink(old)
                    except OSError:
                        pass
            self._known_emotions.pop(key, None)

    def _clear_all(self) -> None:
        """Clear all emotion GIFs from the backend and reset the display."""
        try:
            req = urllib.request.Request(
                f"{self._api_base}/api/desktop/clear",
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            pass
        self._gif_panel.clear_all()
        self._known_emotions.clear()
        for path in self._gif_temp_files.values():
            if os.path.isfile(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass
        self._gif_temp_files.clear()
        self._status_label.setText("已清除")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        for path in self._gif_temp_files.values():
            if os.path.isfile(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass
        self._gif_temp_files.clear()
        super().closeEvent(event)
