import shlex
from .ssh_client import SSHClientWrapper

class NetworkManager:
    def __init__(self):
        self.ssh = SSHClientWrapper()

    def get_ufw_status(self):
        out, err = self.ssh.run_sudo_command("ufw status numbered")
        return out

    def toggle_ufw(self, enable: bool):
        action = "enable" if enable else "disable"
        return self.ssh.run_sudo_command(f"ufw --force {action}")

    def add_ufw_rule(self, port: str, proto: str):
        safe_port = shlex.quote(port)
        cmd = f"ufw allow {safe_port}"
        if proto in ["tcp", "udp"]:
            cmd += f"/{proto}"
        return self.ssh.run_sudo_command(cmd)

    def delete_ufw_rule(self, rule_id: str):
        safe_id = shlex.quote(rule_id)
        return self.ssh.run_sudo_command(f"ufw --force delete {safe_id}")