import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv, set_key

_ENV_PATH = Path(find_dotenv(usecwd=True) or (Path.cwd() / ".env"))

def load_env_config() -> Path:
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
    return _ENV_PATH


def get_ssh_config() -> dict[str, str]:
    load_env_config()
    password = os.getenv("SSH_PASSWORD", "")
    return {
        "host": os.getenv("SSH_HOST", ""),
        "user": os.getenv("SSH_USER", ""),
        "password": password,
        "sudo_password": os.getenv("SSH_SUDO_PASSWORD", password),
    }


def save_ssh_config(host: str, user: str, password: str, sudo_password: str = "") -> Path:
    env_path = load_env_config()
    env_path.touch(exist_ok=True)
    resolved_sudo_password = sudo_password or password

    set_key(str(env_path), "SSH_HOST", host, quote_mode="auto")
    set_key(str(env_path), "SSH_USER", user, quote_mode="auto")
    set_key(str(env_path), "SSH_PASSWORD", password, quote_mode="auto")
    set_key(str(env_path), "SSH_SUDO_PASSWORD", resolved_sudo_password, quote_mode="auto")

    os.environ["SSH_HOST"] = host
    os.environ["SSH_USER"] = user
    os.environ["SSH_PASSWORD"] = password
    os.environ["SSH_SUDO_PASSWORD"] = resolved_sudo_password
    return env_path
