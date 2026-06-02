"""
Module for handling APT package management on the remote Debian/Ubuntu server.
"""
import re
from typing import Iterator
from ...components.ssh.ssh import SSH

class PackagesManager:
    """
    Manager class for APT operations like install, remove, update, and search in real-time.
    """

    def __init__(self, ssh_client: SSH) -> None:
        self.ssh = ssh_client
        self._ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def execute_apt_stream(self, action: str, package: str = "") -> Iterator[tuple[bool, str]]:
        """
        Execute an apt command and yield the output stream line by line.

        Args:
            action (str): The apt action (update, upgrade, install, remove, search).
            package (str): The package name (required for install, remove, search).

        Yields:
            tuple[bool, str]: Success flag and single output line.
        """
        if not self.ssh:
            yield False, "SSH client is not connected."
            return

        cmd = ""
        if action == "update":
            cmd = "apt-get update"
        elif action == "upgrade":
            cmd = "DEBIAN_FRONTEND=noninteractive apt-get upgrade -y"
        elif action == "install":
            cmd = f"DEBIAN_FRONTEND=noninteractive apt-get install -y {package}"
        elif action == "remove":
            cmd = f"DEBIAN_FRONTEND=noninteractive apt-get remove -y {package}"
        elif action == "search":
            cmd = f"apt-cache search {package}"
        else:
            yield False, "Unknown action."
            return

        try:
            if action == "search":
                stdin, stdout, stderr = self.ssh.client.exec_command(cmd, get_pty=True)
                for line in iter(stdout.readline, ""):
                    clean_line = self._ansi_escape.sub('', line).strip()
                    if clean_line:
                        yield True, clean_line
            else:
                for line in self.ssh.run_sudo_command_stream(cmd):
                    clean_line = self._ansi_escape.sub('', line).strip()
                    if clean_line:
                        yield True, clean_line
                        
        except Exception as e:
            yield False, f"Error executing APT command: {str(e)}"