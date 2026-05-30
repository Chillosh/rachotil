#!/bin/bash
set -e

echo "======================================"
echo " Starting Rachotil Server Setup..."
echo "======================================"

if [ "$EUID" -eq 0 ]; then
  echo "Please do not run this script directly as root. Run it as your normal user."
  exit 1
fi

echo "[1/5] Updating system repositories..."
sudo apt update && sudo apt upgrade -y

echo "[2/5] Installing core dependencies..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    curl \
    wget \
    ufw \
    timeshift \
    rsync \
    docker.io \
    wireguard \
    wireguard-tools \
    qrencode \
    htop \
    tree

echo "[3/5] Setting up Python Virtual Environment..."
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
echo "[4/5] Installing Python libraries..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[5/5] Creating global 'rachotil' command..."
LAUNCHER_PATH="$(pwd)/rachotil-launcher.sh"

cat << EOF > "$LAUNCHER_PATH"
#!/bin/bash
cd "$(pwd)"
source venv/bin/activate
export PYTHONPATH="$(pwd)/src"
python3 src/rachotil/main.py
EOF

chmod +x "$LAUNCHER_PATH"
sudo ln -sf "$LAUNCHER_PATH" /usr/local/bin/rachotil

sudo usermod -aG docker $USER

echo "======================================"
echo " Installation Complete!"
echo " Please log out and log back in for Docker permissions to apply."
echo " You can now start the app anytime by typing: rachotil"
echo "======================================"