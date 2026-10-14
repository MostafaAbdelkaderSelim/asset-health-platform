import argparse
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from simulator import telemetry as sim  # noqa: E402

METRICS = [
    "temperature_c", "cpu_pct", "latency_ms",
    "packet_loss_pct", "vibration_mm_s", "load_pct",
]
BASELINE_FRAC = 0.25
WINDOW = 10
TICKS = 200
THRESHOLDS = [1.5, 2.0, 3.0, 4.0]
SCALES = [1.0, 0.5, 0.25, 0.1]   # fault strength vs the original simulator
BASE_DRIFT = dict(sim.DRIFT)


def pick_mixed_faults(assets, ticks, n_each=3):
    telecom = [a for a in assets if a["asset_type"] in sim.TELECOM]
    industrial = [a for a in assets if a["asset_type"] not in sim.TELECOM]
    chosen = random.sample(telecom, n_each) + random.sample(industrial, n_each)
    return {
        a["asset_id"]: random.randint(int(ticks * 0.3), int(ticks * 0.6))
        for a in chosen
    }


def build_frame(assets, faulty):
    df = pd.DataFrame(list(sim.generate_events(assets, TICKS, faulty)))
    for m in METRICS:
        if m not in df.columns:
            df[m] = np.nan
    df = df.drop_duplicates("event_id")                      # same as Silver
    df[METRICS] = df[METRICS].astype(float).replace(-999.0, np.nan)
    return df.sort_values(["asset_id", "event_ts"]).reset_index(drop=True)


def z_matrix(g):
    n = len(g)
    split = int(n * BASELINE_FRAC)
    cols = []
    for m in METRICS:
        base = g[m].iloc[:split]
        mu, sd = base.mean(), base.std()
        if not (np.isfinite(mu) and np.isfinite(sd)) or sd == 0:
            cols.append(np.full(n, np.nan))
            continue
        roll = g[m].rolling(WINDOW, min_periods=WINDOW // 2).mean()
        cols.append(((roll - mu) / sd).to_numpy())
    return np.column_stack(cols), split


def first_alert(Z, split, thr):
    with np.errstate(invalid="ignore"):
        hit = (Z >= thr).any(axis=1)
    hit[:split] = False
    idx = np.flatnonzero(hit)
    return int(idx[0]) if len(idx) else None


def summarize(g):
    f, h = g[g.faulty], g[~g.faulty]
    d = f[f.detected]
    return {
        "recall_telecom": f[f.group == "telecom"].detected.mean(),
        "recall_industrial": f[f.group == "industrial"].detected.mean(),
        "false_alarm_rate": h.detected.mean(),
        "early_alerts": int((d.delay < 0).sum()),
        "median_delay": d.delay.median(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--n-seeds", type=int, default=5)
    args = ap.parse_args()

    assets = sim.load_assets()
    group = {
        a["asset_id"]: "telecom" if a["asset_type"] in sim.TELECOM else "industrial"
        for a in assets
    }

    rows = []
    for scale in SCALES:
        for k, v in BASE_DRIFT.items():
            sim.DRIFT[k] = v * scale
        for seed in range(args.seed_start, args.seed_start + args.n_seeds):
            random.seed(seed)
            faulty = pick_mixed_faults(assets, TICKS)
            df = build_frame(assets, faulty)
            for asset_id, g in df.groupby("asset_id"):
                Z, split = z_matrix(g.reset_index(drop=True))
                for thr in THRESHOLDS:
                    at = first_alert(Z, split, thr)
                    rows.append({
                        "scale": scale, "threshold": thr, "seed": seed,
                        "asset_id": asset_id, "group": group[asset_id],
                        "true_start": faulty.get(asset_id),
                        "alert_tick": at,
                    })

    res = pd.DataFrame(rows)
    res["faulty"] = res.true_start.notna()
    res["detected"] = res.alert_tick.notna()
    res["delay"] = res.alert_tick - res.true_start

    lines = []
    for (scale, thr), g in res.groupby(["scale", "threshold"]):
        lines.append({"scale": scale, "threshold": thr, **summarize(g)})
    out = pd.DataFrame(lines).round(2)

    n_seeds = args.n_seeds
    print(f"Seeds: {args.seed_start}..{args.seed_start + n_seeds - 1} | "
          f"per config: {3 * n_seeds} telecom + {3 * n_seeds} industrial faults, "
          f"{54 * n_seeds} healthy asset-runs")
    print("scale = fault strength (1.0 = original). delay is in readings (1 reading = 10 s).\n")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
