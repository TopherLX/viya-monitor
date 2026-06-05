import logging
import sys
from pathlib import Path

from src.client import ClickHouseClient
from src.collectors.lsblk import LsblkCollector
from src.config import Config

logger = logging.getLogger("viya-monitor")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config.yaml")
    config = Config(config_path)
    logger.info("host=%s ip=%s", config.hostname, config.host_ip)

    collectors = [LsblkCollector()]
    client = ClickHouseClient(config)

    try:
        for collector in collectors:
            result = collector.collect()
            count = client.insert(result)
            logger.info("%s: %d rows inserted", collector.table_name(), count)
    finally:
        client.close()


if __name__ == "__main__":
    main()
