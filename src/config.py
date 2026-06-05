import os
import subprocess
from pathlib import Path
from typing import Any

import yaml


def _sh(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    result.check_returncode()
    return result.stdout.strip()


class Config:
    def __init__(self, path: str | Path = "config.yaml"):
        raw = self._load(path)
        self.clickhouse_host: str = raw["clickhouse"].get("host", "10.24.50.13")
        self.clickhouse_port: int = raw["clickhouse"].get("port", 8123)
        self.clickhouse_user: str = raw["clickhouse"].get("user", "cd_user")
        pwd: str = raw["clickhouse"].get("password", "")
        if pwd.startswith("${") and pwd.endswith("}"):
            self.clickhouse_password: str = os.environ.get(pwd[2:-1], "")
        else:
            self.clickhouse_password = pwd
        self.clickhouse_database: str = raw["clickhouse"].get("database", "cd_temp")
        self.host_name: str = _sh("hostname")
        ips = _sh("hostname", "-I").split()
        self.host_ip: str = next((ip for ip in ips if ip.startswith("172.17.12.")), "")

    def _load(self, path: str | Path) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not raw:
            raise ValueError(f"配置文件 {path} 为空或格式错误")
        if "clickhouse" not in raw:
            raise ValueError(f"配置文件 {path} 缺少 clickhouse 配置段")
        return raw
