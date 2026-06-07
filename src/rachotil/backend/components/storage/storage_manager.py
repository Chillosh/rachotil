"""
Manager for block devices, partitions and LVM using lsblk.
"""
import json
from ...components.ssh.ssh import SSH

class StorageManager:
    def __init__(self, ssh_client: SSH):
        self.ssh = ssh_client

    def get_devices(self) -> tuple[bool, list | str]:
        if not self.ssh:
            return False, "SSH client is not connected."

        cmd = "lsblk -J -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT"
        out, err = self.ssh.run_sudo_command(cmd)

        if "lsblk: command not found" in err:
            return False, "lsblk is not installed on the server."

        try:
            start_idx = out.find('{')
            end_idx = out.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                clean_json = out[start_idx:end_idx]
                data = json.loads(clean_json)
                return True, data.get("blockdevices", [])
            else:
                return False, f"No valid JSON structure found in output. Raw: {out}"
                
        except json.JSONDecodeError:
            return False, f"Failed to parse lsblk output. Raw: {out}"