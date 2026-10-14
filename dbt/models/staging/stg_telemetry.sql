select *
from delta_scan('{{ var("silver_path") }}')