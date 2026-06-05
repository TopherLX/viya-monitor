DROP TABLE IF EXISTS cd_dws.viya_server_usage_local on cluster clickhouse_cluster sync;

CREATE TABLE IF NOT EXISTS cd_dws.viya_server_usage_local on cluster clickhouse_cluster
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
ENGINE = ReplicatedMergeTree
ORDER BY (hostname, device_name, collected_at)
SETTINGS allow_nullable_key = 1
COMMENT 'Viya服务器存储信息，命令：lsblk -J -p -o NAME,TYPE,SIZE,MOUNTPOINT,FSUSE%';