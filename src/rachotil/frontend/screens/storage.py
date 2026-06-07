"""
Screen for managing disks, partitions, and LVM volumes.
"""

from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Log
from textual.containers import Vertical, Horizontal
from textual import work

from ...backend.components.ssh.config import get_ssh_config
from ...backend.components.ssh.ssh import SSH
from ...backend.components.storage.storage_manager import StorageManager

class StorageScreen(Screen):
    """UI Screen for storage monitoring and formatting."""
    
    CSS_PATH = ["../components/styles/global.tcss", "../components/styles/storage.tcss"]

    def __init__(self):
        super().__init__()
        self.ssh = None
        self.storage_mgr = None

    def compose(self) -> None:
        yield Header()
        yield Footer()

        with Vertical(id="storage-main"):
            yield Static("Disk & Partition Manager", id="storage-title")
            yield DataTable(id="storage-table", cursor_type="row")
            
            with Horizontal(id="storage-actions"):
                yield Button("Refresh", id="btn-refresh-storage", variant="default")
                yield Button("Format to EXT4", id="btn-format-disk", variant="warning", disabled=True)
                yield Button("Create LVM Volume", id="btn-create-lvm", variant="success", disabled=True)
                
            yield Log(id="storage-log", classes="status-display")

    def on_mount(self) -> None:
        table = self.query_one("#storage-table", DataTable)
        table.add_columns("Device Name", "Type", "Size", "File System", "Mountpoint")
        self.connect_and_load()

    @work(thread=True)
    def connect_and_load(self) -> None:
        self.write_log("Connecting to server to map storage devices...")
        try:
            config = get_ssh_config()
            self.ssh = SSH(config["host"], config["user"], config["password"], config.get("sudo_password"))
            self.ssh.connect()
            self.storage_mgr = StorageManager(self.ssh)
            self.load_devices()
        except Exception as e:
            self.write_log(f"Connection failed: {str(e)}")

    def load_devices(self) -> None:
        if not self.storage_mgr: return
        self.write_log("Fetching block devices...")
        
        success, result = self.storage_mgr.get_devices()
        if success:
            self.app.call_from_thread(self._update_table, result)
            self.write_log("Storage list updated.")
        else:
            self.write_log(f"Error: {result}")

    def _update_table(self, devices: list) -> None:
        table = self.query_one("#storage-table", DataTable)
        table.clear()
        
        def add_device_to_table(dev, prefix=""):
            name = f"{prefix} {dev.get('name', '')}"
            dtype = dev.get("type", "")
            size = dev.get("size", "")
            fstype = dev.get("fstype", "") or "-"
            mount = dev.get("mountpoint", "") or "-"
            
            if dtype == "disk": name = f"[bold green]{name}[/bold green]"
            elif dtype == "lvm": name = f"[bold yellow]{name}[/bold yellow]"
            
            table.add_row(name, dtype, size, fstype, mount, key=dev.get('name', ''))
            
            if "children" in dev:
                for child in dev["children"]:
                    add_device_to_table(child, prefix + " └─")

        for d in devices:
            add_device_to_table(d)

    def write_log(self, message: str) -> None:
        try:
            log_widget = self.query_one("#storage-log", Log)
            self.app.call_from_thread(log_widget.write_line, message)
        except: pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-storage":
            self.app.run_worker(self.load_devices, thread=True)