with src as (
  select * from raw.contact_attempts
)
select
  attempt_id,
  lead_id,
  lower(channel) as channel,
  attempt_ts,
  lower(outcome) as outcome,
  campaign_id
from src
