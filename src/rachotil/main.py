"""
Main entry point for the Rachotil application.
"""

from rachotil.backend.components.ssh.config import load_env_config
from rachotil.frontend.app import Rachotil
import sys
import os

def main() -> None:
    """
    Load environment configuration and launch the Textual application.
    """
    load_env_config()
    app = Rachotil()
    app.run()

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("src"), relative_path)

if __name__ == "__main__":
    main()