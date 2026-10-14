select 1
where (select count(*) from {{ ref('fct_telemetry') }})
   <> (select count(*) from {{ ref('stg_telemetry') }})