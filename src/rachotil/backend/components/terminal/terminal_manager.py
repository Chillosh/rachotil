import re
import json
from pathlib import Path
from ...components.ssh.ssh import SSH

class TerminalManager:
    def __init__(self, ssh_client: SSH):
        self.ssh = ssh_client
        self.config = self.load_config()
        self._ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def _storage_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "storage" / "terminal_config.json"

    def load_config(self) -> dict:
        path = self._storage_path()
        default_config = {"clean_ansi": True, "poll_interval": 0.5}
        
        if not path.exists():
            return default_config
        
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return default_config

    def open_shell(self) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            self.ssh.open_shell()
            return True, "Interactive shell opened."
        except Exception as e:
            return False, f"Error opening shell: {e}"

    def send_command(self, command: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            self.ssh.shell_send(command)
            return True, ""
        except Exception as e:
            return False, f"Critical error: {e}"

    def read_output(self) -> str:
        if not self.ssh:
            return ""
        
        output = self.ssh.shell_read()
        if output and self.config.get("clean_ansi", True):
            return self._ansi_escape.sub('', output)
        return output