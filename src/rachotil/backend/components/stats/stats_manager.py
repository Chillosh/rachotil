from ...components.ssh.ssh import SSH

class StatsManager:
    def __init__(self, ssh_client: SSH):
        self.ssh = ssh_client

    def fetch_stat(self, command: str) -> str:
        if not self.ssh:
            return "Error: SSH client not connected."
            
        try:
            out, err = self.ssh.run_command(command)
            return out.strip() if out else err.strip()
        except Exception as e:
            return f"Error: {e}"