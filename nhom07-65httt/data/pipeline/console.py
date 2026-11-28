import sys


def configure_utf8_console():
    """Configure Windows console streams so Vietnamese help text can be printed."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except (AttributeError, OSError):
            pass
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, OSError, ValueError):
                pass
