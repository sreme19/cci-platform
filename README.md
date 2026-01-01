# Compliance-Aware Data Platform (dbt + Postgres)

## Problem
High-volume, multi-channel customer engagement platforms generate millions of regulated interactions (calls, texts, emails).
Without strong data governance, organizations face:
- TCPA / DNC violations
- Inability to quantify compliance risk
- Slow decision-making due to fragmented analytics
- High operational cost from manual audits

## Solution
Designed and implemented an end-to-end, compliance-aware analytics platform using:
- **Postgres** for raw event storage
- **dbt** for governed transformations and testing
- **Docker** for reproducible local infrastructure

The system converts raw engagement data into **auditable, executive-ready risk metrics**.

## Architecture
- Raw Layer: Ads, contact attempts, conversions, DNC lists
- Staging Layer (dbt): Cleaned, typed, tested datasets
- Mart Layer (dbt): `mart_compliance_risk` — a unified compliance risk table

## Key Capabilities
- Timezone-aware calling window enforcement (8am–9pm local)
- Daily attempt frequency violation detection
- Opt-out enforcement monitoring
- DNC list matching via hashed identifiers
- Severity-based risk classification (medium / high / critical)

## Business Impact
- Reduced manual compliance audits
- Enabled proactive risk mitigation
- Created a single source of truth for compliance leadership
- Foundation for ML-driven risk prediction and alerting

## Tech Stack
- Postgres (Dockerized)
- dbt Core + dbt-postgres
- SQL
- Git

## What This Demonstrates
- End-to-end data platform ownership
- Governance-first analytics design
- Regulatory-aware data modeling
- Production-grade transformation discipline
- Executive-level problem framing

## Results (Synthetic Run)

Violation distribution from `analytics.mart_compliance_risk`:

- outside_allowed_hours (high): 250  
- dnc_match (critical): 36  
- attempt_after_opt_out (high): 30  
- no_consent (high): 20  
- too_many_attempts_per_day (medium): 2  

Reproduce:

```bash
docker exec -it cci_postgres psql -U cci_user -d cci_db -c "
select violation_type, severity, count(*) as cnt
from analytics.mart_compliance_risk
group by 1,2
order by cnt desc;"
```

## Executive Takeaways

- Majority of compliance risk originated from operational misconfiguration
  (calling outside allowed hours), indicating system-level rather than agent-level failure.
- DNC and post–opt-out violations represent critical legal exposure and require
  real-time suppression controls.
- Consent gaps remain a material risk even with moderate volumes, reinforcing the
  need for consent-aware routing and campaign gating.
- Low incidence of attempt-frequency violations suggests rate-limiting controls
  are largely effective.

```mermaid
flowchart LR
  subgraph Sources["Data Sources"]
    A1["leads.csv"]
    A2["contact_attempts.csv"]
    A3["conversions.csv"]
    A4["dnc.csv"]
  end

  subgraph Ingest["Ingestion"]
    B1["Python generator (gen_synth_data.py)"]
    B2["psql copy into raw schema"]
  end

  subgraph Storage["Postgres (Docker)"]
    C1["raw.leads"]
    C2["raw.contact_attempts"]
    C3["raw.conversions"]
    C4["raw.dnc"]
  end

  subgraph Transform["dbt Transformations"]
    D1["stg_leads"]
    D2["stg_contact_attempts"]
    D3["stg_conversions"]
    D4["mart_compliance_risk"]
    D5["dbt tests (not_null, unique)"]
  end

  subgraph Consume["Analytics & Consumption"]
    E1["SQL analysis (psql)"]
    E2["BI dashboards (Tableau / Metabase)"]
  end

  A1 --> B1
  A2 --> B1
  A3 --> B1
  A4 --> B1

  B1 --> B2
  B2 --> C1
  B2 --> C2
  B2 --> C3
  B2 --> C4

  C1 --> D1
  C2 --> D2
  C3 --> D3
  D1 --> D4
  D2 --> D4
  D3 --> D4
  D5 --- D1
  D5 --- D2
  D5 --- D3

  D4 --> E1
  D4 --> E2

```

