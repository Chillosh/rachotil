import paramiko

"""
Module for handling SSH connections and command execution.
"""

import paramiko

class SSH:
    """
    Class for managing an SSH connection to a remote server using Paramiko.
    """

    def __init__(self, host: str, user: str, password: str, sudo_password: str | None = None):
        """
        Initialize the SSH connection parameters.

        Args:
            host (str): Remote host address.
            user (str): SSH username.
            password (str): SSH password.
            sudo_password (str | None): Optional sudo password. Defaults to password.
        """
        self.host = host
        self.user = user
        self.password = password
        self.sudo_password = sudo_password or password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.shell = None

    def connect(self) -> None:
        """
        Establish the SSH connection.
        """
        self.client.connect(
            hostname=self.host,
            username=self.user,
            password=self.password,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )

    def run_command(self, command: str, get_pty: bool = False) -> tuple[str, str]:
        """
        Run a command on the remote server.

        Args:
            command (str): The command to execute.
            get_pty (bool): Whether to request a pseudo-terminal.

        Returns:
            tuple[str, str]: (stdout, stderr)
        """
        stdin, stdout, stderr = self.client.exec_command(command, get_pty=get_pty)
        out = stdout.read().decode()
        err = stderr.read().decode()
        stdout.channel.recv_exit_status()
        return out, err

    def run_sudo_command(self, command: str, sudo_password: str | None = None) -> tuple[str, str]:
        """
        Run a command with sudo privileges on the remote server.

        Args:
            command (str): The command to execute.
            sudo_password (str | None): Optional sudo password.

        Returns:
            tuple[str, str]: (stdout, stderr)
        """
        password = sudo_password if sudo_password is not None else self.sudo_password
        prepared = command.strip()
        if not prepared:
            return "", "Empty command"

        if not prepared.startswith("sudo "):
            prepared = f"sudo -S -p '' {prepared}"
        else:
            prepared = prepared.replace("sudo ", "sudo -S -p '' ", 1)

        stdin, stdout, stderr = self.client.exec_command(prepared, get_pty=True)
        if password:
            stdin.write(password + "\n")
            stdin.flush()

        out = stdout.read().decode()
        err = stderr.read().decode()
        stdout.channel.recv_exit_status()
        return out, err

    def run_sudo_command_stream(self, command: str):
        """
        Execute a sudo command and yield the output line by line in real-time.
        Requires get_pty=True to prevent APT from hanging on background daemon triggers.
        """
        if not self.client:
            raise Exception("SSH client is not connected.")

        stdin, stdout, stderr = self.client.exec_command(f"sudo -S -p '' {command}", get_pty=True)

        if self.sudo_password:
            stdin.write(self.sudo_password + "\n")
            stdin.flush()

        for line in iter(stdout.readline, ""):
            yield line.strip()
    
    def open_shell(self) -> paramiko.Channel:
        """
        Open an interactive shell channel.

        Returns:
            paramiko.Channel: The interactive shell channel.
        """
        self.shell = self.client.invoke_shell(width=120, height=40, term="dumb")
        self.shell.settimeout(0.0)
        return self.shell

    def shell_send(self, command: str) -> None:
        """
        Send a command to the active interactive shell.

        Args:
            command (str): The command to send.
        """
        if self.shell is None:
            self.open_shell()
        self.shell.send(command.rstrip("\n") + "\n")

    def shell_read(self) -> str:
        """
        Read output from the active interactive shell.

        Returns:
            str: The output read from the shell.
        """
        if self.shell is None or not self.shell.recv_ready():
            return ""
        
        return self.shell.recv(65535).decode(errors="ignore")

    def get_sftp_client(self) -> paramiko.SFTPClient:
        """
        Open an SFTP session from the existing SSH connection.

        Returns:
            paramiko.SFTPClient: The SFTP client instance.
        """
        return self.client.open_sftp()

    def download_file(self, remote_path: str, local_path: str) -> tuple[bool, str]:
        """
        Download a file from the remote server.

        Args:
            remote_path (str): Path to the remote file.
            local_path (str): Path to the local file.

        Returns:
            tuple[bool, str]: (success, status_message)
        """
        sftp = self.get_sftp_client()
        try:
            sftp.get(remote_path, local_path)
            return True, f"Downloaded {remote_path} to {local_path}"
        except Exception as e:
            return False, f"Download failed: {str(e)}"
        finally:
            sftp.close()

    def upload_file(self, local_path: str, remote_path: str) -> tuple[bool, str]:
        """
        Upload a file to the remote server.

        Args:
            local_path (str): Path to the local file.
            remote_path (str): Path to the remote file.

        Returns:
            tuple[bool, str]: (success, status_message)
        """
        sftp = self.get_sftp_client()
        try:
            sftp.put(local_path, remote_path)
            return True, f"Uploaded {local_path} to {remote_path}"
        except Exception as e:
            return False, f"Upload failed: {str(e)}"
        finally:
            sftp.close()

    def file_exists(self, remote_path: str) -> bool:
        """
        Check if a file exists on the remote server.

        Args:
            remote_path (str): Path to the remote file.

        Returns:
            bool: True if it exists, False otherwise.
        """
        sftp = self.get_sftp_client()
        try:
            sftp.stat(remote_path)
            return True
        except IOError:
            return False
        finally:
            sftp.close()

    def close(self) -> None:
        """
        Close the SSH connection and any active shell.
        """
        if self.shell is not None:
            self.shell.close()
            self.shell = None
        self.client.close()