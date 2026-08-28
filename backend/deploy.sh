#!/bin/bash
# Deployment script for Oracle Cloud Free Tier
# Usage: bash deploy.sh

set -e

echo "🚀 Setting up Qur-aan App on Oracle Cloud..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv libgl1-mesa-glx libglib2.0-0

# Create virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install CPU-only PyTorch (saves ~1GB RAM)
echo "🤖 Installing CPU-only PyTorch..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/qur-aan-app.service > /dev/null <<EOF
[Unit]
Description=Quranic App Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 80
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "▶️ Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable qur-aan-app
sudo systemctl start qur-aan-app

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Your app is running at:"
echo "   - API: http://$(curl -s ifconfig.me)/api/v1/health"
echo "   - Health: http://$(curl -s ifconfig.me)/api/v1/health"
echo ""
echo "🔧 Useful commands:"
echo "   - Check status: sudo systemctl status qur-aan-app"
echo "   - View logs: sudo journalctl -u qur-aan-app -f"
echo "   - Restart: sudo systemctl restart qur-aan-app"
echo "   - Stop: sudo systemctl stop qur-aan-app"
echo ""
echo "📌 Next steps:"
echo "   1. Open port 80 in Oracle Cloud firewall"
echo "   2. Update web app API URL with your public IP"
echo "   3. Access web app at https://qur-aan-app.pages.dev"
