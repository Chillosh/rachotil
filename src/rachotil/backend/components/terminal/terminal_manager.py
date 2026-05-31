"""
Module for managing interactive terminal sessions on the remote server.
"""

import re
import json
from pathlib import Path
from ...components.ssh.ssh import SSH

class TerminalManager:
    """
    Manager class for handling interactive shell communication and output filtering.
    """

    def __init__(self, ssh_client: SSH):
        """
        Initialize the TerminalManager.

        Args:
            ssh_client (SSH): Connected SSH client instance.
        """
        self.ssh = ssh_client
        self.config = self.load_config()
        self._ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def _storage_path(self) -> Path:
        """
        Get the path to the terminal configuration file.

        Returns:
            Path: The resolved Path object for the configuration file.
        """
        return Path(__file__).resolve().parents[2] / "storage" / "terminal_config.json"

    def load_config(self) -> dict:
        """
        Load terminal configuration from storage.

        Returns:
            dict: A dictionary containing terminal settings.
        """
        path = self._storage_path()
        default_config = {"clean_ansi": True, "poll_interval": 0.5}
        
        if not path.exists():
            return default_config
        
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return default_config

    def open_shell(self) -> tuple[bool, str]:
        """
        Initialize an interactive shell session.

        Returns:
            tuple[bool, str]: A success flag and a status message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            self.ssh.open_shell()
            return True, "Interactive shell opened."
        except Exception as e:
            return False, f"Error opening shell: {e}"

    def send_command(self, command: str) -> tuple[bool, str]:
        """
        Send a command to the active shell session.

        Args:
            command (str): The command string to send.

        Returns:
            tuple[bool, str]: A success flag and an optional error message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            self.ssh.shell_send(command)
            return True, ""
        except Exception as e:
            return False, f"Critical error: {e}"

    def read_output(self) -> str:
        """
        Read pending output from the shell session, optionally cleaning ANSI escape codes.

        Returns:
            str: The raw or cleaned output string.
        """
        if not self.ssh:
            return ""
        
        output = self.ssh.shell_read()
        if output and self.config.get("clean_ansi", True):
            return self._ansi_escape.sub('', output)
        return output