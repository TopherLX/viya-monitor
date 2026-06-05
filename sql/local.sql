DROP TABLE IF EXISTS cd_dws.viya_server_usage_local ON CLUSTER clickhouse_cluster SYNC;

CREATE TABLE IF NOT EXISTS cd_dws.viya_server_usage_local ON CLUSTER clickhouse_cluster
(
    hostname       Nullable(String),
    host_ip        Nullable(String),
    collected_at   Nullable(DateTime),
    device_name    Nullable(String),
    device_type    Nullable(String),
    size_bytes     Nullable(UInt64),
    mountpoint     Nullable(String),
    fsuse_pct      Nullable(Float32),
    parent_device  Nullable(String)
)
ENGINE = ReplicatedReplacingMergeTree
PARTITION BY toYYYYMM(collected_at)
ORDER BY (hostname, device_name, toYYYYMMDD(collected_at))
SETTINGS allow_nullable_key = 1, min_age_to_force_merge_seconds = 21600, min_age_to_force_merge_on_partition_only = 1
COMMENT 'Viya服务器存储信息，命令：lsblk -J -p -o NAME,TYPE,SIZE,MOUNTPOINT,FSUSE%';