"""Cross-platform raw keyboard input listener for interactive TUI navigation."""

import sys
from typing import Optional

KEY_UP = "UP"
KEY_DOWN = "DOWN"
KEY_LEFT = "LEFT"
KEY_RIGHT = "RIGHT"
KEY_ENTER = "ENTER"
KEY_ESC = "ESC"
KEY_BACK = "BACK"
KEY_QUIT = "QUIT"
KEY_REFRESH = "REFRESH"


class KeyListener:
    """Listens for single raw keypresses without requiring Enter."""

    def __init__(self):
        self.is_windows = sys.platform == "win32"
        self._old_settings = None

    def __enter__(self):
        if not self.is_windows:
            import termios
            import tty

            try:
                self.fd = sys.stdin.fileno()
                self._old_settings = termios.tcgetattr(self.fd)
                tty.setcbreak(self.fd)
            except Exception:
                self._old_settings = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.is_windows and self._old_settings:
            import termios

            try:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old_settings)
            except Exception:
                pass

    def read_key(self) -> Optional[str]:
        """Read a single key or key sequence (arrow keys, enter, esc)."""
        if self.is_windows:
            import msvcrt

            if not msvcrt.kbhit():
                return None
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                if ch2 == b"H":
                    return KEY_UP
                if ch2 == b"P":
                    return KEY_DOWN
                if ch2 == b"K":
                    return KEY_LEFT
                if ch2 == b"M":
                    return KEY_RIGHT
            if ch in (b"\r", b"\n"):
                return KEY_ENTER
            if ch == b"\x1b":
                return KEY_ESC
            if ch in (b"q", b"Q"):
                return KEY_QUIT
            if ch in (b"k", b"K"):
                return KEY_UP
            if ch in (b"j", b"J"):
                return KEY_DOWN
            return ch.decode("utf-8", errors="ignore")

        # Unix / macOS
        import select

        rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
        if not rlist:
            return None

        ch = sys.stdin.read(1)
        if ch == "\x1b":
            # Check if it is an escape sequence
            r2, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not r2:
                return KEY_ESC
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A":
                    return KEY_UP
                if ch3 == "B":
                    return KEY_DOWN
                if ch3 == "C":
                    return KEY_RIGHT
                if ch3 == "D":
                    return KEY_LEFT
            return KEY_ESC

        if ch in ("\r", "\n"):
            return KEY_ENTER
        if ch in ("q", "Q"):
            return KEY_QUIT
        if ch in ("k", "K"):
            return KEY_UP
        if ch in ("j", "J"):
            return KEY_DOWN
        if ch in ("r", "R"):
            return KEY_REFRESH
        if ch in ("b", "B"):
            return KEY_BACK
        return ch
