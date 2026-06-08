"""从 ClickHouse 导出数据到 dashboard 仓库。"""
import json
import logging
import subprocess
import sys
from pathlib import Path

from src.client import ClickHouseClient
from src.config import Config

logger = logging.getLogger("viya-monitor.export")

DASHBOARD_REPO = Path("/opt/viya-monitor-dashboard")
REL_PATH = "public/viya_server_usage.json"
GIT_REMOTE = "git@github.com:TopherLX/viya-monitor-dashboard.git"
TABLE = "viya_server_usage"


def _git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=DASHBOARD_REPO, check=True)


def _git_quiet(*args: str) -> bool:
    result = subprocess.run(
        ["git", *args], cwd=DASHBOARD_REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config.yaml")
    config = Config(config_path)
    client = ClickHouseClient(config)

    try:
        if not DASHBOARD_REPO.is_dir():
            logger.error(
                "Dashboard repo not found at %s. Clone it first: git clone %s %s",
                DASHBOARD_REPO, GIT_REMOTE, DASHBOARD_REPO,
            )
            sys.exit(1)

        logger.info("git pull dashboard repo")
        _git("pull", "origin", "main")

        existing = _load_existing()
        max_ts = max((row["collected_at"] for row in existing), default=None)
        logger.info("existing rows: %d, max collected_at: %s", len(existing), max_ts)

        if max_ts:
            sql = (
                f"SELECT * FROM {config.clickhouse_database}.{TABLE}_all "
                f"WHERE collected_at > '{max_ts}' "
                f"ORDER BY collected_at"
            )
        else:
            sql = f"SELECT * FROM {config.clickhouse_database}.{TABLE}_all ORDER BY collected_at"

        logger.info("querying ClickHouse...")
        new_rows = client.query(sql)
        logger.info("got %d new rows", len(new_rows))

        if not new_rows:
            logger.info("no new data, skipping commit")
            return

        all_rows = existing + new_rows
        json_path = DASHBOARD_REPO / REL_PATH
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(all_rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.info("wrote %d rows to %s", len(all_rows), json_path)

        if _git_quiet("diff", "--quiet", "--", REL_PATH):
            logger.info("no changes detected, skipping push")
            return

        _git("add", REL_PATH)
        _git("commit", "-m", f"data: update viya_server_usage ({len(new_rows)} new rows)")
        _git("push", "origin", "main")
        logger.info("pushed to %s", GIT_REMOTE)

    finally:
        client.close()


def _load_existing() -> list[dict]:
    json_path = DASHBOARD_REPO / REL_PATH
    if not json_path.exists():
        return []
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        logger.warning("existing JSON is not a list, treating as empty")
        return []
    except json.JSONDecodeError:
        logger.warning("existing JSON is invalid, treating as empty")
        return []


if __name__ == "__main__":
    main()
