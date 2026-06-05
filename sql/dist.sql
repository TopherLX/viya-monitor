DROP TABLE IF EXISTS cd_dws.viya_server_usage_all ON CLUSTER clickhouse_cluster SYNC;

CREATE TABLE IF NOT EXISTS cd_dws.viya_server_usage_all ON CLUSTER clickhouse_cluster
    AS cd_dws.viya_server_usage_local
ENGINE = Distributed('clickhouse_cluster', 'cd_dws', 'viya_server_usage_local', cityHash64(host_name, device_name))
COMMENT 'Viya服务器存储信息，命令：lsblk -J -p -o NAME,TYPE,SIZE,MOUNTPOINT,FSUSE%';