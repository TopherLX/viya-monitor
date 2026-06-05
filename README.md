# viya-monitor

SAS Viya 服务器存储指标采集 agent，每日执行 `lsblk` 并上报至 ClickHouse。

## 部署

```bash
# 1. 拉取代码
git clone https://github.com/TopherLX/viya-monitor.git /opt/viya-monitor
cd /opt/viya-monitor

# 2. 安装依赖（需先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh）
uv sync

# 3. 创建密码文件
echo 'CH_PASSWORD=your-password' > /etc/viya-monitor.env

# 4. 手工执行验证
export CH_PASSWORD='your-password'
uv run python -m src.main config.yaml

# 5. 安装 systemd timer（北京时间 00:00 触发）
cp deploy/viya-monitor.service /etc/systemd/system/
cp deploy/viya-monitor.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now viya-monitor.timer

# 6. 确认状态
systemctl status viya-monitor.timer
```

## 日志

```bash
journalctl -u viya-monitor.service
```
