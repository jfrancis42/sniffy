#!/bin/bash
set -e

# Self-contained quantum-sniffer persistent monitoring installer
# Creates isolated venv, installs package with dependencies, sets up systemd service

INSTALL_DIR="/opt/quantum-sniffer"
LOG_DIR="/var/log/quantum-sniffer"
STAGING_DIR="/tmp/quantum-sniffer-deploy"

echo "=== Installing Quantum Sniffer Persistent Monitor ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Must run as root (use sudo)"
    exit 1
fi

# Check staging directory exists
if [ ! -d "$STAGING_DIR" ]; then
    echo "Error: Staging directory $STAGING_DIR not found"
    exit 1
fi

# Detect interface
INTERFACE=$(ip route show default | awk '/default/ {print $5; exit}' 2>/dev/null || echo "eth0")
echo "Network interface: $INTERFACE"

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Create venv
echo "Creating isolated Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"

# Upgrade pip
echo "Upgrading pip..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip setuptools wheel >/dev/null 2>&1

# Copy source to installation directory for editable install
echo "Copying source files..."
mkdir -p "$INSTALL_DIR/src"
cp -r "$STAGING_DIR"/* "$INSTALL_DIR/src/"

# Install quantum-sniffer package from installation directory
echo "Installing quantum-sniffer package with dependencies..."
cd "$INSTALL_DIR/src"
"$INSTALL_DIR/venv/bin/pip" install -e . >/dev/null 2>&1

# Verify installation
if ! "$INSTALL_DIR/venv/bin/quantum-sniffer" --help >/dev/null 2>&1; then
    echo "Error: quantum-sniffer installation failed"
    exit 1
fi

# persistent-monitor.py is already copied with the source files
chmod +x "$INSTALL_DIR/src/persistent-monitor.py"
ln -sf "$INSTALL_DIR/src/persistent-monitor.py" "$INSTALL_DIR/persistent-monitor.py"

# Create log directory
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Install systemd service
echo "Installing systemd service..."
cat > /etc/systemd/system/quantum-sniffer-monitor@.service << 'SERVICEEOF'
[Unit]
Description=Quantum Sniffer Persistent PQC Monitor
Documentation=https://github.com/illumio-community/quantum-sniffer
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/opt/quantum-sniffer/venv/bin/python3 /opt/quantum-sniffer/persistent-monitor.py --interface %i --output-dir /var/log/quantum-sniffer
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/quantum-sniffer

# Capabilities needed for packet capture
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN
CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable "quantum-sniffer-monitor@$INTERFACE"
systemctl restart "quantum-sniffer-monitor@$INTERFACE"

# Wait and check status
sleep 3
if systemctl is-active --quiet "quantum-sniffer-monitor@$INTERFACE"; then
    echo "✓ Quantum Sniffer installed and running"
    echo "  Service: quantum-sniffer-monitor@$INTERFACE"
    echo "  Logs: $LOG_DIR"
    echo "  Interface: $INTERFACE"
    echo "  Command: $INSTALL_DIR/venv/bin/quantum-sniffer"
else
    echo "✗ Service failed to start"
    systemctl status "quantum-sniffer-monitor@$INTERFACE" --no-pager -l
    exit 1
fi
