import paramiko
from ..storage.config_store import ConfigStore

class SSHClientWrapper:
    def __init__(self):
        self.db = ConfigStore()
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connected = False

    def connect(self):
        ssh_conf = self.db.get("ssh", {})
        if not ssh_conf.get("host") or not ssh_conf.get("user"):
            raise ValueError("SSH credentials not configured.")
            
        self.client.connect(
            hostname=ssh_conf["host"],
            username=ssh_conf["user"],
            password=ssh_conf["password"],
            timeout=10
        )
        self.connected = True
        self.sudo_password = ssh_conf.get("sudo_password", ssh_conf.get("password", ""))

    def run_command(self, cmd: str):
        if not self.connected:
            self.connect()
        stdin, stdout, stderr = self.client.exec_command(cmd)
        return stdout.read().decode('utf-8'), stderr.read().decode('utf-8')

    def run_sudo_command(self, cmd: str):
        if not self.connected:
            self.connect()
        sudo_cmd = f"sudo -S -p '' {cmd}"
        stdin, stdout, stderr = self.client.exec_command(sudo_cmd)
        stdin.write(self.sudo_password + "\n")
        stdin.flush()
        return stdout.read().decode('utf-8'), stderr.read().decode('utf-8')

    def get_sftp(self):
        if not self.connected:
            self.connect()
        return self.client.open_sftp()

    def close(self):
        if self.connected:
            self.client.close()
            self.connected = False
    
    def open_shell(self):
        if not self.connected:
            self.connect()
        self.shell = self.client.invoke_shell()
        self.shell.setblocking(0)

    def shell_send(self, command: str):
        if hasattr(self, 'shell'):
            self.shell.send(command + "\n")

    def shell_read(self) -> str:
        if hasattr(self, 'shell') and self.shell.recv_ready():
            return self.shell.recv(4096).decode("utf-8", "ignore")
        return ""