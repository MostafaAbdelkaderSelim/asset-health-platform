select
    asset_id,
    client,
    asset_type,
    site,
    vendor,
    install_date
from {{ ref('stg_assets') }}