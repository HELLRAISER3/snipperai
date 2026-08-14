import sys
import os

APP_NAME = "SnipperAI"


def set_autostart(enable: bool) -> bool:
    """
    Enables or disables system autostart.
    On Windows, it writes/removes an entry in the CurrentUser Run registry key.
    """
    if sys.platform == "win32":
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            if getattr(sys, "frozen", False):
                exe_path = f'"{os.path.realpath(sys.executable)}"'
            else:
                exe_path = f'"{sys.executable}" "{os.path.realpath(sys.argv[0])}"'

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS
            )

            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)
            return True
        except Exception as exc:
            print(f"[Autostart Error] {exc}", file=sys.stderr)
            return False

    # Fallback for non-Windows platforms
    return True