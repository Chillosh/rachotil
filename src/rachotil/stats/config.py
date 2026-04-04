import json
from pathlib import Path
from typing import Any

_DEFAULT_BLOCKS = [
    {
        "id": "ram_cpu",
        "label": "RAM+CPU monitoring",
        "command": "top -bn1 | head -n 15",
        "interval_seconds": 2,
        "enabled": True,
        "built_in": True,
    },
    {
        "id": "disk",
        "label": "DISK load",
        "command": "df -h",
        "interval_seconds": 10,
        "enabled": True,
        "built_in": True,
    },
    {
        "id": "network",
        "label": "NETWORK",
        "command": "ip addr show",
        "interval_seconds": 10,
        "enabled": True,
        "built_in": True,
    },
    {
        "id": "processes",
        "label": "PROCESSES",
        "command": "ps aux --sort=-%mem | head -n 10",
        "interval_seconds": 10,
        "enabled": True,
        "built_in": True,
    },
    {
        "id": "services",
        "label": "SERVICES",
        "command": "systemctl status | head -n 15",
        "interval_seconds": 10,
        "enabled": True,
        "built_in": True,
    },
    {
        "id": "users",
        "label": "USERS",
        "command": "w",
        "interval_seconds": 10,
        "enabled": True,
        "built_in": True,
    },
]


def _config_path() -> Path:
    # config.py -> stats -> rachotil -> src -> project root
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "stats_config.json"


def _default_config() -> dict[str, Any]:
    return {"version": 1, "blocks": [dict(item) for item in _DEFAULT_BLOCKS]}


def _validate_block(block: Any) -> bool:
    if not isinstance(block, dict):
        return False

    required = ["id", "label", "command", "interval_seconds", "enabled"]
    if any(key not in block for key in required):
        return False

    return (
        isinstance(block["id"], str)
        and block["id"].strip() != ""
        and isinstance(block["label"], str)
        and block["label"].strip() != ""
        and isinstance(block["command"], str)
        and block["command"].strip() != ""
        and isinstance(block["interval_seconds"], int)
        and block["interval_seconds"] > 0
        and isinstance(block["enabled"], bool)
    )


def _validate_config(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    if not isinstance(data.get("blocks"), list):
        return False

    seen_ids = set()
    for block in data["blocks"]:
        if not _validate_block(block):
            return False
        if block["id"] in seen_ids:
            return False
        seen_ids.add(block["id"])

    return True


def load_stats_config() -> dict[str, Any]:
    path = _config_path()
    if not path.exists():
        default = _default_config()
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default

    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        content = _default_config()
        path.write_text(json.dumps(content, indent=2), encoding="utf-8")
        return content

    if not _validate_config(content):
        content = _default_config()
        path.write_text(json.dumps(content, indent=2), encoding="utf-8")

    return content


def save_stats_config(config: dict[str, Any]) -> Path:
    if not _validate_config(config):
        raise ValueError("Invalid stats config")

    path = _config_path()
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def get_enabled_stats_blocks() -> list[dict[str, Any]]:
    config = load_stats_config()
    return [block for block in config["blocks"] if block.get("enabled")]
