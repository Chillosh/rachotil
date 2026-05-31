"""
Screen for displaying real-time system statistics from the remote server.
"""

from datetime import datetime
from textual import work
from textual.screen import Screen
from textual.widgets import Footer, Header, Log

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.stats.config import get_enabled_stats_blocks
from ...backend.components.stats.stats_manager import StatsManager


class StatsScreen(Screen):
    """
    UI Screen that periodically refreshes and displays various system metrics.
    """
    def compose(self) -> None:
        yield Header()
        yield Log(id="output")
        yield Footer()

    def on_mount(self) -> None:
        config = get_ssh_config()
        self.ssh_connect = SSH(
            config["host"],
            config["user"],
            config["password"],
            config.get("sudo_password"),
        )
        self.blocks = get_enabled_stats_blocks()
        self.stats_data = {block["id"]: "" for block in self.blocks}

        log = self.query_one("#output", Log)
        log.auto_scroll = False

        if not self.blocks:
            log.write_line("No stat blocks are enabled. Open Settings -> Stats Configuration.")
            return

        try:
            self.ssh_connect.connect()
            self.stats_mgr = StatsManager(self.ssh_connect)
            
            self.set_interval(1, self.refresh_screen)
            for block in self.blocks:
                self.set_interval(
                    block["interval_seconds"],
                    lambda b=block: self.run_stats_command(b["command"], b["id"]),
                )
                self.run_stats_command(block["command"], block["id"])
        except Exception as e:
            log.write_line(f"Error: {e}")

    @work(thread=True)
    def run_stats_command(self, command: str, block_id: str) -> None:
        """
        Execute a statistics command on the server in a background thread.
        """
        if hasattr(self, "stats_mgr"):
            result = self.stats_mgr.fetch_stat(command)
            self.stats_data[block_id] = result

    def refresh_screen(self) -> None:
        """
        Update the log widget with the latest collected statistics data.
        """
        log = self.query_one("#output", Log)
        pos = log.scroll_y
        log.clear()

        cas = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[{cas}] SERVER STATS\n" + "=" * 40)

        for block in self.blocks:
            block_id = block["id"]
            if self.stats_data.get(block_id):
                log.write_line(f"\n--- {block['label'].upper()} ---")
                log.write_line(self.stats_data[block_id])

        log.scroll_y = pos

    def on_unmount(self) -> None:
        if hasattr(self, "ssh_connect"):
            self.ssh_connect.close()