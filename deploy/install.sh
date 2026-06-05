#!/bin/bash
set -euo pipefail

# ============================================================
# Viya Monitor 部署脚本
# 在 Ubuntu 24.04 目标服务器上以 root 执行
# ============================================================

APP_DIR="/opt/viya-monitor"
VENV_DIR="$APP_DIR/.venv"

echo "=== 1/5 安装 uv ==="
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # 确保当前 shell 能找到 uv
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "=== 2/5 同步代码 ==="
# 假设代码已在 /opt/viya-monitor，或通过 git clone 获取
# git clone <repo-url> "$APP_DIR"
mkdir -p "$APP_DIR"

echo "=== 3/5 创建虚拟环境并安装依赖 ==="
cd "$APP_DIR"
uv sync

echo "=== 4/5 安装 systemd timer ==="
cp "$APP_DIR/deploy/viya-monitor.service" /etc/systemd/system/
cp "$APP_DIR/deploy/viya-monitor.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable viya-monitor.timer
systemctl start viya-monitor.timer

echo "=== 5/5 验证 ==="
echo "手动执行一次测试："
"$VENV_DIR/bin/python" -m src.main "$APP_DIR/config.yaml"
echo ""
echo "查看 timer 状态："
systemctl status viya-monitor.timer --no-pager
echo ""
echo "=== 部署完成 ==="
echo "日志查看: journalctl -u viya-monitor.service"
