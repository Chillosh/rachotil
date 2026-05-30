import json
from pathlib import Path

class ConfigStore:
    _instance = None
    CONFIG_DIR = Path.home() / ".config" / "rachotil"
    CONFIG_FILE = CONFIG_DIR / "settings.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigStore, cls).__new__(cls)
            cls._instance.data = {}
            cls._instance.load()
        return cls._instance

    def load(self):
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = self._get_default_data()
                self.save()
        else:
            self.data = self._get_default_data()
            self.save()

    def _get_default_data(self):
        return {
            "ssh": {"host": "", "user": "", "password": "", "sudo_password": ""},
            "stats": {"blocks": []},
            "theme": "theme-dark"
        }

    def save(self):
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()