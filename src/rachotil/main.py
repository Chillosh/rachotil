"""
Main entry point for the Rachotil application.
"""

from .backend.components.ssh.config import load_env_config
from .frontend.app import Rachotil

def main() -> None:
    """
    Load environment configuration and launch the Textual application.
    """
    load_env_config()
    app = Rachotil()
    app.run()

if __name__ == "__main__":
    main()