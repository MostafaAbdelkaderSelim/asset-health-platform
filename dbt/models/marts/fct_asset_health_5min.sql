select
    asset_key,
    time_bucket(interval '5 minutes', event_ts) as bucket_start,
    count(*) as readings,
    avg(temperature_c) as avg_temp_c,
    max(temperature_c) as max_temp_c,
    avg(vibration_mm_s) as avg_vibration_mm_s,
    avg(cpu_pct) as avg_cpu_pct,
    avg(latency_ms) as avg_latency_ms,
    avg(packet_loss_pct) as avg_packet_loss_pct,
    sum(case when has_sensor_error then 1 else 0 end) as sensor_error_readings
from {{ ref('fct_telemetry') }}
group by 1, 2