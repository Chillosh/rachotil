import json
from pathlib import Path
from ...components.ssh.ssh import SSH

class SnapshotManager:
    def __init__(self, ssh_client: SSH):
        self.ssh = ssh_client

    def _storage_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "storage" / "snapshot_config.json"

    def load_config(self) -> dict:
        path = self._storage_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_snapshots(self) -> tuple[bool, list | str]:
        if not self.ssh:
            return False, "SSH client is not connected."

        out, err = self.ssh.run_sudo_command("timeshift --list")
        
        if "command not found" in err or "command not found" in out:
            return False, "Error: 'timeshift' is not installed. Run: sudo apt install timeshift"

        parsed_data = []
        lines = out.split("\n")
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].isdigit() and parts[1] == '>':
                s_id = parts[0]
                s_date = parts[2]
                s_tags = parts[3] if len(parts) > 3 else ""
                s_desc = " ".join(parts[4:]) if len(parts) > 4 else ""
                parsed_data.append((s_id, s_date, s_tags, s_desc))

        return True, parsed_data

    def create_snapshot(self, description: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."

        if not description:
            config = self.load_config()
            description = config.get("default_description", "Manual backup")

        cmd = f"timeshift --create --comments '{description}'"
        out, err = self.ssh.run_sudo_command(cmd)

        if "E:" in out or "Error" in err:
            return False, err or out
            
        return True, "Snapshot created successfully."

    def delete_snapshot(self, snap_name: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."

        cmd = f"timeshift --delete --snapshot '{snap_name}'"
        out, err = self.ssh.run_sudo_command(cmd)
        
        return True, f"Snapshot {snap_name} deleted."

    def restore_snapshot(self, snap_name: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."

        cmd = f"timeshift --restore --snapshot '{snap_name}' --yes"
        try:
            self.ssh.run_sudo_command(cmd)
            return True, "Restore command sent. Connection may drop due to automatic reboot."
        except Exception as e:
            return False, f"Error during restore: {str(e)}"