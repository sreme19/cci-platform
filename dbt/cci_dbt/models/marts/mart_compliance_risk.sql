with leads as (
  select
    lead_id,
    phone_hash,
    timezone,
    consent_flag,
    opt_out_at
  from {{ ref('stg_leads') }}
),

attempts as (
  select
    attempt_id,
    lead_id,
    channel,
    attempt_ts,
    outcome,
    campaign_id
  from {{ ref('stg_contact_attempts') }}
),

-- join attempts with lead attributes
attempts_enriched as (
  select
    a.*,
    l.phone_hash,
    l.timezone,
    l.consent_flag,
    l.opt_out_at,

    -- local hour approximation (simple + good enough for prototype)
    -- PST = UTC-8, MST = UTC-7, CST = UTC-6, EST = UTC-5
    case
      when l.timezone = 'PST' then (a.attempt_ts - interval '8 hours')
      when l.timezone = 'MST' then (a.attempt_ts - interval '7 hours')
      when l.timezone = 'CST' then (a.attempt_ts - interval '6 hours')
      when l.timezone = 'EST' then (a.attempt_ts - interval '5 hours')
      else a.attempt_ts
    end as attempt_ts_local

  from attempts a
  join leads l using (lead_id)
),

dnc as (
  select distinct phone_hash
  from raw.dnc
),

-- violation 1: attempts outside legal calling window (8am–9pm local)
v_outside_hours as (
  select
    lead_id,
    attempt_id,
    attempt_ts,
    attempt_ts_local,
    campaign_id,
    'outside_allowed_hours' as violation_type,
    'high' as severity,
    'Attempt made outside 08:00–21:00 local time' as details
  from attempts_enriched
  where extract(hour from attempt_ts_local) < 8
     or extract(hour from attempt_ts_local) >= 21
),

-- violation 2: too many attempts per day (>3) per lead
v_too_many_attempts as (
  select
    lead_id,
    null::text as attempt_id,
    min(attempt_ts) as attempt_ts,
    min(attempt_ts_local) as attempt_ts_local,
    null::text as campaign_id,
    'too_many_attempts_per_day' as violation_type,
    'medium' as severity,
    'More than 3 attempts in a single local day' as details
  from (
    select
      lead_id,
      date(attempt_ts_local) as local_day,
      count(*) as attempts_in_day,
      min(attempt_ts) as attempt_ts,
      min(attempt_ts_local) as attempt_ts_local
    from attempts_enriched
    group by 1,2
  ) x
  where attempts_in_day > 3
  group by lead_id
),

-- violation 3: attempted after opt-out
v_after_opt_out as (
  select
    lead_id,
    attempt_id,
    attempt_ts,
    attempt_ts_local,
    campaign_id,
    'attempt_after_opt_out' as violation_type,
    'high' as severity,
    'Contact attempt occurred after opt-out timestamp' as details
  from attempts_enriched
  where opt_out_at is not null
    and attempt_ts >= opt_out_at
),

-- violation 4: DNC hit
v_dnc as (
  select
    ae.lead_id,
    ae.attempt_id,
    ae.attempt_ts,
    ae.attempt_ts_local,
    ae.campaign_id,
    'dnc_match' as violation_type,
    'critical' as severity,
    'Phone hash matched DNC list' as details
  from attempts_enriched ae
  join dnc d using (phone_hash)
),

-- violation 5: no consent (if you want strict mode)
v_no_consent as (
  select
    lead_id,
    attempt_id,
    attempt_ts,
    attempt_ts_local,
    campaign_id,
    'no_consent' as violation_type,
    'high' as severity,
    'Lead consent_flag=false but attempts exist' as details
  from attempts_enriched
  where consent_flag = false
)

select * from v_outside_hours
union all
select * from v_too_many_attempts
union all
select * from v_after_opt_out
union all
select * from v_dnc
union all
select * from v_no_consent
