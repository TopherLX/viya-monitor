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

## 更新

```bash
cd /opt/viya-monitor
git pull
uv sync                       # 仅依赖变更时需要

# 如果 deploy/viya-monitor.service 或 .timer 有变更：
cp deploy/viya-monitor.service /etc/systemd/system/
cp deploy/viya-monitor.timer /etc/systemd/system/
systemctl daemon-reload        # 重新加载 systemd 配置，不影响运行中的服务

# 验证
systemctl start viya-monitor.service
journalctl -u viya-monitor.service --no-pager -n 5
```

## 导出（仅 worker1）

将 ClickHouse 数据导出到 [viya-monitor-dashboard](https://github.com/TopherLX/viya-monitor-dashboard)，供 GitHub Pages 部署。

### 首次部署

```bash
# 1. 克隆 dashboard 仓库
git clone git@github.com:TopherLX/viya-monitor-dashboard.git /opt/viya-monitor-dashboard

# 2. 安装 timer（每天 12:10 和 23:10 触发）
cp deploy/viya-export.service /etc/systemd/system/
cp deploy/viya-export.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now viya-export.timer

# 3. 验证
systemctl start viya-export.service
journalctl -u viya-export.service --no-pager -n 10
```

### 更新

```bash
cd /opt/viya-monitor && git pull
# 如果 deploy/viya-export.service 或 .timer 有变更：
cp deploy/viya-export.service /etc/systemd/system/
cp deploy/viya-export.timer /etc/systemd/system/
systemctl daemon-reload
```

## 日志

```bash
journalctl -u viya-monitor.service
```
