with src as (
  select * from raw.leads
)
select
  lead_id,
  phone_hash,
  state,
  timezone,
  source,
  created_at,
  consent_flag,
  opt_out_at
from src
