import json
import shlex
from pathlib import Path
from ..ssh.ssh import SSH

class ManagementManager:
    def __init__(self, ssh_client: SSH):
        self.ssh = ssh_client

    def _storage_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "storage" / "management_sections.json"

    def load_sections(self) -> dict:
        path = self._storage_path()
        if not path.exists():
            return {}
        
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def execute_action(self, action_config: dict, target: str, extra: str) -> tuple[bool, str, str, str, bool]:
        if not self.ssh:
            return False, "SSH client not connected.", "", "", False

        command = action_config["command"].format(
            target=shlex.quote(target) if target else "",
            extra=shlex.quote(extra) if extra else "",
        )
        use_sudo = action_config.get("sudo", False)
        
        success, out, err = self.execute_custom(command, use_sudo)
        return success, command, out, err, use_sudo

    def execute_custom(self, command: str, use_sudo: bool) -> tuple[bool, str, str]:
        if not self.ssh:
            return False, "SSH client not connected.", ""
            
        try:
            if use_sudo:
                out, err = self.ssh.run_sudo_command(command)
            else:
                out, err = self.ssh.run_command(command)
            return True, out, err
        except Exception as e:
            return False, "", str(e)