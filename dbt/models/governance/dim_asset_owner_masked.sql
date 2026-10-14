select
    asset_id,
    regexp_replace(owner_name, '(\w)\w*', '\1***', 'g') as owner_name_masked,
    substr(owner_email, 1, 1) || '***@' || split_part(owner_email, '@', 2) as owner_email_masked,
    md5('{{ env_var("PII_SALT", "dev-only-salt") }}' || lower(owner_email)) as owner_pseudo_id
from {{ ref('stg_assets') }}