#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# ─── KHOKHO BL3 BOT — VPS Setup Script (Ubuntu 22.04)
# ═══════════════════════════════════════════════════════════════════
set -e

echo "🚀 Installing Khokho Bl3 Bot..."

# System deps
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip git \
                   libjpeg-dev zlib1g-dev fonts-dejavu-core

# Create user
useradd -m -s /bin/bash botuser || true

# Clone
cd /opt
git clone https://github.com/youruser/khokho-bl3.git || true
chown -R botuser:botuser /opt/khokho-bl3
cd /opt/khokho-bl3

# Venv
sudo -u botuser python3.11 -m venv venv
sudo -u botuser venv/bin/pip install --upgrade pip
sudo -u botuser venv/bin/pip install -r requirements.txt

# Env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Edit /opt/khokho-bl3/.env w 3ammer DISCORD_TOKEN!"
fi

# Logs
mkdir -p /var/log/khokho
chown -R botuser:botuser /var/log/khokho

# Systemd
cp deploy/khokho.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable khokho
systemctl start khokho

echo "✅ Done! Check: systemctl status khokho"
echo "📋 Logs: journalctl -u khokho -f"