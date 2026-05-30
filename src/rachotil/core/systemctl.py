from .ssh_client import SSHClientWrapper

class SystemctlManager:
    def __init__(self):
        self.ssh = SSHClientWrapper()

    def get_all_services(self):
        cmd = "systemctl list-units --type=service --all --no-pager --plain"
        out, err = self.ssh.run_command(cmd)
        results = []
        for line in out.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].endswith(".service"):
                svc_name = parts[0].replace(".service", "")
                active_state = parts[2]
                results.append((svc_name, active_state))
        return results

    def manage_service(self, service: str, action: str):
        if action not in ["start", "stop", "restart"]:
            raise ValueError("Invalid action")
        return self.ssh.run_sudo_command(f"systemctl {action} {service}")