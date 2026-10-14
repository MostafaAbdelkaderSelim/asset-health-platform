select m.asset_id
from {{ ref('dim_asset_owner_masked') }} m
join {{ ref('asset_owner_restricted') }} r using (asset_id)
where m.owner_name_masked = r.owner_name
   or m.owner_email_masked = r.owner_email