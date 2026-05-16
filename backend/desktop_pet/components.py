from __future__ import annotations

import json
import threading
import urllib.parse
import urllib.request
from typing import Optional

from PySide6.QtCore import QObject, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QImageReader, QMovie, QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)


class CrossFadeGifSlot(QWidget):
    """Single emotion GIF display slot with cross-fade transition support.

    Uses two stacked QLabels to cross-fade between old and new animated GIFs
    when the emotion expression changes.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(1, 1)

        self._current_movie: Optional[QMovie] = None
        self.emotion_name: str = ""
        self.current_etag: Optional[str] = None
        self._max_gif_w: int = 700
        self._max_gif_h: int = 700

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # --- GIF display area with two overlapping labels for cross-fade ---
        # Uses QGridLayout so both labels occupy the same cell and overlap
        self._gif_container = QWidget(self)
        gif_layout = QGridLayout(self._gif_container)
        gif_layout.setContentsMargins(0, 0, 0, 0)
        gif_layout.setSpacing(0)

        self._old_label = QLabel(self._gif_container)
        self._old_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._old_label.setScaledContents(True)
        self._old_opacity = QGraphicsOpacityEffect(self._old_label)
        self._old_opacity.setOpacity(1.0)
        self._old_label.setGraphicsEffect(self._old_opacity)

        self._new_label = QLabel(self._gif_container)
        self._new_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._new_label.setScaledContents(True)
        self._new_opacity = QGraphicsOpacityEffect(self._new_label)
        self._new_opacity.setOpacity(0.0)
        self._new_label.setGraphicsEffect(self._new_opacity)

        gif_layout.addWidget(self._old_label, 0, 0)
        gif_layout.addWidget(self._new_label, 0, 0)

        layout.addWidget(self._gif_container)

        # --- Emotion label below GIF ---
        self._emotion_label = QLabel("")
        self._emotion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._emotion_label.setStyleSheet(
            "color: rgba(255,255,255,200);"
            "background: rgba(0,0,0,100);"
            "padding: 2px 8px;"
            "border-radius: 4px;"
            "font-size: 12px;"
        )
        self._emotion_label.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        layout.addWidget(self._emotion_label, 0, Qt.AlignmentFlag.AlignCenter)

        self._placeholder_label = QLabel("")
        self._placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder_label.setStyleSheet(
            "color: rgba(255,255,255,60); font-size: 11px;"
        )
        layout.addWidget(self._placeholder_label, 0, Qt.AlignmentFlag.AlignCenter)

    def set_gif(self, gif_path: str, emotion: str, etag: str) -> None:
        """Replace the displayed GIF with a cross-fade transition."""
        self.emotion_name = emotion
        self.current_etag = etag
        self._emotion_label.setText(emotion if emotion else " ")
        self._placeholder_label.setText("")

        # Capture current frame of old movie as static pixmap for fade-out
        if self._current_movie is not None:
            frame = self._current_movie.currentPixmap()
            if frame and not frame.isNull():
                self._old_label.setPixmap(frame)
            self._old_label.setMovie(None)
            self._old_opacity.setOpacity(1.0)
            self._current_movie.stop()
            self._current_movie.deleteLater()
            self._current_movie = None
        else:
            self._old_label.setPixmap(QPixmap())
            self._old_opacity.setOpacity(1.0)

        # Set up new movie on the new label
        new_movie = QMovie(gif_path)
        if not new_movie.isValid():
            self._new_label.clear()
            self._new_label.setMovie(None)
            self._placeholder_label.setText("无效 GIF")
            self._new_opacity.setOpacity(0.0)
            return

        # Size labels to fit GIF within max bounds while preserving aspect ratio
        reader = QImageReader(gif_path)
        src_size = reader.size()
        reader = None
        if src_size.isValid() and src_size.width() > 0 and src_size.height() > 0:
            scaled = src_size.scaled(self._max_gif_w, self._max_gif_h, Qt.KeepAspectRatio)
            self._old_label.setFixedSize(scaled)
            self._new_label.setFixedSize(scaled)

        self._current_movie = new_movie
        self._new_label.setMovie(new_movie)
        self._new_label.setStyleSheet("background: transparent;")
        self._new_opacity.setOpacity(0.0)
        self._new_label.show()
        new_movie.start()

        # Cross-fade animation
        self._fade_out = QPropertyAnimation(self._old_opacity, b"opacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)

        self._fade_in = QPropertyAnimation(self._new_opacity, b"opacity")
        self._fade_in.setDuration(250)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)

        self._fade_out.finished.connect(self._on_fade_out_done)
        self._fade_out.start()
        self._fade_in.start()

    def _on_fade_out_done(self) -> None:
        self._old_label.clear()
        self._old_label.setMovie(None)
        self._old_opacity.setOpacity(1.0)

    def clear(self) -> None:
        """Clear the slot and show placeholder."""
        if self._current_movie is not None:
            self._current_movie.stop()
            self._current_movie.deleteLater()
            self._current_movie = None
        self._old_label.clear()
        self._old_label.setMovie(None)
        self._new_label.clear()
        self._new_label.setMovie(None)
        self._new_opacity.setOpacity(0.0)
        self._old_opacity.setOpacity(1.0)
        self._emotion_label.setText("")
        self._placeholder_label.setText("等待中…")
        self.emotion_name = ""
        self.current_etag = None

    def show_static_pixmap(self, pixmap: QPixmap) -> None:
        """Display a static photo (used for initial soyo photo before GIFs arrive)."""
        if self._current_movie is not None:
            self._current_movie.stop()
            self._current_movie.deleteLater()
            self._current_movie = None
        scaled = pixmap.scaled(self._max_gif_w, self._max_gif_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._old_label.setFixedSize(scaled.size())
        self._new_label.setFixedSize(scaled.size())
        self._old_label.setPixmap(scaled)
        self._old_label.setMovie(None)
        self._new_label.clear()
        self._new_label.setMovie(None)
        self._new_opacity.setOpacity(0.0)
        self._old_opacity.setOpacity(1.0)
        self._emotion_label.setText("Soyo")

    def show_placeholder_text(self, text: str) -> None:
        self._placeholder_label.setText(text)

    def set_fixed_gif_size(self, w: int, h: int) -> None:
        self._max_gif_w = w
        self._max_gif_h = h
        self._refit_labels()

    def _refit_labels(self) -> None:
        if self._current_movie is None or not self._current_movie.isValid():
            return
        path = self._current_movie.fileName()
        if not path:
            return
        reader = QImageReader(path)
        src_size = reader.size()
        reader = None
        if src_size.isValid() and src_size.width() > 0 and src_size.height() > 0:
            scaled = src_size.scaled(self._max_gif_w, self._max_gif_h, Qt.KeepAspectRatio)
            self._old_label.setFixedSize(scaled)
            self._new_label.setFixedSize(scaled)


class GifPanel(QWidget):
    """Single-slot panel displaying one emotion GIF at a time with navigation.

    Use the settings menu or the on-screen arrow buttons to cycle through
    available emotions. Emits no signals; the parent window can call
    navigate_next / navigate_prev or select by key.
    """

    def __init__(
        self, panel_width: int, panel_height: int, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.setMinimumSize(1, 1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.resize(panel_width, panel_height)

        # Ordered list of emotion entries
        self._entries: list[dict] = []       # each: {"key": str, "path": str, "label": str, "etag": str}
        self._current_index: int = -1
        self._slot = CrossFadeGifSlot(self)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._nav_layout = QHBoxLayout()
        self._nav_layout.setContentsMargins(8, 8, 8, 0)
        self._nav_layout.setSpacing(4)

        btn_style = (
            "QPushButton {"
            "  background: rgba(255,255,255,30);"
            "  color: rgba(255,255,255,180);"
            "  border: none;"
            "  border-radius: 12px;"
            "  font-size: 18px;"
            "  padding: 0;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(255,255,255,80);"
            "  color: white;"
            "}"
            "QPushButton:disabled {"
            "  background: rgba(255,255,255,8);"
            "  color: rgba(255,255,255,40);"
            "}"
        )

        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedSize(28, 28)
        self._prev_btn.setStyleSheet(btn_style)
        self._prev_btn.clicked.connect(self.navigate_prev)

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedSize(28, 28)
        self._next_btn.setStyleSheet(btn_style)
        self._next_btn.clicked.connect(self.navigate_next)

        self._counter_label = QLabel("")
        self._counter_label.setStyleSheet(
            "color: rgba(255,255,255,100); font-size: 11px;"
        )
        self._counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._nav_layout.addWidget(self._prev_btn)
        self._nav_layout.addStretch(1)
        self._nav_layout.addWidget(self._counter_label)
        self._nav_layout.addStretch(1)
        self._nav_layout.addWidget(self._next_btn)

        layout.addLayout(self._nav_layout)
        layout.addWidget(self._slot, 0.8)

        self._update_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_slot(self, emotion_key: str, gif_path: str, emotion_label: str, etag: str) -> None:
        """Add or update an emotion entry. Switches to it if it's the only one."""
        # Update existing entry
        for entry in self._entries:
            if entry["key"] == emotion_key:
                entry["path"] = gif_path
                entry["label"] = emotion_label
                entry["etag"] = etag
                if self._slot.current_etag == etag:
                    return
                self._show_current()
                return

        # New entry
        self._entries.append({
            "key": emotion_key,
            "path": gif_path,
            "label": emotion_label,
            "etag": etag,
        })
        if self._current_index < 0:
            self._current_index = 0
        self._show_current()

    def remove_slot(self, emotion_key: str) -> None:
        self._entries = [e for e in self._entries if e["key"] != emotion_key]
        if self._current_index >= len(self._entries):
            self._current_index = max(0, len(self._entries) - 1)
        self._show_current()

    def clear_all(self) -> None:
        self._entries.clear()
        self._current_index = -1
        self._slot.clear()
        self._update_ui()

    def navigate_next(self) -> None:
        if len(self._entries) <= 1:
            return
        self._current_index = (self._current_index + 1) % len(self._entries)
        self._show_current()

    def navigate_prev(self) -> None:
        if len(self._entries) <= 1:
            return
        self._current_index = (self._current_index - 1) % len(self._entries)
        self._show_current()

    def select_by_key(self, emotion_key: str) -> None:
        for i, e in enumerate(self._entries):
            if e["key"] == emotion_key:
                self._current_index = i
                self._show_current()
                return

    def emotion_keys(self) -> list[str]:
        return [e["key"] for e in self._entries]

    def current_key(self) -> Optional[str]:
        if 0 <= self._current_index < len(self._entries):
            return self._entries[self._current_index]["key"]
        return None

    def current_label(self) -> str:
        if 0 <= self._current_index < len(self._entries):
            return self._entries[self._current_index]["label"]
        return ""

    def slot_count(self) -> int:
        return 1 if self._current_index >= 0 else 0

    def has_emotion(self, emotion_key: str) -> bool:
        return any(e["key"] == emotion_key for e in self._entries)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _show_current(self) -> None:
        if 0 <= self._current_index < len(self._entries):
            e = self._entries[self._current_index]
            self._slot.set_gif(e["path"], e["label"], e["etag"])
        else:
            self._slot.clear()
        self._update_ui()

    def _update_ui(self) -> None:
        n = len(self._entries)
        has_items = n > 0 and 0 <= self._current_index < n
        self._prev_btn.setEnabled(has_items and n > 1)
        self._next_btn.setEnabled(has_items and n > 1)
        if has_items:
            self._counter_label.setText(f"{self._current_index + 1} / {n}")
        else:
            self._counter_label.setText("")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if w < 1 or h < 1:
            return
        self.panel_width = w
        self.panel_height = h
        gif_w = max(200, w)
        gif_h = max(200, h - 50)
        self._slot.set_fixed_gif_size(gif_w, gif_h)


# ---------------------------------------------------------------------------
# Chat dialog widget
# ---------------------------------------------------------------------------

CHAT_STYLE = """
QScrollArea, QScrollArea > QWidget { background: transparent; border: none; }
QScrollBar:vertical {
    width: 4px; background: transparent;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,60); border-radius: 2px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

BUBBLE_USER = (
    "background: rgba(160,130,110,230);"
    "color: white;"
    "border-radius: 10px;"
    "padding: 6px 12px;"
    "font-size: 12px;"
)
BUBBLE_BOT = (
    "background: rgba(190,160,140,230);"
    "color: white;"
    "border-radius: 10px;"
    "padding: 6px 12px;"
    "font-size: 12px;"
)
INPUT_STYLE = (
    "QLineEdit {"
    "  background: rgba(200,175,155,230);"
    "  color: white;"
    "  border: none;"
    "  border-radius: 12px;"
    "  padding: 4px 12px;"
    "  font-size: 12px;"
    "}"
    "QLineEdit::placeholder { color: rgba(255,255,255,120); }"
)
SEND_STYLE = (
    "QPushButton {"
    "  background: rgba(160,130,110,230);"
    "  color: white;"
    "  border: none;"
    "  border-radius: 12px;"
    "  font-size: 12px;"
    "  padding: 4px 14px;"
    "}"
    "QPushButton:hover { background: rgba(140,110,90,240); }"
    "QPushButton:disabled { background: rgba(160,130,110,100); color: rgba(255,255,255,80); }"
)


class ChatDialog(QWidget):
    """Chat bubble area + text input for the desktop pet."""

    _result_ready = Signal(object)  # cross-thread signal (QueuedConnection)

    def __init__(self, api_base: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._api_base = api_base.rstrip("/")
        self.setMinimumHeight(80)
        self.setMaximumHeight(200)
        self.setStyleSheet(
            "ChatDialog {"
            "  background: #dcc4b0;"
            "  border-top-left-radius: 8px;"
            "  border-top-right-radius: 8px;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 6)
        layout.setSpacing(4)

        # --- Scrollable message area ---
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(CHAT_STYLE)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._msg_container = QWidget()
        self._msg_container.setStyleSheet("background: transparent;")
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(0, 0, 0, 0)
        self._msg_layout.setSpacing(4)
        self._msg_layout.addStretch(1)
        self._scroll.setWidget(self._msg_container)

        layout.addWidget(self._scroll, 1)

        # --- Input row ---
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("说点什么…")
        self._input.setStyleSheet(INPUT_STYLE)
        self._input.setFixedHeight(28)
        self._input.setMinimumWidth(200)
        self._input.returnPressed.connect(self._send)

        self._send_btn = QPushButton("发送")
        self._send_btn.setFixedSize(48, 28)
        self._send_btn.setStyleSheet(SEND_STYLE)

        from PySide6.QtWidgets import QSpinBox
        self._intensity = QSpinBox()
        self._intensity.setRange(1, 5)
        self._intensity.setValue(3)
        self._intensity.setPrefix("强度")
        self._intensity.setFixedWidth(65)
        self._intensity.setFixedHeight(28)

        input_row.addWidget(self._input, 1)
        input_row.addWidget(self._intensity)
        input_row.addWidget(self._send_btn)

        layout.addLayout(input_row)

        # Add welcome message
        self._add_bubble("你好，我是 Soyo！有什么想说的吗？", is_user=False)

        # Connect
        self._send_btn.clicked.connect(self._send)
        self._loading = False

        # Cross-thread signal: background thread emits, main thread handles
        self._result_ready.connect(self._on_result, Qt.ConnectionType.QueuedConnection)

        # Signals (outer handler)
        self.on_chat_response = None  # callable(response_dict)

    def _send(self) -> None:
        text = self._input.text().strip()
        if not text or self._loading:
            return
        self._input.clear()
        self._add_bubble(text, is_user=True)
        self._loading = True
        self._send_btn.setEnabled(False)
        self._input.setEnabled(False)
        self._input.setPlaceholderText("Soyo 正在思考…")
        self._call_chat_api(text, self._intensity.value())

    def _call_chat_api(self, text: str, intensity: int = 5) -> None:
        data = json.dumps({"text": text, "intensity": intensity}).encode("utf-8")
        url = f"{self._api_base}/api/desktop/chat"
        threading.Thread(
            target=self._do_request,
            args=(url, data),
            daemon=True,
        ).start()

    def _do_request(self, url: str, data: bytes) -> None:
        try:
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            result = {"reply": f"（连接后端失败: {e}）", "emotion": "平静"}

        self._result_ready.emit(result)

    def _on_result(self, result: dict) -> None:
        self._loading = False
        self._send_btn.setEnabled(True)
        self._input.setEnabled(True)
        self._input.setPlaceholderText("说点什么…")

        emotion = result.get("emotion", "平静")
        reply = result.get("reply", "")
        self._add_bubble(f"[{emotion}] {reply}", is_user=False)

        if self.on_chat_response:
            self.on_chat_response(result)

    def _add_bubble(self, text: str, is_user: bool) -> None:
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(max(300, self.width() - 40))
        bubble.setStyleSheet(BUBBLE_USER if is_user else BUBBLE_BOT)
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wr = QHBoxLayout(wrapper)
        wr.setContentsMargins(0, 0, 0, 0)
        if is_user:
            wr.addStretch(1)
            wr.addWidget(bubble)
        else:
            wr.addWidget(bubble)
            wr.addStretch(1)

        idx = self._msg_layout.count() - 1
        self._msg_layout.insertWidget(idx, wrapper)

        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        mw = max(300, self.width() - 60)
        for i in range(self._msg_layout.count()):
            item = self._msg_layout.itemAt(i)
            if item and item.widget():
                wrapper = item.widget()
                for child in wrapper.findChildren(QLabel):
                    child.setMaximumWidth(mw)
