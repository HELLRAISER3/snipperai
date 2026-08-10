import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

APP_NAME = "SnipperAI"

# On Windows: C:\Users\<Username>\AppData\Roaming\SnipperAI
CONFIG_DIR = Path(os.getenv("APPDATA") or Path.home() / ".config") / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"


class Settings(BaseSettings):
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def save_api_key(self, key: str):
        """Saves a user's API key to local OS storage."""
        self.openrouter_api_key = key
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"OPENROUTER_API_KEY": key}, f, indent=2)

    @classmethod
    def load(cls) -> "Settings":
        """
        Loads key in order:
        1. Local user config (%APPDATA%/SnipperAI/config.json)
        2. Developer .env file
        """
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("OPENROUTER_API_KEY"):
                        return cls(openrouter_api_key=data["OPENROUTER_API_KEY"])
            except Exception:
                pass

        return cls()


settings = Settings.load()