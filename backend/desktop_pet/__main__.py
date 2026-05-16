from __future__ import annotations

import argparse
import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "PySide6 is required. Install with:\n"
            "  pip install 'emotionmirror[desktop]' -e .\n"
            "or: pip install PySide6",
            file=sys.stderr,
        )
        return 1

    from backend.desktop_pet.window import DesktopAvatarWindow

    p = argparse.ArgumentParser(
        description="EmotionMirror desktop floating avatar (multi-emotion pet)"
    )
    p.add_argument(
        "--api",
        default="http://127.0.0.1:8000",
        help="FastAPI base URL (same as VITE_API_BASE)",
    )
    p.add_argument(
        "--poll-interval",
        type=float,
        default=2.5,
        help="Seconds between refresh checks",
    )
    p.add_argument(
        "--max-slots",
        type=int,
        default=6,
        help="Maximum number of emotion GIF slots to display simultaneously",
    )
    args = p.parse_args()

    app = QApplication(sys.argv)
    win = DesktopAvatarWindow(
        api_base=args.api,
        poll_interval=args.poll_interval,
        max_slots=args.max_slots,
    )
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
