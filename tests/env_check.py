import os

import duckdb

# 1) Can DuckDB on Linux read our Silver Delta table?
con = duckdb.connect()
try:
    con.execute("INSTALL delta; LOAD delta;")
    n = con.execute(
        "select count(*) from delta_scan('data/lake/silver/telemetry')"
    ).fetchone()[0]
    print(f"[1] delta_scan on Linux: OK, {n} rows")
except Exception as e:
    print(f"[1] delta_scan on Linux: FAILED -> {str(e)[:300]}")

# 2) Can DuckDB write its file on the Windows bind mount?
path = "data/_lock_test.duckdb"
try:
    c2 = duckdb.connect(path)
    c2.execute("create table t as select 1 as x")
    c2.close()
    c3 = duckdb.connect(path, read_only=True)
    print(f"[2] write + reopen on bind mount: OK, {c3.execute('select * from t').fetchone()}")
    c3.close()
except Exception as e:
    print(f"[2] write on bind mount: FAILED -> {str(e)[:300]}")
finally:
    if os.path.exists(path):
        os.remove(path)
