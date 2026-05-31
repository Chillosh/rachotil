"""
Module for managing system snapshots using Timeshift on the remote server.
"""

import json
from pathlib import Path
from ...components.ssh.ssh import SSH

class SnapshotManager:
    """
    Manager class for system snapshot operations including creation, deletion, and restoration.
    """

    def __init__(self, ssh_client: SSH):
        """
        Initialize the SnapshotManager.

        Args:
            ssh_client (SSH): Connected SSH client instance.
        """
        self.ssh = ssh_client

    def _storage_path(self) -> Path:
        """
        Get the path to the snapshot configuration file.

        Returns:
            Path: The resolved Path object for the configuration file.
        """
        return Path(__file__).resolve().parents[2] / "storage" / "snapshot_config.json"

    def load_config(self) -> dict:
        """
        Load snapshot configuration from storage.

        Returns:
            dict: A dictionary containing snapshot configuration settings.
        """
        path = self._storage_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_snapshots(self) -> tuple[bool, list[tuple[str, str, str, str]] | str]:
        """
        Retrieve a list of available system snapshots.

        Returns:
            tuple[bool, list[tuple[str, str, str, str]] | str]: A success flag and either a list of snapshot info tuples or an error message.
        """
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
        """
        Create a new system snapshot with the given description.

        Args:
            description (str): A description for the new snapshot.

        Returns:
            tuple[bool, str]: A success flag and a status message.
        """
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
        """
        Delete an existing system snapshot.

        Args:
            snap_name (str): The identifier or tag of the snapshot to delete.

        Returns:
            tuple[bool, str]: A success flag and a status message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."

        cmd = f"timeshift --delete --snapshot '{snap_name}'"
        out, err = self.ssh.run_sudo_command(cmd)
        
        return True, f"Snapshot {snap_name} deleted."

    def restore_snapshot(self, snap_name: str) -> tuple[bool, str]:
        """
        Restore the system to a specific snapshot.

        Args:
            snap_name (str): The identifier or tag of the snapshot to restore.

        Returns:
            tuple[bool, str]: A success flag and a status message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."

        cmd = f"timeshift --restore --snapshot '{snap_name}' --yes"
        try:
            self.ssh.run_sudo_command(cmd)
            return True, "Restore command sent. Connection may drop due to automatic reboot."
        except Exception as e:
            return False, f"Error during restore: {str(e)}"