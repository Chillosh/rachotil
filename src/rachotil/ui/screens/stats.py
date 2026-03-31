from datetime import datetime
from textual import work
from textual.screen import Screen
from textual.widgets import Header, Footer, Log
from ssh.ssh import SSH
from ssh.config import HOST, USER, PASSWORD

items = [
    ["ram+cpu", "top -bn1 | head -n 15", 2],
    ["disk", "df -h", 10],
    ["network", "ip addr show", 10],
    ["processes", "ps aux --sort=-%mem | head -n 10", 10],
    ["services", "systemctl status | head -n 15", 10],
    ["users", "w", 10]
]


class StatsScreen(Screen):
    def compose(self):
        yield Header()
        yield Log(id='output')
        yield Footer()

    def on_mount(self):
        self.ssh_connect = SSH(HOST, USER, PASSWORD)
        self.stats_data = {item[0]: "" for item in items}

        log = self.query_one('#output', Log)
        log.auto_scroll = False

        try:
            self.ssh_connect.connect()
            self.set_interval(1, self.refresh_screen)
            for label, command, interval in items:
                self.set_interval(interval, lambda cmd=command, lbl=label: self.run_stats_command(cmd, lbl))
                self.run_stats_command(command, label)
        except Exception as e:
            log.write_line(f"Error: {e}")

    @work(thread=True)
    def run_stats_command(self, command, label):
        try:
            out, err = self.ssh_connect.run_command(command)
            if out:
                self.stats_data[label] = out.strip()
            elif err:
                self.stats_data[label] = err.strip()
        except Exception as e:
            self.stats_data[label] = f"Error: {e}"

    def refresh_screen(self):
        log = self.query_one('#output', Log)
        pos = log.scroll_y
        log.clear()

        cas = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[{cas}] SERVER STATS\n" + "=" * 40)

        for label, command, interval in items:
            if self.stats_data[label]:
                log.write_line(f"\n--- {label.upper()} ---")
                log.write_line(self.stats_data[label])

        log.scroll_y = pos

    def on_unmount(self):
        if hasattr(self, 'ssh_connect'):
            self.ssh_connect.close()