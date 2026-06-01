"""
Module for fetching system information for the dashboard.
"""

from ...components.ssh.ssh import SSH

class DashboardManager:
    """
    Manager class for retrieving high-level system status and information.
    """

    def __init__(self, ssh_client: SSH):
        """
        Initialize the DashboardManager.

        Args:
            ssh_client (SSH): Connected SSH client instance.
        """
        self.ssh = ssh_client

    def fetch_sys_info(self) -> tuple[bool, str]:
        """
        Fetch basic system information including OS, kernel, uptime, RAM, and disk usage.

        Returns:
            tuple[bool, str]: A tuple containing a success flag and the formatted system info string or error message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."

        cmd = """
        echo "OS: $(grep PRETTY_NAME /etc/os-release | cut -d'=' -f2 | tr -d '\"')"
        echo "Kernel: $(uname -r)"
        echo "Uptime: $(uptime -p)"
        echo "RAM: $(free -m | awk '/Mem:/ {print $3" MB / "$2" MB"}')"
        echo "Disk (/): $(df -h / | awk 'NR==2 {print $3" / "$2" ("$5")"}')"
        echo "Local IP: $(hostname -I | awk '{print $1}')"
        echo "Public IP: $(curl -s ifconfig.me)"
        """
        
        try:
            out, err = self.ssh.run_command(cmd)
            if err and not out:
                 return False, f"Error fetching info: {err}"
            return True, out.strip()
        except Exception as e:
            return False, f"Execution error: {str(e)}"