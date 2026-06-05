DROP TABLE IF EXISTS cd_dws.viya_server_usage_local ON CLUSTER clickhouse_cluster SYNC;

CREATE TABLE IF NOT EXISTS cd_dws.viya_server_usage_local ON CLUSTER clickhouse_cluster
(
    host_name      String,
    host_ip        String,
    parent_device  Nullable(String),
    device_name    String,
    device_type    Nullable(String),
    mountpoint     Nullable(String),
    size_bytes     Nullable(UInt64),
    fsuse_pct      Nullable(Float32),
    collected_at   DateTime
)
ENGINE = ReplicatedReplacingMergeTree
PARTITION BY toYYYYMM(collected_at)
ORDER BY (host_name, device_name, toStartOfHour(collected_at))
SETTINGS allow_nullable_key = 1, min_age_to_force_merge_seconds = 21600, min_age_to_force_merge_on_partition_only = 1
COMMENT 'Viya服务器存储信息，命令：lsblk -J -p -o NAME,TYPE,SIZE,MOUNTPOINT,FSUSE%';