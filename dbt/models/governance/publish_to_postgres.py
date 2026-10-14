import os

import duckdb
from dotenv import load_dotenv

load_dotenv()

PW = os.environ["PG_ADMIN_PASSWORD"]
PG_CONN = (
    "host=localhost port=5433 dbname=assethealth "
    f"user=admin password={PW}"
)

# (schema, table, query)
PUBLISH = [
    ("gold", "dim_asset",
     "select * from asset_health.main.dim_asset"),
    ("gold", "fct_telemetry",
     "select f.*, a.client from asset_health.main.fct_telemetry f "
     "join asset_health.main.dim_asset a using (asset_key)"),
    ("gold", "fct_asset_health_5min",
     "select f.*, a.client from asset_health.main.fct_asset_health_5min f "
     "join asset_health.main.dim_asset a using (asset_key)"),
    ("masked", "dim_asset_owner_masked",
     "select * from asset_health.main.dim_asset_owner_masked"),
    ("restricted", "asset_owner_restricted",
     "select * from asset_health.main_restricted.asset_owner_restricted"),
]

con = duckdb.connect()  # in-memory: كل database بتتوصّل بوضعها الخاص
con.execute("ATTACH 'dbt/asset_health.duckdb' AS asset_health (READ_ONLY)")
con.execute("INSTALL postgres; LOAD postgres;")

try:
    con.execute(f"ATTACH '{PG_CONN}' AS pg (TYPE postgres)")
except duckdb.IOException as e:
    raise SystemExit("Cannot connect to Postgres: " + str(e).replace(PW, "***"))

for schema in sorted({s for s, _, _ in PUBLISH}):
    con.execute(f"CREATE SCHEMA IF NOT EXISTS pg.{schema}")

for schema, table, query in PUBLISH:
    con.execute(f"DROP TABLE IF EXISTS pg.{schema}.{table}")
    con.execute(f"CREATE TABLE pg.{schema}.{table} AS {query}")
    n = con.execute(f"select count(*) from pg.{schema}.{table}").fetchone()[0]
    print(f"{schema}.{table}: {n} rows")