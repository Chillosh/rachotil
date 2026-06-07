import os
import stat
import base64
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

    def list_directory(self, path: str) -> tuple[bool, list[tuple[str, str, str, str]] | str]:
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

    def create_file(self, current_path: str, filename: str) -> tuple[bool, str]:
        if not self.sftp:
            return False, "SFTP client is not connected."
        try:
            full_path = f"{current_path}/{filename}" if current_path != "/" else f"/{filename}"
            with self.sftp.open(full_path, 'w') as f:
                pass
            return True, f"File {filename} created."
        except Exception as e:
            return False, f"Failed to create file: {str(e)}"

    def create_directory(self, current_path: str, dirname: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            full_path = f"{current_path}/{dirname}" if current_path != "/" else f"/{dirname}"
            out, err = self.ssh.run_sudo_command(f"mkdir -p '{full_path}'")
            return True, f"Directory {dirname} created."
        except Exception as e:
            return False, f"Failed to create directory: {str(e)}"

    def delete_item(self, path: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            out, err = self.ssh.run_sudo_command(f"rm -rf '{path}'")
            return True, f"Deleted: {path}"
        except Exception as e:
            return False, f"Error deleting: {str(e)}"

    def copy_item(self, src_path: str, dest_path: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
        try:
            out, err = self.ssh.run_sudo_command(f"cp -r '{src_path}' '{dest_path}'")
            return True, f"Copied to: {dest_path}"
        except Exception as e:
            return False, f"Error copying: {str(e)}"
    
    def read_file(self, filepath: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."
            
        size_check, _ = self.ssh.run_sudo_command(f"stat -c%s '{filepath}'")
        try:
            if int(size_check.strip()) > 500000:
                return False, "File is too large to edit safely."
        except:
            pass

        out, err = self.ssh.run_sudo_command(f"cat '{filepath}'")
        if err and "No such file" in err:
            return False, err
            
        return True, out

    def save_file(self, filepath: str, content: str) -> tuple[bool, str]:
        if not self.ssh:
            return False, "SSH client is not connected."

        try:
            b64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            self.ssh.run_command(f"echo '{b64_content}' > /tmp/r_edit.b64")
            
            cmd = f"base64 -d /tmp/r_edit.b64 > /tmp/r_edit.txt && sudo mv /tmp/r_edit.txt '{filepath}'"
            self.ssh.run_sudo_command(cmd)
            
            self.ssh.run_command("rm -f /tmp/r_edit.b64 /tmp/r_edit.txt")
            
            return True, f"File saved successfully."
        except Exception as e:
            return False, f"Failed to save file: {str(e)}"
        
    def upload_file(self, local_path: str, remote_path: str) -> tuple[bool, str]:
        if not self.sftp:
            return False, "SFTP session is not open."
        import os
        if not os.path.exists(local_path):
            return False, "Local file not found."
            
        try:
            filename = os.path.basename(local_path)
            full_remote_path = f"{remote_path}/{filename}".replace("//", "/")
            self.sftp.put(local_path, full_remote_path)
            return True, f"Uploaded {filename} successfully."
        except Exception as e:
            return False, f"Upload failed: {str(e)}"