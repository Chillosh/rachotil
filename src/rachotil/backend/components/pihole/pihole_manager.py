"""
Manager for handling Pi-hole diagnostics and environment preparation.
"""
import base64

from ...components.ssh.ssh import SSH

class PiholeManager:
    """
    Class responsible for verifying Pi-hole status and fixing systemd-resolved port conflicts.
    """

    def __init__(self, ssh_client: SSH) -> None:
        self.ssh = ssh_client

    def check_status(self) -> tuple[bool, dict | str]:
        if not self.ssh:
            return False, "SSH client is not connected."
            
        try:
            out, _ = self.ssh.run_sudo_command("systemctl is-active pihole-FTL")
            is_running = "active" in out.lower()
            
            out_check, _ = self.ssh.run_command("which pihole")
            is_installed = bool(out_check.strip())
            
            ip_out, _ = self.ssh.run_command("hostname -I | awk '{print $1}'")
            server_ip = ip_out.split()[0] if ip_out.strip() else "Unknown"
            
            return True, {
                "installed": is_installed,
                "status": "Running" if is_running else "Stopped",
                "ip": server_ip,
                "web_url": f"http://{server_ip}/admin"
            }
        except Exception as e:
            return False, f"Error: {str(e)}"

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
    
    def start_pihole(self) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            self.ssh.run_sudo_command("sudo systemctl restart pihole-FTL")
            return True, "Pi-hole service started."
        except Exception as e:
            return False, f"Failed to start: {str(e)}"
            
    def install_pihole(self) -> tuple[bool, str]:   
        if not self.ssh:
            return False, "SSH client is not connected."
            
        try:
            cmd = "curl -sSL https://install.pi-hole.net | bash"
            
            out, err = self.ssh.run_sudo_command(cmd)
            
            return True, "Installation has been completed. Please check the status after a moment."
        except Exception as e:
            return False, f"Install failed: {str(e)}"

    def update_pihole(self) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
            
        try:
            out, err = self.ssh.run_sudo_command("pihole -up")
            return True, "Pi-hole successfully updated."
        except Exception as e:
            return False, f"Update failed: {str(e)}"

    def uninstall_pihole(self) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
            
        try:
            out, err = self.ssh.run_sudo_command("bash -c 'yes | pihole uninstall'")
            return True, "Pi-hole was successfully uninstalled."
        except Exception as e:
            return False, f"Uninstall failed: {str(e)}"