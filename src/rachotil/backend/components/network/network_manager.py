import json
from pathlib import Path
from ...components.ssh.ssh import SSH

class NetworkManager:
    def __init__(self, ssh_client: SSH):
        self.ssh = ssh_client

    def _storage_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "storage" / "network_services.json"

    def load_software(self) -> list:
        path = self._storage_path()
        if not path.exists():
            return []
        
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def scan_services(self) -> tuple[bool, list | str]:
        if not self.ssh:
            return False, "SSH client is not connected."

        software_list = self.load_software()
        if not software_list:
            return False, "No services configured in network_services.json."

        results = []

        for soft in software_list:
            installed = "Not Installed"
            running = "Stopped"
            
            out_sys, _ = self.ssh.run_command(f"systemctl is-active {soft['service']}")
            if out_sys.strip() == "active":
                installed = "Installed (System)"
                running = "Running"
            elif out_sys.strip() in ["inactive", "failed"]:
                installed = "Installed (System)"
                running = "Stopped"
                
            if installed == "Not Installed":
                out_dock, _ = self.ssh.run_command(f"docker ps --filter name={soft['service']} --format '{{{{.Status}}}}'")
                if out_dock.strip():
                    installed = "Installed (Docker)"
                    if "Up" in out_dock:
                        running = "Running"
                else:
                    out_dock_all, _ = self.ssh.run_command(f"docker ps -a --filter name={soft['service']} --format '{{{{.Names}}}}'")
                    if out_dock_all.strip():
                        installed = "Installed (Docker)"
                        running = "Stopped"

            display_inst = f"[bold green]{installed}[/bold green]" if "Installed" in installed else "[yaml_not_inst]Not Installed[/yaml_not_inst]"
            display_run = f"[bold green]Running[/bold green]" if running == "Running" else f"[bold red]{running}[/bold red]"
            
            results.append((soft["name"], soft["type"], display_inst, display_run, soft["id"]))
            
        return True, results

    def get_service_details(self, soft_id: str) -> tuple[bool, dict | str]:
        if not self.ssh:
            return False, "SSH client is not connected."
            
        software_list = self.load_software()
        soft = next((s for s in software_list if s["id"] == soft_id), None)
        if not soft:
            return False, "Service not found in configuration."

        out_sys, _ = self.ssh.run_command(f"systemctl status {soft['service']} --no-pager -n 5")
        out_dock, _ = self.ssh.run_command(f"docker logs --tail 5 {soft['service']}")

        return True, {
            "name": soft["name"],
            "systemd": out_sys.strip() if out_sys.strip() else "No Native Systemd unit active.",
            "docker": out_dock.strip() if out_dock.strip() else "No active Docker container logs found."
        }