#!/bin/bash
# PaperAssistant - LAN Deployment Script

echo "============================================"
echo "  PaperAssistant - 局域网部署模式"
echo "============================================"
echo ""

# Get LAN IP
if command -v ip &>/dev/null; then
    LAN_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | cut -d/ -f1)
elif command -v ifconfig &>/dev/null; then
    LAN_IP=$(ifconfig | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}')
else
    LAN_IP="<无法检测>"
fi

echo "  本机局域网 IP: $LAN_IP"
echo ""
echo "  启动服务器 (0.0.0.0:8000)..."
echo ""
echo "  其他设备访问: http://$LAN_IP:8000"
echo "  本机访问:     http://127.0.0.1:8000"
echo ""
echo "  Ctrl+C 停止服务器"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Init conda
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif command -v conda &>/dev/null; then
    eval "$(conda shell.bash hook)"
fi

conda run -n paper_assistant python "$SCRIPT_DIR/manage.py" runserver 0.0.0.0:8000
