"""
Manager for Ubuntu Netplan (Static IP configuration).
"""
from ...components.ssh.ssh import SSH

class NetplanManager:
    def __init__(self, ssh_client: SSH):
        self.ssh = ssh_client

    def apply_static_ip(self, interface: str, ip_with_cidr: str, gateway: str, dns: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."

        yaml_content = f"""network:
  version: 2
  renderer: networkd
  ethernets:
    {interface}:
      dhcp4: false
      addresses:
        - {ip_with_cidr}
      routes:
        - to: default
          via: {gateway}
      nameservers:
        addresses: [{dns}]
"""
        try:
            safe_content = yaml_content.replace("'", "'\\''")
            cmd_write = f"echo '{safe_content}' | sudo tee /etc/netplan/99-rachotil-static.yaml > /dev/null"
            self.ssh.run_sudo_command(cmd_write)
            
            self.ssh.run_sudo_command("netplan apply")
            return True, "Netplan applied. Connection dropped."
        except Exception as e:
            return True, "IP changed. Please update your SSH config and reconnect."