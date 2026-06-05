import json
import re
import subprocess
from typing import Any

from src.collectors.base import CollectResult

_SIZE_UNITS = {"K": 1, "M": 2, "G": 3, "T": 4, "P": 5}


def parse_size(raw: str | None) -> int | None:
    """将 lsblk 的 SIZE 字段转换为字节数。支持 "49.3M", "447.1G", "1.7T" 等格式。"""
    if raw is None or raw == "":
        return None
    match = re.match(r"^([\d.]+)\s*([KMGTP])?$", raw.strip().upper())
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit is None:
        return int(value)
    return int(value * (1024 ** _SIZE_UNITS[unit]))


def parse_pct(raw: str | None) -> float | None:
    """将 lsblk 的 FSUSE% 字段转换为浮点数。支持 "43%", "100%", "1%" 等格式。"""
    if raw is None or raw == "":
        return None
    match = re.match(r"^([\d.]+)\s*%?$", str(raw).strip())
    if not match:
        return None
    return float(match.group(1))


def _flatten(node: dict[str, Any], parent: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if node.get("type") == "loop":
        return []
    rows: list[dict[str, Any]] = []
    rows.append({
        "device_name": node["name"],
        "device_type": node["type"],
        "size_bytes": parse_size(node.get("size")),
        "mountpoint": node.get("mountpoint") or None,
        "fsuse_pct": parse_pct(node.get("fsuse%")),
        "parent_device": parent["name"] if parent else None,
    })
    for child in node.get("children", []):
        rows.extend(_flatten(child, parent=node))
    return rows


class LsblkCollector:
    def table_name(self) -> str:
        return "viya_server_usage"

    def collect(self) -> CollectResult:
        result = subprocess.run(
            ["lsblk", "-J", "-p", "-o", "NAME,TYPE,SIZE,MOUNTPOINT,FSUSE%"],
            capture_output=True, text=True, timeout=30,
        )
        result.check_returncode()
        data = json.loads(result.stdout)
        rows: list[dict[str, Any]] = []
        for device in data.get("blockdevices", []):
            rows.extend(_flatten(device))
        return CollectResult(table_name=self.table_name(), rows=rows)
