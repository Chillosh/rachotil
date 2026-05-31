from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Horizontal, Vertical
from textual import work
from ...core.ssh_client import SSHClientWrapper

class DashboardScreen(Screen):
    def __init__(self):
        super().__init__()
        self.ssh = SSHClientWrapper()

    def compose(self):
        yield Header()
        yield Footer()
        
        with Vertical(id="dashboard-main"):
            yield Static("System Dashboard", id="dashboard-title")
            with Horizontal(id="dashboard-content"):
                yield Static("", id="dashboard-ascii", classes="dashboard-box")
                yield Static("Loading system info...", id="dashboard-info", classes="dashboard-box")

    def on_mount(self) -> None:
        ascii_art = """
         ____  _   _ 
        |  _ \\| | | |
        | |_) | | | |
        |  _ <| |_| |
        |_| \\_\\\\___/ 
        
        Ubuntu Server
        """
        self.query_one("#dashboard-ascii", Static).update(ascii_art)
        self.fetch_sys_info()

    @work(thread=True)
    def fetch_sys_info(self):
        cmd = """
        echo "OS: $(grep PRETTY_NAME /etc/os-release | cut -d'=' -f2 | tr -d '\"')"
        echo "Kernel: $(uname -r)"
        echo "Uptime: $(uptime -p)"
        echo "RAM: $(free -m | awk '/Mem:/ {print $3" MB / "$2" MB"}')"
        echo "Disk (/): $(df -h / | awk 'NR==2 {print $3" / "$2" ("$5")"}')"
        echo "Local IP: $(hostname -I | awk '{print $1}')"
        echo "Public IP: $(curl -s ifconfig.me)"
        """
        try:
            out, err = self.ssh.run_command(cmd)
            self.app.call_from_thread(
                lambda: self.query_one("#dashboard-info", Static).update(out.strip())
            )
        except Exception as e:
            self.app.call_from_thread(
                lambda: self.query_one("#dashboard-info", Static).update(f"Error: {str(e)}")
            )