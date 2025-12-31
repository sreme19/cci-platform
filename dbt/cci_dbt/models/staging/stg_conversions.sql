with src as (
  select * from raw.conversions
)
select
  conversion_id,
  lead_id,
  conversion_ts,
  lower(conversion_type) as conversion_type,
  revenue::numeric as revenue
from src
