"""
Module for managing systemd services on the remote server.
"""

from ...components.ssh.ssh import SSH

class ServicesManager:
    """
    Manager class for systemd service operations including listing and lifecycle management.
    """

    def __init__(self, ssh_client: SSH):
        """
        Initialize the ServicesManager.

        Args:
            ssh_client (SSH): Connected SSH client instance.
        """
        self.ssh = ssh_client

    def get_services(self) -> tuple[bool, list[tuple[str, str]] | str]:
        """
        Retrieve a list of all systemd services and their status.

        Returns:
            tuple[bool, list[tuple[str, str]] | str]: A success flag and either a list of service status tuples or an error message.
        """
        if not self.ssh:
             return False, "SSH client is not connected."
             
        try:
            cmd = "systemctl list-units --type=service --all --no-pager --plain"
            out, err = self.ssh.run_command(cmd)
            
            results = []
            for line in out.split("\n"):
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0].endswith(".service"):
                    svc_name = parts[0].replace(".service", "")
                    active_state = parts[2]
                    
                    if active_state == "active":
                        display_status = "[bold green]Active[/bold green]"
                    elif active_state in ["inactive", "failed"]:
                        display_status = f"[bold red]{active_state.capitalize()}[/bold red]"
                    else:
                        display_status = f"[yellow]{active_state}[/yellow]"
                        
                    results.append((svc_name, display_status))
            return True, results
        except Exception as e:
             return False, f"Scan failed: {str(e)}"

    def manage_service(self, action: str, svc_name: str) -> tuple[bool, str]:
        """
        Perform a lifecycle action (start, stop, restart) on a specific systemd service.

        Args:
            action (str): The action to perform ("start", "stop", or "restart").
            svc_name (str): The name of the service.

        Returns:
            tuple[bool, str]: A success flag and the output or an error message.
        """
        if not self.ssh:
             return False, "SSH client is not connected."
             
        if action not in ["start", "stop", "restart"]:
             return False, "Invalid action."
             
        try:
             out, err = self.ssh.run_sudo_command(f"systemctl {action} {svc_name}")
             return True, out.strip() or err.strip()
        except Exception as e:
             return False, f"Error: {str(e)}"