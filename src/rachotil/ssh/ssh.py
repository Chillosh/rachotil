import paramiko

class SSH:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.shell = None

    def connect(self):
        self.client.connect(
            hostname=self.host,
            username=self.user,
            password=self.password,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )

    def run_command(self, command, get_pty=False):
        stdin, stdout, stderr = self.client.exec_command(command, get_pty=get_pty)
        if get_pty:
            stdout.channel.recv_exit_status()
        return stdout.read().decode(), stderr.read().decode()

    def open_shell(self):
        self.shell = self.client.invoke_shell(width=120, height=40)
        self.shell.settimeout(0.0)
        return self.shell

    def shell_send(self, command):
        if self.shell is None:
            self.open_shell()
        self.shell.send(command.rstrip("\n") + "\n")

    def shell_read(self):
        if self.shell is None:
            return ""

        output = []
        while self.shell.recv_ready():
            output.append(self.shell.recv(4096).decode(errors="ignore"))
        while self.shell.recv_stderr_ready():
            output.append(self.shell.recv_stderr(4096).decode(errors="ignore"))
        return "".join(output)

    def close(self):
        if self.shell is not None:
            self.shell.close()
            self.shell = None
        self.client.close()