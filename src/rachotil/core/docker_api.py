import shlex
from .ssh_client import SSHClientWrapper

class DockerManager:
    def __init__(self):
        self.ssh = SSHClientWrapper()

    def check_installed(self):
        out, err = self.ssh.run_command("docker --version")
        if "command not found" in err or "command not found" in out:
            return False, ""
        return True, out.strip()

    def get_containers(self):
        cmd = "docker ps -a --format '{{.Names}}|{{.State}}|{{.Status}}|{{.Image}}'"
        out, err = self.ssh.run_sudo_command(cmd)
        results = []
        for line in out.strip().split("\n"):
            if line.strip():
                parts = line.split("|")
                if len(parts) == 4:
                    results.append(parts)
        return results

    def manage_container(self, action: str, name: str):
        if action not in ["start", "stop", "restart"]:
            raise ValueError("Invalid action")
        safe_name = shlex.quote(name)
        return self.ssh.run_sudo_command(f"docker {action} {safe_name}")

    def get_logs(self, name: str, lines: int = 50):
        safe_name = shlex.quote(name)
        out, err = self.ssh.run_sudo_command(f"docker logs --tail {lines} {safe_name}")
        return out if out else err