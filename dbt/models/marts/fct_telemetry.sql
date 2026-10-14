select
    t.event_id,
    a.asset_key,
    t.asset_id,
    t.event_ts,
    t.temperature_c,
    t.cpu_pct,
    t.latency_ms,
    t.packet_loss_pct,
    t.vibration_mm_s,
    t.load_pct,
    t.has_sensor_error
from {{ ref('stg_telemetry') }} t
join {{ ref('dim_asset') }} a
    on t.asset_id = a.asset_id
   and t.event_ts >= a.valid_from
   and t.event_ts <  a.valid_to