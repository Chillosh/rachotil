"""
Module for managing the configuration of system statistics blocks.
"""

import json
from pathlib import Path
from typing import Any

def _storage_dir() -> Path:
    """
    Get the directory path for storing configuration files.

    Returns:
        Path: The storage directory path.
    """
    path = Path(__file__).resolve().parents[2] / "storage"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_available_defaults() -> list[dict[str, Any]]:
    """
    Load the default statistics blocks from storage.

    Returns:
        list[dict[str, Any]]: A list of default block configurations.
    """
    path = _storage_dir() / "default_blocks.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

def _config_path() -> Path:
    """
    Get the path to the stats configuration file.

    Returns:
        Path: The path to stats_config.json.
    """
    return _storage_dir() / "stats_config.json"


def _default_config() -> dict[str, Any]:
    """
    Create a default configuration dictionary.

    Returns:
        dict[str, Any]: The default configuration.
    """
    return {"version": 1, "blocks": get_available_defaults()}


def _validate_block(block: Any) -> bool:
    """
    Validate a single statistics block configuration.

    Args:
        block (Any): The block configuration to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
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
    """
    Validate the entire statistics configuration dictionary.

    Args:
        data (Any): The configuration data to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
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
    """
    Load the statistics configuration from file, falling back to defaults if necessary.

    Returns:
        dict[str, Any]: The loaded configuration.
    """
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
    """
    Save a statistics configuration dictionary to file.

    Args:
        config (dict[str, Any]): The configuration to save.

    Returns:
        Path: The path to the saved file.

    Raises:
        ValueError: If the configuration is invalid.
    """
    if not _validate_config(config):
        raise ValueError("Invalid stats config")

    path = _config_path()
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def get_enabled_stats_blocks() -> list[dict[str, Any]]:
    """
    Retrieve only the statistics blocks that are currently enabled.

    Returns:
        list[dict[str, Any]]: A list of enabled block configurations.
    """
    config = load_stats_config()
    return [block for block in config["blocks"] if block.get("enabled")]