{{ config(schema='restricted') }}

select
    asset_id,
    owner_name,
    owner_email
from {{ ref('stg_assets') }}