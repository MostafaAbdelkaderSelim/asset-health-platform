select table_name, column_name
from information_schema.columns
where column_name in ('owner_name', 'owner_email')
  and table_name in (
      'dim_asset',
      'fct_telemetry',
      'fct_asset_health_5min',
      'dim_asset_owner_masked'
  )