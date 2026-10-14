select
    asset_id,
    client,
    asset_type,
    site,
    vendor,
    cast(install_date as date) as install_date,
    owner_name,
    owner_email
from {{ ref('assets') }}