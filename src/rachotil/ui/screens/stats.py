from datetime import datetime
from textual import work
from textual.screen import Screen
from textual.widgets import Footer, Header, Log
from ssh.config import get_ssh_config
from ssh.ssh import SSH
from stats.config import get_enabled_stats_blocks


class StatsScreen(Screen):
    def compose(self):
        yield Header()
        yield Log(id="output")
        yield Footer()

    def on_mount(self):
        config = get_ssh_config()
        self.ssh_connect = SSH(config["host"], config["user"], config["password"])
        self.blocks = get_enabled_stats_blocks()
        self.stats_data = {block["id"]: "" for block in self.blocks}

        log = self.query_one("#output", Log)
        log.auto_scroll = False

        if not self.blocks:
            log.write_line("No stat blocks are enabled. Open Settings -> Stats Configuration.")
            return

        try:
            self.ssh_connect.connect()
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
    def run_stats_command(self, command, block_id):
        try:
            out, err = self.ssh_connect.run_command(command)
            if out:
                self.stats_data[block_id] = out.strip()
            elif err:
                self.stats_data[block_id] = err.strip()
        except Exception as e:
            self.stats_data[block_id] = f"Error: {e}"

    def refresh_screen(self):
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

    def on_unmount(self):
        if hasattr(self, "ssh_connect"):
            self.ssh_connect.close()

