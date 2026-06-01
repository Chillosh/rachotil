"""
Manager for handling Pi-hole diagnostics and environment preparation.
"""

from ...components.ssh.ssh import SSH

class PiholeManager:
    """
    Class responsible for verifying Pi-hole status and fixing systemd-resolved port conflicts.
    """

    def __init__(self, ssh_client: SSH) -> None:
        self.ssh = ssh_client

    def check_status(self) -> tuple[bool, dict | str]:
        """
        Check if Pi-hole is installed, running, and retrieve the web interface IP address.
        
        Returns:
            tuple[bool, dict | str]: A boolean indicating success, and a dictionary with status details or an error message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."
            
        try:
            out, err = self.ssh.run_command("which pihole")
            is_installed = bool(out.strip())
            
            ip_out, _ = self.ssh.run_command("hostname -I | awk '{print $1}'")
            server_ip = ip_out.strip()
            
            if is_installed:
                status_out, _ = self.ssh.run_sudo_command("pihole status")
                is_running = "Listening" in status_out or "active" in status_out.lower()
                status_text = "Running" if is_running else "Stopped or Error"
            else:
                status_text = "Not Installed"
                
            return True, {
                "installed": is_installed,
                "status": status_text,
                "ip": server_ip,
                "web_url": f"http://{server_ip}/admin" if server_ip else "Unknown"
            }
        except Exception as e:
            return False, f"Error checking Pi-hole: {str(e)}"

    def fix_port_53(self) -> tuple[bool, str]:
        """
        Disable DNSStubListener in systemd-resolved to free port 53 for Pi-hole.
        
        Returns:
            tuple[bool, str]: Success flag and execution message.
        """
        if not self.ssh:
            return False, "SSH client is not connected."
            
        try:
            cmd = (
                "sudo sed -i 's/#DNSStubListener=yes/DNSStubListener=no/' /etc/systemd/resolved.conf && "
                "sudo sed -i 's/DNSStubListener=yes/DNSStubListener=no/' /etc/systemd/resolved.conf && "
                "sudo systemctl restart systemd-resolved"
            )
            out, err = self.ssh.run_sudo_command(cmd)
            return True, "Port 53 freed. systemd-resolved stub listener disabled."
        except Exception as e:
            return False, f"Failed to fix port 53: {str(e)}"
            
    def get_install_command(self) -> str:
        """
        Get the official curl command required to install Pi-hole.
        
        Returns:
            str: The installation command.
        """
        return "curl -sSL https://install.pi-hole.net | bash"