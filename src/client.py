import json
import logging
import time
from datetime import datetime, timedelta, timezone

import httpx

from src.collectors.base import CollectResult
from src.config import Config

logger = logging.getLogger("viya-monitor")
_CH_TZ = timezone(timedelta(hours=8))

class ClickHouseClient:
    def __init__(self, config: Config):
        self._base_url = f"http://{config.clickhouse_host}:{config.clickhouse_port}"
        self._auth = (config.clickhouse_user, config.clickhouse_password)
        self._database = config.clickhouse_database
        self._hostname = config.hostname
        self._host_ip = config.host_ip
        self._client = httpx.Client(timeout=30)

    def insert(self, result: CollectResult) -> int:
        """写入 ClickHouse，返回写入行数。"""
        if not result.rows:
            return 0
        now = datetime.now(_CH_TZ).strftime("%Y-%m-%d %H:%M:%S")
        for row in result.rows:
            row.setdefault("hostname", self._hostname)
            row.setdefault("host_ip", self._host_ip)
            row.setdefault("collected_at", now)
        lines = "\n".join(json.dumps(row, ensure_ascii=False) for row in result.rows)
        url = f"{self._base_url}/"
        params = {
            "query": f"INSERT INTO {self._database}.{result.table_name}_all FORMAT JSONEachRow",
        }
        for attempt in range(1, 4):
            try:
                resp = self._client.post(
                    url, params=params, content=lines, auth=self._auth
                )
                resp.raise_for_status()
                return len(result.rows)
            except httpx.HTTPError as e:
                if attempt == 3:
                    raise
                logger.warning("insert attempt %d/3 failed: %s", attempt, e)
                time.sleep(5)
        return 0

    def close(self) -> None:
        self._client.close()
