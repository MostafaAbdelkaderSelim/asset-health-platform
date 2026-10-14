import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

METRICS = [
    "temperature_c", "cpu_pct", "latency_ms",
    "packet_loss_pct", "vibration_mm_s", "load_pct",
]
BASELINE_FRAC = 0.25   # healthy reference window
WINDOW = 10            # rolling window: 10 readings
THRESHOLD = 2.0        # chosen from the stress test (seeds 1-5 and 101-120)

con = duckdb.connect("dbt/asset_health.duckdb", read_only=True)
df = con.execute(
    f"select asset_id, event_ts, {', '.join(METRICS)} "
    "from main.fct_telemetry order by asset_id, event_ts"
).df()
cur = con.execute(
    "select asset_id, client, asset_type, site from main.dim_asset where is_current"
).df()

rows = []
for asset_id, g in df.groupby("asset_id"):
    g = g.reset_index(drop=True)
    n = len(g)
    split = int(n * BASELINE_FRAC)
    best = None
    for m in METRICS:
        base = g[m].iloc[:split]
        mu, sd = base.mean(), base.std()
        if not (np.isfinite(mu) and np.isfinite(sd)) or sd == 0:
            continue
        z = ((g[m].rolling(WINDOW, min_periods=WINDOW // 2).mean() - mu) / sd).to_numpy(copy=True)
        z[:split] = np.nan
        with np.errstate(invalid="ignore"):
            hits = np.flatnonzero(z >= THRESHOLD)
        if len(hits) and (best is None or hits[0] < best["tick"]):
            best = {"tick": int(hits[0]), "metric": m, "z": float(z[hits[0]])}
    rows.append({
        "asset_id": asset_id,
        "status": "alert" if best else "ok",
        "alert_tick": best["tick"] if best else None,
        "alert_ts": g["event_ts"].iloc[best["tick"]] if best else pd.NaT,
        "metric": best["metric"] if best else None,
        "z_at_alert": round(best["z"], 2) if best else None,
        "readings": n,
    })

alerts = pd.DataFrame(rows).merge(cur, on="asset_id", how="left")
alerts = alerts.sort_values(["status", "alert_ts"]).reset_index(drop=True)

out = Path("data/ml")
out.mkdir(parents=True, exist_ok=True)
alerts.to_csv(out / "asset_alerts.csv", index=False)

fired = alerts[alerts.status == "alert"]
print(fired[["asset_id", "client", "asset_type", "metric",
             "alert_tick", "z_at_alert"]].to_string(index=False))
print(f"\nAssets: {len(alerts)} | alerts: {len(fired)} | threshold: {THRESHOLD}")

# evaluation only: the simulator's ground truth is NOT used to compute alerts
truth = json.load(open("data/ground_truth.json", encoding="utf-8"))
alerted = set(fired.asset_id)
print(f"Truly faulty: {len(truth)} | caught: {len(alerted & set(truth))} "
      f"| missed: {len(set(truth) - alerted)} "
      f"| false alarms: {len(alerted - set(truth))}")
