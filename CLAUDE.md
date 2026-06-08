# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

SAS Viya 存储指标采集 agent，在 Ubuntu 24.04 服务器上每日执行 `lsblk`，将数据写入 ClickHouse。部署在 3 台服务器上（1 master + 2 worker）。

## 常用命令

```bash
uv sync                        # 安装依赖
uv run python -m src.main config.yaml  # 手工执行采集
uv run python -m src.export config.yaml  # 手工执行导出
uv run ruff check src/ --fix   # Lint
uv run ruff format src/        # 格式化
```

## 架构

```
src/main.py          → 入口：读配置 → 遍历 collector → 采集 → 写入 ClickHouse
src/export.py        → 导出：从 ClickHouse 增量查询 → 写 JSON → git push 到 dashboard 仓库
src/config.py        → 加载 config.yaml，自动探测 host_name/IP
src/client.py        → ClickHouse HTTP 客户端（JSONEachRow 格式，含重试/查询）
src/collectors/
  base.py            → CollectResult 数据容器（table_name + rows）
  lsblk.py           → LsblkCollector：执行 lsblk，递归拍平 JSON 树，清洗字段
```

### 数据流（采集）

1. `Config` 加载 `config.yaml`，通过 `hostname` 和 `hostname -I` 自动获取主机标识
2. `main.py` 遍历 collector 列表，每个 collector 返回 `CollectResult(table_name, rows)`
3. `ClickHouseClient.insert()` 给每行注入 `host_name`、`host_ip`、`collected_at`，POST 到 ClickHouse

### 数据流（导出）

1. `export.py` 从 dashboard 仓库 `git pull` 同步最新 JSON
2. 读取现有 JSON，提取 `max(collected_at)`
3. `ClickHouseClient.query()` 执行增量 SELECT（`WHERE collected_at > '{max_ts}'`）
4. 增量数据追加写入 `public/viya_server_usage.json`
5. `git add && git commit && git push` 推送到 `TopherLX/viya-monitor-dashboard`

### ClickHouse 表命名约定

- `lsblk.py` 的 `table_name()` 返回 `"viya_server_usage"`
- `client.py` 硬编码追加 `_all` 后缀 → 最终插入 `viya_server_usage_all`（分布式表）
- `viya_server_usage_all` → Distributed → `viya_server_usage_local`（ReplicatedMergeTree）
- 新增 collector 时，`table_name()` 返回的表名必须遵循此约定（有对应的 `_all` 分布式表）

### 字段清洗

- `parse_size("447.1G")` → 字节数（1024 进制，支持 K/M/G/T/P）
- `parse_pct("43%")` → 浮点数 43.0
- `_flatten()` 将 lsblk JSON 树拍平，过滤 `type="loop"` 设备，`parent_device` 保留父子关系

## 部署

- 服务器时区为 UTC+0，timer 设 `OnCalendar=hourly` 每小时触发一次
- ClickHouse 集群时区为 UTC+8，`collected_at` 直接生成 UTC+8 本地时间（ClickHouse 23.10 不支持 `+00:00` 后缀）
- `host_ip` 过滤 `172.17.12.*` 网段，排除 Docker/VPN 的额外 IP
- `RandomizedDelaySec=300` 避免 3 台同时发送
- 密码通过 `EnvironmentFile=/etc/viya-monitor.env` 注入 systemd，不写入仓库
- `viya-export` 仅在 worker1 上部署，每天 12:10 和 23:10（北京时间）导出数据到 dashboard 仓库

### 采集服务器更新流程

```bash
cd /opt/viya-monitor && git pull
# 仅当 deploy/viya-monitor.service 或 .timer 有变更时才需要：
cp deploy/viya-monitor.service /etc/systemd/system/ && cp deploy/viya-monitor.timer /etc/systemd/system/ && systemctl daemon-reload
# 验证
systemctl start viya-monitor.service && journalctl -u viya-monitor.service --no-pager -n 5
```

仅源码变更时只需 `git pull`，无需 `daemon-reload`。timer 下次触发自动使用最新代码。

### 导出服务器更新流程（仅 worker1）

```bash
cd /opt/viya-monitor && git pull
# 仅当 deploy/viya-export.service 或 .timer 有变更时才需要：
cp deploy/viya-export.service /etc/systemd/system/ && cp deploy/viya-export.timer /etc/systemd/system/ && systemctl daemon-reload
# 验证
systemctl start viya-export.service && journalctl -u viya-export.service --no-pager -n 5
```

## 已知待改进

- 单个 collector 失败会中断后续 collector 的执行。添加第二个 collector 时需在 main.py 的 for 循环内做错误隔离。详见 memory。
