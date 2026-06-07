"""
Native text editor modal for editing remote files.
"""

from textual.screen import ModalScreen
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal
from textual import on, work
from pathlib import Path

class EditorModal(ModalScreen):
    CSS = """
    EditorModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #editor-modal-container {
        width: 90%;
        height: 90%;
        border: solid cyan;
        background: $surface;
        padding: 1;
    }
    #editor-title {
        text-style: bold;
        color: cyan;
        margin-bottom: 1;
    }
    #file-editor {
        height: 1fr;
        margin-bottom: 1;
    }
    #editor-actions {
        height: 3;
        align: right middle;
    }
    #editor-actions Button {
        margin-left: 1;
    }
    """

    def __init__(self, filepath: str, initial_content: str, file_mgr):
        super().__init__()
        self.filepath = filepath
        self.initial_content = initial_content
        self.file_mgr = file_mgr 
        
        ext = Path(filepath).suffix.lower()
        self.language = "text"
        if ext in [".py"]: self.language = "python"
        elif ext in [".json"]: self.language = "json"
        elif ext in [".yml", ".yaml"]: self.language = "yaml"
        elif ext in [".html", ".htm"]: self.language = "html"
        elif ext in [".css", ".tcss"]: self.language = "css"
        elif ext in [".js"]: self.language = "javascript"
        elif ext in [".sh", ".bash"]: self.language = "bash"

    def compose(self) -> None:
        with Vertical(id="editor-modal-container"):
            yield Static(f"Editing: {self.filepath}", id="editor-title")
            yield TextArea(text=self.initial_content, language=self.language, id="file-editor")
            
            with Horizontal(id="editor-actions"):
                yield Button("Save", id="btn-save-file", variant="success")
                yield Button("Cancel", id="btn-cancel-edit", variant="error")

    @on(Button.Pressed, "#btn-save-file")
    def save_file(self) -> None:
        content = self.query_one("#file-editor", TextArea).text
        self.query_one("#editor-title", Static).update(f"Saving {self.filepath}...")
        self.execute_save(content)

    @work(thread=True)
    def execute_save(self, content: str) -> None:
        success, msg = self.file_mgr.save_file(self.filepath, content)
        if success:
            self.app.call_from_thread(self.app.pop_screen)
        else:
            self.app.call_from_thread(lambda: self.query_one("#editor-title", Static).update(f"[red]Error:[/red] {msg}"))

    @on(Button.Pressed, "#btn-cancel-edit")
    def cancel_edit(self) -> None:
        self.app.pop_screen()