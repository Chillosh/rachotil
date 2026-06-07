"""
Module for managing Docker containers on the remote server.
"""

import os
import re
from typing import Iterator
from ...components.ssh.ssh import SSH

class DockerManager:
    """
    Manager class for Docker operations including container listing, logs, and lifecycle management.
    """

    def __init__(self, ssh_client: SSH):
        """
        Initialize the DockerManager.

        Args:
            ssh_client (SSH): Connected SSH client instance.
        """
        self.ssh = ssh_client
        self._ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def check_docker_installed(self) -> tuple[bool, str]:
        """
        Verify if Docker is installed on the remote server.
        """
        if not self.ssh:
            return False, "SSH client is not connected."
            
        out, err = self.ssh.run_command("docker --version")
        if "command not found" in err or "command not found" in out:
            return False, "Docker is not installed on the server."
            
        return True, out.strip()

    def get_containers(self) -> tuple[bool, list[tuple[str, str, str, str]] | str]:
        """
        Retrieve a list of all Docker containers on the server.
        """
        if not self.ssh:
             return False, "SSH client is not connected."
             
        try:
            cmd = "docker ps -a --format '{{.Names}}|{{.State}}|{{.Status}}|{{.Image}}'"
            out, err = self.ssh.run_sudo_command(cmd)
            
            results = []
            for line in out.strip().split("\n"):
                if line.strip():
                    parts = line.split("|")
                    if len(parts) == 4:
                        name, state, status, image = parts
                        
                        if state == "running":
                            display_state = f"[bold green]{state.capitalize()}[/bold green]"
                        elif state == "exited":
                            display_state = f"[bold red]{state.capitalize()}[/bold red]"
                        else:
                            display_state = f"[yellow]{state.capitalize()}[/yellow]"
                            
                        results.append((name, display_state, status, image))
            return True, results
        except Exception as e:
             return False, f"Failed to fetch containers: {str(e)}"

    def manage_container(self, action: str, container_name: str) -> tuple[bool, str]:
        """
        Perform a lifecycle action (start, stop, restart) on a specific container.
        """
        if not self.ssh:
             return False, "SSH client is not connected."
             
        if action not in ["start", "stop", "restart"]:
             return False, "Invalid action."
             
        try:
             out, err = self.ssh.run_sudo_command(f"docker {action} {container_name}")
             return True, out.strip() or err.strip()
        except Exception as e:
             return False, f"Error: {str(e)}"

    def get_container_logs(self, container_name: str, lines: int = 50) -> tuple[bool, str]:
         """
         Fetch recent logs for a specific container.
         """
         if not self.ssh:
             return False, "SSH client is not connected."
             
         try:
             out, err = self.ssh.run_sudo_command(f"docker logs --tail {lines} {container_name}")
             log_output = out if out else err
             if not log_output:
                 log_output = "No logs available or container is empty."
             return True, log_output
         except Exception as e:
             return False, f"Failed to fetch logs: {str(e)}"
    
    def delete_container(self, container_id: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            out, err = self.ssh.run_sudo_command(f"docker rm -f {container_id}")
            return True, f"Container {container_id} deleted."
        except Exception as e:
            return False, str(e)

    def deploy_compose_stream(self, yaml_content: str) -> Iterator[tuple[bool, str]]:
        if not self.ssh:
            yield False, "SSH client is not connected."
            return

        try:
            safe_content = yaml_content.replace("'", "'\\''")
            cmd_write = f"echo '{safe_content}' | sudo tee /tmp/rachotil_compose.yml > /dev/null"
            self.ssh.run_sudo_command(cmd_write)
            
            cmd_up = "sudo docker compose -f /tmp/rachotil_compose.yml up -d"
            
            for line in self.ssh.run_sudo_command_stream(cmd_up):
                clean_line = self._ansi_escape.sub('', line).strip()
                if clean_line:
                    yield True, clean_line
        except Exception as e:
            yield False, f"Deploy failed: {str(e)}"