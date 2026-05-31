from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Horizontal, Vertical
from textual import work
from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH

class DashboardScreen(Screen):
    CSS_PATH = "../styles.tcss"

    def __init__(self):
        super().__init__()
        self.ssh = None

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
        
        try:
            config = get_ssh_config()
            self.ssh = SSH(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                sudo_password=config.get("sudo_password")
            )
            self.ssh.connect()
            self.fetch_sys_info()
        except Exception as e:
            self.query_one("#dashboard-info", Static).update(f"Connection failed: {str(e)}")

    @work(thread=True)
    def fetch_sys_info(self):
        if not self.ssh:
            return
            
        cmd = """
        echo "OS: $(grep PRETTY_NAME /etc/os-release | cut -d'=' -f2 | tr -d '\"')"
        echo "Kernel: $(uname -r)"
        echo "Uptime: $(uptime -p)"
        echo "RAM: $(free -m | awk '/Mem:/ {print $3" MB / "$2" MB"}')"
        echo "Disk (/): $(df -h / | awk 'NR==2 {print $3" / "$2" ("$5")"}')"
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