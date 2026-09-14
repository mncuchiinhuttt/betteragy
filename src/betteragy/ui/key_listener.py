"""Cross-platform raw keyboard input listener for interactive TUI navigation."""

import os
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
        self.fd = None

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
        if not self.is_windows and self._old_settings is not None:
            import termios

            try:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old_settings)
            except Exception:
                pass

    def read_key(self) -> Optional[str]:
        """Read a single key or key sequence (arrow keys, enter, esc)."""
        if self.is_windows:
            return self._read_windows()
        return self._read_unix()

    def _read_windows(self) -> Optional[str]:
        import msvcrt

        if not msvcrt.kbhit():
            return None
        ch = msvcrt.getch()
        if ch == b"\x03":
            raise KeyboardInterrupt
        if ch in (b"\x00", b"\xe0"):
            ch2 = msvcrt.getch()
            mapping = {b"H": KEY_UP, b"P": KEY_DOWN, b"K": KEY_LEFT, b"M": KEY_RIGHT}
            return mapping.get(ch2)
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

    def _read_unix(self) -> Optional[str]:
        import select

        if self.fd is None:
            return None

        rlist, _, _ = select.select([self.fd], [], [], 0.05)
        if not rlist:
            return None

        # Read bytes directly with os.read to avoid Python TextIOWrapper buffer eating escape sequences
        try:
            data = os.read(self.fd, 32)
        except (OSError, EOFError):
            return None

        if not data:
            return None

        if data == b"\x03":
            raise KeyboardInterrupt

        # If an ESC was read alone, check if the rest of sequence is immediately arriving
        if data == b"\x1b":
            r2, _, _ = select.select([self.fd], [], [], 0.03)
            if r2:
                try:
                    data += os.read(self.fd, 32)
                except (OSError, EOFError):
                    pass

        return self._parse_unix_sequence(data)

    @staticmethod
    def _parse_unix_sequence(data: bytes) -> str:
        """Parse raw terminal byte sequences into standardized key tokens."""
        if data.startswith(b"\x1b"):
            if len(data) == 1:
                return KEY_ESC
            seq = data[1:].decode("latin1", errors="ignore")
            # CSI sequences (\x1b[) and SS3 sequences (\x1bO)
            if seq in ("[A", "OA", "[5~", "[H", "1~"):
                return KEY_UP
            if seq in ("[B", "OB", "[6~", "[F", "4~"):
                return KEY_DOWN
            if seq in ("[C", "OC"):
                return KEY_RIGHT
            if seq in ("[D", "OD"):
                return KEY_LEFT
            return KEY_ESC

        char = data.decode("utf-8", errors="ignore")
        if char in ("\r", "\n"):
            return KEY_ENTER
        if char in ("q", "Q"):
            return KEY_QUIT
        if char in ("k", "K"):
            return KEY_UP
        if char in ("j", "J"):
            return KEY_DOWN
        if char in ("r", "R"):
            return KEY_REFRESH
        if char in ("b", "B", "\x7f", "\x08"):
            return KEY_BACK
        return char
