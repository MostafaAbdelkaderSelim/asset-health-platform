import json

import duckdb
import pandas as pd

METRICS = [
    "temperature_c", "cpu_pct", "latency_ms",
    "packet_loss_pct", "vibration_mm_s", "load_pct",
]
BASELINE_FRAC = 0.25   # first 25% of an asset's readings = healthy reference
RECENT_FRAC = 0.20     # last 20% = current state
THRESHOLD = 3.0        # flag assets drifting more than 3 std devs

con = duckdb.connect("dbt/asset_health.duckdb", read_only=True)
df = con.execute(
    f"select asset_id, event_ts, {', '.join(METRICS)} "
    "from main.fct_telemetry order by asset_id, event_ts"
).df()

truth = set(json.load(open("data/ground_truth.json", encoding="utf-8")))

df["rn"] = df.groupby("asset_id").cumcount() + 1
n = df.groupby("asset_id")["rn"].transform("max")
base = df[df["rn"] <= n * BASELINE_FRAC]
recent = df[df["rn"] > n * (1 - RECENT_FRAC)]

b = base.groupby("asset_id")[METRICS].agg(["mean", "std"])
r = recent.groupby("asset_id")[METRICS].mean()

z = pd.DataFrame({m: (r[m] - b[(m, "mean")]) / b[(m, "std")] for m in METRICS})
out = pd.DataFrame({"drift_score": z.max(axis=1), "top_metric": z.idxmax(axis=1)})
out["is_faulty"] = out.index.isin(truth)
out["flagged"] = out["drift_score"] >= THRESHOLD
out = out.sort_values("drift_score", ascending=False)

print(out.head(10).round(2).to_string())

tp = int((out["flagged"] & out["is_faulty"]).sum())
fp = int((out["flagged"] & ~out["is_faulty"]).sum())
fn = int((~out["flagged"] & out["is_faulty"]).sum())
print("\n===== DETECTION REPORT =====")
print(f"Assets: {len(out)} | truly faulty: {len(truth)}")
print(f"TP={tp} FP={fp} FN={fn}")
print(f"Precision: {tp / max(tp + fp, 1):.2f} | Recall: {tp / max(tp + fn, 1):.2f}")
print(f"Lowest faulty score : {out[out.is_faulty].drift_score.min():.2f}")
print(f"Highest healthy score: {out[~out.is_faulty].drift_score.max():.2f}")
