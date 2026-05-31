import os
import stat
from ...components.ssh.ssh import SSH

class SFTPManager:
    def __init__(self, ssh_client: SSH):
        self.ssh = ssh_client
        self.sftp = None

    def open_sftp(self) -> bool:
        if not self.ssh:
            return False
        try:
            self.sftp = self.ssh.get_sftp_client()
            return True
        except Exception:
            return False

    def close_sftp(self) -> None:
        if self.sftp:
            self.sftp.close()

    def list_directory(self, path: str) -> tuple[bool, list | str]:
        if not self.sftp:
            return False, "SFTP client is not connected."
            
        try:
            directory_items = self.sftp.listdir_attr(path)
            
            dirs = []
            files = []
            
            for item in directory_items:
                is_dir = stat.S_ISDIR(item.st_mode)
                size = f"{item.st_size} B"
                if item.st_size > 1048576:
                    size = f"{item.st_size / 1048576:.1f} MB"
                elif item.st_size > 1024:
                    size = f"{item.st_size / 1024:.1f} KB"
                    
                perms = stat.filemode(item.st_mode)
                
                if is_dir:
                    dirs.append(("[DIR]", item.filename, "", perms))
                else:
                    files.append(("[FILE]", item.filename, size, perms))
                    
            dirs.sort(key=lambda x: x[1].lower())
            files.sort(key=lambda x: x[1].lower())
            
            return True, dirs + files
        except Exception as e:
            return False, f"Error reading directory: {str(e)}"

    def download_file(self, remote_path: str, filename: str) -> tuple[bool, str]:
        if not self.sftp:
            return False, "SFTP client is not connected."
            
        try:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            local_path = os.path.join(downloads_dir, filename)
            
            self.sftp.get(remote_path, local_path)
            return True, f"Successfully downloaded to: {local_path}"
        except Exception as e:
            return False, f"Download failed: {str(e)}"