"""
Module for executing management actions on the remote server based on pre-defined sections.
"""

import json
import shlex
from pathlib import Path
from ..ssh.ssh import SSH

class ManagementManager:
    """
    Manager class for executing custom and pre-defined administrative commands.
    """

    def __init__(self, ssh_client: SSH):
        """
        Initialize the ManagementManager.

        Args:
            ssh_client (SSH): Connected SSH client instance.
        """
        self.ssh = ssh_client

    def _storage_path(self) -> Path:
        """
        Get the path to the management sections configuration file.

        Returns:
            Path: The resolved Path object for the configuration file.
        """
        return Path(__file__).resolve().parents[2] / "storage" / "management_sections.json"

    def load_sections(self) -> dict:
        """
        Load management sections from the local storage.

        Returns:
            dict: A dictionary containing management sections and actions.
        """
        path = self._storage_path()
        if not path.exists():
            return {}
        
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def execute_action(self, action_config: dict, target: str, extra: str) -> tuple[bool, str, str, str, bool]:
        """
        Execute a pre-defined action with target and extra parameters.

        Args:
            action_config (dict): The configuration for the action to execute.
            target (str): The primary target of the action (e.g., user name, package name).
            extra (str): Additional arguments or parameters.

        Returns:
            tuple[bool, str, str, str, bool]: (success, command_string, stdout, stderr, sudo_used)
        """
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
        """
        Execute a custom shell command.

        Args:
            command (str): The command string to execute.
            use_sudo (bool): Whether to run the command with sudo privileges.

        Returns:
            tuple[bool, str, str]: (success, stdout, stderr)
        """
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