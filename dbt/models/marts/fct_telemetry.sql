select
    t.event_id,
    a.asset_key,
    t.event_ts,
    t.temperature_c,
    t.cpu_pct,
    t.latency_ms,
    t.packet_loss_pct,
    t.vibration_mm_s,
    t.load_pct,
    t.has_sensor_error
from {{ ref('stg_telemetry') }} t
join {{ ref('dim_asset') }} a using (asset_id)