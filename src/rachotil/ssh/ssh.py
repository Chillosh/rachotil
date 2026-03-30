import paramiko

class SSH:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.client.connect(
            hostname=self.host,
            username=self.user,
            password=self.password,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )

    def run_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()

    def close(self):
        self.client.close()