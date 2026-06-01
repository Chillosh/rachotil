import json
from pathlib import Path

def _storage_path() -> Path:
    return Path(__file__).resolve().parents[2] / "storage" / "keybinds_config.json"

def load_keybinds() -> dict:
    path = _storage_path()
    default_config = {"menu": "space", "quit": "q"}
    
    if not path.exists():
        return default_config
        
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_config

def save_keybinds(config: dict) -> None:
    path = _storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=4), encoding="utf-8")