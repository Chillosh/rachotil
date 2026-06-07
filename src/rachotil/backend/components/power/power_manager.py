"""
Manager for power operations (Shutdown, Reboot, Wake on LAN).
"""

import socket
import json
from pathlib import Path
from ...components.ssh.ssh import SSH

class PowerManager:
    def __init__(self, ssh_client: SSH = None):
        self.ssh = ssh_client

    def power_off(self) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            self.ssh.run_sudo_command("shutdown -h now")
            return True, "Shutdown command sent. Server is powering off."
        except Exception as e:
            return True, "Server connection closed (powering off)."
    
    def restart(self) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            self.ssh.run_sudo_command("reboot")
            return True, "Reboot command sent. Server is restarting."
        except Exception as e:
            return True, "Server connection closed (restarting)."

    def wake_on_lan(self, mac_address: str, broadcast_ip: str = "255.255.255.255") -> tuple[bool, str]:
        """
        Sends a Magic Packet to the specified MAC address to wake up the machine.
        This runs LOCALLY from the client PC, no SSH needed.
        """
        mac_clean = mac_address.replace(":", "").replace("-", "").upper()
        if len(mac_clean) != 12:
            return False, "Invalid MAC address format."

        try:
            data = bytes.fromhex("FF" * 6 + mac_clean * 16)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(data, (broadcast_ip, 9))
                
            return True, f"Magic Packet sent to {mac_address}."
        except Exception as e:
            return False, f"Failed to send WOL packet: {str(e)}"
            
    def _mac_storage_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "storage" / "power_config.json"

    def get_saved_mac(self) -> str:
        path = self._mac_storage_path()
        if path.exists():
            try:
                return json.loads(path.read_text()).get("mac_address", "")
            except: pass
        return ""

    def save_mac(self, mac: str) -> None:
        path = self._mac_storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"mac_address": mac}))