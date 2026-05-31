"""
Module for fetching system statistics from the remote server.
"""

from ...components.ssh.ssh import SSH

class StatsManager:
    """
    Manager class for retrieving various system metrics and statistics.
    """

    def __init__(self, ssh_client: SSH):
        """
        Initialize the StatsManager.

        Args:
            ssh_client (SSH): Connected SSH client instance.
        """
        self.ssh = ssh_client

    def fetch_stat(self, command: str) -> str:
        """
        Execute a statistics-gathering command and return the output.

        Args:
            command (str): The command to run.

        Returns:
            str: The output of the command or an error message.
        """
        if not self.ssh:
            return "Error: SSH client not connected."
            
        try:
            out, err = self.ssh.run_command(command)
            return out.strip() if out else err.strip()
        except Exception as e:
            return f"Error: {e}"