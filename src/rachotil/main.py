from ssh.config import load_env_config
from ui.app import Rachotil

def main() -> None:
    load_env_config()
    app = Rachotil()
    app.run()

if __name__ == "__main__":
    main()