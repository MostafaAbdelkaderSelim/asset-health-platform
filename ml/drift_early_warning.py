import json

import duckdb
import numpy as np
import pandas as pd

METRICS = [
    "temperature_c", "cpu_pct", "latency_ms",
    "packet_loss_pct", "vibration_mm_s", "load_pct",
]
BASELINE_FRAC = 0.25   # healthy reference window (first 25% of readings)
WINDOW = 10            # rolling window: 10 readings (~100 seconds)
THRESHOLD = 3.0
STEP_SECONDS = 10

con = duckdb.connect("dbt/asset_health.duckdb", read_only=True)
df = con.execute(
    f"select asset_id, event_ts, {', '.join(METRICS)} "
    "from main.fct_telemetry order by asset_id, event_ts"
).df()
types = con.execute("select distinct asset_id, asset_type from main.dim_asset").df()
truth = json.load(open("data/ground_truth.json", encoding="utf-8"))  # asset_id -> fault start tick

rows = []
for asset_id, g in df.groupby("asset_id"):
    g = g.reset_index(drop=True)
    n = len(g)
    split = int(n * BASELINE_FRAC)
    base = g.iloc[:split]
    best = None
    for m in METRICS:
        mu, sd = base[m].mean(), base[m].std()
        if not np.isfinite(sd) or sd == 0:
            continue
        roll = g[m].rolling(WINDOW, min_periods=WINDOW // 2).mean()
        z = ((roll - mu) / sd).to_numpy()
        mask = (z >= THRESHOLD) & (np.arange(n) >= split)
        hits = np.flatnonzero(mask)
        if len(hits) and (best is None or hits[0] < best[0]):
            best = (int(hits[0]), m)
    rows.append({
        "asset_id": asset_id,
        "alert_tick": best[0] if best else None,
        "metric": best[1] if best else None,
        "true_start": truth.get(asset_id),
    })

res = pd.DataFrame(rows).merge(types, on="asset_id")
res["is_faulty"] = res["true_start"].notna()
faulty = res[res.is_faulty].copy()
healthy = res[~res.is_faulty]

faulty["delay_ticks"] = faulty["alert_tick"] - faulty["true_start"]
faulty["delay_min"] = (faulty["delay_ticks"] * STEP_SECONDS / 60).round(1)

cols = ["asset_id", "asset_type", "true_start", "alert_tick",
        "delay_ticks", "delay_min", "metric"]
print(faulty[cols].sort_values("true_start").to_string(index=False))

detected = int(faulty["alert_tick"].notna().sum())
early = int((faulty["delay_ticks"] < 0).sum())
false_alarms = int(healthy["alert_tick"].notna().sum())
print("\n===== EARLY WARNING REPORT =====")
print(f"Faulty assets: {len(faulty)} | detected: {detected} | missed: {len(faulty) - detected}")
print(f"Alerts before the fault started: {early}")
print(f"False alarms on healthy assets: {false_alarms} / {len(healthy)}")
print("Faulty assets by type:", faulty["asset_type"].value_counts().to_dict())
if detected:
    print(f"Median detection delay: {faulty['delay_ticks'].median():.0f} readings "
          f"({faulty['delay_min'].median()} min)")
