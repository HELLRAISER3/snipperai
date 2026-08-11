import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

APP_NAME = "SnipperAI"
CONFIG_DIR = Path(os.getenv("APPDATA") or Path.home() / ".config") / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"


class Settings(BaseSettings):
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    hotkey: str = Field(default="ctrl+shift+s", alias="HOTKEY")
    autostart: bool = Field(default=False, alias="AUTOSTART")
    first_launch: bool = Field(default=True, alias="FIRST_LAUNCH")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def save_settings(
        self,
        api_key: str | None,
        hotkey: str = "ctrl+shift+s",
        autostart: bool = False,
        first_launch: bool = False,
    ):
        self.openrouter_api_key = api_key
        self.hotkey = hotkey.lower()
        self.autostart = autostart
        self.first_launch = first_launch

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "OPENROUTER_API_KEY": self.openrouter_api_key,
            "HOTKEY": self.hotkey,
            "AUTOSTART": self.autostart,
            "FIRST_LAUNCH": self.first_launch,
        }

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    @classmethod
    def load(cls) -> "Settings":
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(
                        openrouter_api_key=data.get("OPENROUTER_API_KEY"),
                        hotkey=data.get("HOTKEY", "ctrl+shift+s"),
                        autostart=data.get("AUTOSTART", False),
                        first_launch=data.get("FIRST_LAUNCH", False),  
                    )
            except Exception:
                pass

        return cls()


settings = Settings.load()