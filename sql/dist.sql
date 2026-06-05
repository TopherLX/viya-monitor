DROP TABLE IF EXISTS cd_dws.viya_server_usage_all on cluster clickhouse_cluster sync;

CREATE TABLE IF NOT EXISTS cd_dws.viya_server_usage_all on cluster clickhouse_cluster
    as cd_dws.viya_server_usage_local
ENGINE = Distributed('clickhouse_cluster', 'cd_dws', 'viya_server_usage_local', rand())
;