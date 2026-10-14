with versions as (
    select
        *,
        row_number() over (partition by asset_id order by dbt_valid_from) as version_no
    from {{ ref('snap_asset') }}
)

select
    md5(asset_id || '|' || cast(dbt_valid_from as varchar)) as asset_key,
    asset_id,
    client,
    asset_type,
    site,
    vendor,
    install_date,
    case
        when version_no = 1 then timestamptz '1900-01-01'
        else dbt_valid_from
    end as valid_from,
    coalesce(dbt_valid_to, timestamptz '9999-12-31') as valid_to,
    dbt_valid_to is null as is_current
from versions