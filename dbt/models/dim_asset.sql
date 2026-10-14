select
    md5(asset_id) as asset_key,
    asset_id,
    client,
    asset_type,
    site,
    vendor,
    install_date
from {{ ref('stg_assets') }}