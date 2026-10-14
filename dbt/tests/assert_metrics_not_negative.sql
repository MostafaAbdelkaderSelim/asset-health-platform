select *
from {{ ref('fct_telemetry') }}
where temperature_c < 0
   or cpu_pct < 0
   or latency_ms < 0
   or packet_loss_pct < 0
   or vibration_mm_s < 0
   or load_pct < 0