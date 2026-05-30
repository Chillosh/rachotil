from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Vertical, Horizontal
from textual import work
from ...core.ssh_client import SSHClientWrapper
from ...storage.config_store import ConfigStore

class StatsScreen(Screen):
    def __init__(self):
        super().__init__()
        self.ssh = SSHClientWrapper()
        self.db = ConfigStore()
        self.timers = []

    def compose(self):
        yield Header()
        yield Footer()
        with Vertical(id="stats-main"):
            yield Static("Live Stats Monitoring", id="stats-title")
            yield Vertical(id="stats-container")

    def on_mount(self) -> None:
        container = self.query_one("#stats-container", Vertical)
        stats_data = self.db.get("stats", {"blocks": []})
        blocks = stats_data.get("blocks", [])

        active_blocks = [b for b in blocks if b.get("enabled", False)]
        
        if not active_blocks:
            container.mount(Static("No stat blocks enabled. Go to Settings.", classes="stats-box"))
            return

        for block in active_blocks:
            widget_id = f"stat-{block['id']}"
            box = Static(f"{block['label']}\nLoading...", id=widget_id, classes="stats-box")
            container.mount(box)
            
            t = self.set_interval(
                block.get("interval_seconds", 5), 
                lambda b=block, wid=widget_id: self.update_block(b, wid)
            )
            self.timers.append(t)
            self.update_block(block, widget_id)

    @work(thread=True)
    def update_block(self, block: dict, widget_id: str) -> None:
        try:
            out, err = self.ssh.run_command(block["command"])
            result = out.strip() if out.strip() else err.strip()
            display_text = f"[bold]{block['label']}[/bold]\n{result}"
            self.app.call_from_thread(lambda: self.query_one(f"#{widget_id}", Static).update(display_text))
        except Exception as e:
            self.app.call_from_thread(lambda: self.query_one(f"#{widget_id}", Static).update(f"[bold]{block['label']}[/bold]\nError: {e}"))

    def on_unmount(self) -> None:
        for t in self.timers:
            t.stop()