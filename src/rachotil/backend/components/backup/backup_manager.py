"""
Module for managing server backups.
Provides functionality to search directories and create/download archives.
"""

import os
from datetime import datetime
from typing import Callable
from ..ssh.ssh import SSH

class BackupManager:
    """
    Manager class for handling backup operations on the remote server.
    """

    def __init__(self, ssh_client: SSH) -> None:
        self.ssh = ssh_client

    def search_directories(self, query: str) -> list[str]:
        if not self.ssh:
            raise RuntimeError("SSH client is not connected.")
        
        cmd = f"find / -maxdepth 4 -name '*{query}*' -type d 2>/dev/null | head -10"
        out, err = self.ssh.run_command(cmd)
        
        return [line.strip() for line in out.strip().split("\n") if line.strip()]

    def create_and_download_backup(self, dirs_to_backup: list[str], backup_name: str, local_dest: str, status_callback: Callable[[str], None] | None = None) -> tuple[bool, str]:
        """
        Create a compressed archive of specified directories and download it to the local machine.
        """
        if not self.ssh:
             return False, "SSH client is not connected."

        if not dirs_to_backup:
             return False, "Select at least one directory for backup."

        if not backup_name:
             return False, "Backup name cannot be empty."

        if not backup_name.endswith(".tar.gz"):
            backup_name += ".tar.gz"

        dirs_str = " ".join(f'"{d}"' for d in dirs_to_backup)
        remote_archive = f"/tmp/{backup_name}"

        if status_callback:
            status_callback(f"Step 1/3: Archiving data on server to {backup_name}...")
            status_callback(f"Includes: {', '.join(dirs_to_backup)}")

        cmd = f"tar -czf {remote_archive} {dirs_str} 2>&1"
        out, err = self.ssh.run_sudo_command(cmd)

        if not self.ssh.file_exists(remote_archive):
            return False, f"Failed to create backup on server. Details: {err or out}"

        if status_callback:
            status_callback("Step 1/3 completed. Archive created on server.")

        os.makedirs(local_dest, exist_ok=True)
        local_file = os.path.join(local_dest, backup_name)

        if status_callback:
            status_callback(f"Step 2/3: Downloading data to your machine...")
            status_callback(f"Path: {local_file}")

        success, message = self.ssh.download_file(remote_archive, local_file)

        if not success:
            return False, f"Download failed: {message}"

        if status_callback:
            status_callback("Step 2/3 completed. File successfully downloaded.")
            status_callback("Step 3/3: Cleaning up /tmp directory on server...")
            
        self.ssh.run_command(f"rm {remote_archive}")

        return True, f"SUCCESS: Backup is ready in {local_dest}."