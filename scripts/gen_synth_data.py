import csv
import random
from datetime import datetime, timedelta
import hashlib

random.seed(42)

N_LEADS = 200
MAX_ATTEMPTS_PER_LEAD = 6

states = ["CA", "TX", "FL", "NY", "IL", "WA", "NJ", "AZ"]
timezones = ["PST", "MST", "CST", "EST"]
sources = ["facebook", "google", "affiliate", "seo"]
channels = ["call", "sms"]
outcomes = ["answered", "no_answer", "voicemail", "dropped"]
conversion_types = ["retainer_signed", "transfer", "qualified_lead"]

now = datetime.utcnow()

def phone_hash(i: int) -> str:
    # deterministic hash for repeatability
    raw = f"+1555{1000000+i}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]

leads = []
for i in range(1, N_LEADS + 1):
    tz = random.choice(timezones)
    consent = random.random() > 0.08  # 92% consented
    created_at = now - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23), minutes=random.randint(0, 59))

    # 12% opt out, but only if consented
    opt_out_at = None
    if consent and random.random() < 0.12:
        opt_out_at = created_at + timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))

    leads.append({
        "lead_id": i,
        "phone_hash": phone_hash(i),
        "state": random.choice(states),
        "timezone": tz,
        "source": random.choice(sources),
        "created_at": created_at.isoformat(timespec="seconds"),
        "consent_flag": str(consent).lower(),
        "opt_out_at": opt_out_at.isoformat(timespec="seconds") if opt_out_at else ""
    })

attempt_rows = []
attempt_id = 1

for lead in leads:
    num_attempts = random.randint(0, MAX_ATTEMPTS_PER_LEAD)
    base = datetime.fromisoformat(lead["created_at"])
    for _ in range(num_attempts):
        # spread attempts across a few days
        ts = base + timedelta(days=random.randint(0, 6), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        channel = random.choice(channels)

        # push some violations:
        #  - 10% attempts outside allowed hours (UTC basis; your mart shifts by timezone)
        if random.random() < 0.10:
            ts = ts.replace(hour=random.choice([0, 1, 2, 22, 23]))

        attempt_rows.append({
            "attempt_id": attempt_id,
            "lead_id": lead["lead_id"],
            "channel": channel,
            "attempt_ts": ts.isoformat(timespec="seconds"),
            "outcome": random.choice(outcomes),
            "campaign_id": f"cmp_{random.randint(1,8)}"
        })
        attempt_id += 1

conversion_rows = []
conversion_id = 1
for lead in leads:
    # 18% convert
    if random.random() < 0.18:
        created = datetime.fromisoformat(lead["created_at"])
        conv_ts = created + timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))
        conversion_rows.append({
            "conversion_id": conversion_id,
            "lead_id": lead["lead_id"],
            "conversion_ts": conv_ts.isoformat(timespec="seconds"),
            "conversion_type": random.choice(conversion_types),
            "revenue": round(random.uniform(50, 350), 2)
        })
        conversion_id += 1

# DNC list: 7% of leads
dnc_rows = [{"phone_hash": lead["phone_hash"]} for lead in random.sample(leads, k=max(1, int(0.07 * N_LEADS)))]

with open("data/leads.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["lead_id","phone_hash","state","timezone","source","created_at","consent_flag","opt_out_at"])
    w.writeheader()
    w.writerows(leads)

with open("data/contact_attempts.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["attempt_id","lead_id","channel","attempt_ts","outcome","campaign_id"])
    w.writeheader()
    w.writerows(attempt_rows)

with open("data/conversions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["conversion_id","lead_id","conversion_ts","conversion_type","revenue"])
    w.writeheader()
    w.writerows(conversion_rows)

with open("data/dnc.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["phone_hash"])
    w.writeheader()
    w.writerows(dnc_rows)

print("Wrote data/leads.csv, data/contact_attempts.csv, data/conversions.csv, data/dnc.csv")
