"""
simulate_all_crms.py
====================
Pushes ONE lead per CRM into the database with a unique leadsource_id.
We have commented out the successful, live CRMs (BBCL, LML, Radiance, 
Royal, Sameera, StepsStone) to prevent spamming their production databases.

Run:
    # Terminal 1 — start the worker
    python main.py

    # Terminal 2 — inject leads
    python simulate_all_crms.py

Then check results:
    python check_verify.py
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from src.models.lead import Lead
from src.utilities.db.utilities import DatabaseUtilities
from config.db import DB_CONFIG

# ─── Shared CP Info ───────────────────────────────────────────────────────────
CP_NAME      = "Dinesh Suriyanathan"
CP_COMPANY   = "Marutham Prop Consulting"
CP_PHONE     = "9876543212"
CP_DIAL_CODE = "+91"
CP_ID_ROYAL  = "67a330f75d8defcff4ae3457"
CP_ID_LML    = "663c58e7735daf928426634a"

TS = datetime.now().strftime("%d%m%H%M")   # unique suffix per run

# ─── Leads (Filtered to only the ones needing debug) ────────────────────
TEST_LEADS = [

    # ── 1. SIS Golden Gate (Playwright login → fetch POST) ────────────────────
    Lead(
        leadsource_id=f"LEAD_SIS_{TS}",
        first_name="Manoj",
        last_name="Kumar",
        mobile=f"987650{TS[:4]}",
        dial_code="+91",
        email=f"lead_sis_{TS}@simulator.com",
        location="Pallikaranai",
        project_type="Apartment",
        project_id="6513ad64b791be7102f16958",   # S.I.S Golden Gate
        cp_name=CP_NAME,
        cp_company=CP_COMPANY,
        cp_phone=CP_PHONE,
        remarks="Lead from Marutham Properties (SIS)",
        source="Simulator",
    ),

    # ── 2. S&P CP (Playwright login → fetch POST, no CSRF required) ──────────
    Lead(
        leadsource_id=f"LEAD_SP_{TS}",
        first_name="Arjun",
        last_name="Kumar",
        mobile=f"987651{TS[:4]}",
        dial_code="+91",
        email=f"lead_sp_{TS}@simulator.com",
        location="Chennai",       # S&P matches '*' location
        project_type="Apartment",
        project_id="68f08b08c6380945a9ea9afd",
        cp_name=CP_NAME,
        cp_company=CP_COMPANY,
        cp_phone=CP_PHONE,
        remarks="Lead from Marutham Properties (S&P)",
        source="Simulator",
    ),

    # ── 3. KG Builders (Playwright + referral fields) ─────────────────────────
    Lead(
        leadsource_id=f"LEAD_KG_{TS}",
        first_name="Dinesh",
        last_name="Karthik",
        mobile=f"987652{TS[:4]}",
        dial_code="+91",
        email=f"lead_kg_{TS}@simulator.com",
        location="Siruseri",
        project_type="Villa",
        project_id="6588d8f3b791be673c541b00",
        referral_name=CP_NAME,
        referral_email="user@maruthamprop.com",
        referral_mobile=CP_PHONE,
        remarks="Lead from Marutham Properties (KG Builders)",
        source="Simulator",
    ),

    # ── 4. SalesRobot (Original) ──────────────────────────────────────────
    Lead(
        leadsource_id=f"LEAD_SR_{TS}",
        first_name="Manoj",
        last_name="Kumar",
        mobile=f"987657{TS[:4]}",
        salutation="Mr.",
        email=f"lead_sr_{TS}@simulator.com",
        location="Chennai",
        project_type="Residential",
        project_name="Lifestyle Vardaan",
        cp_name="Dinesh Suriyanathan",
        cp_company="Marutham Prop",
        source="Channel Partner",
        remarks="Lead from Marutham Properties (SalesRobot)",
    ),
 
    # ── 5. Urbantree (SalezRobot) ────────────────────────────────────────
    Lead(
        leadsource_id=f"LEAD_UT_{TS}",
        first_name="Manoj UT",
        mobile=f"976543{TS[:4]}",
        email=f"ut_{TS}@simulator.com",
        project_type="Crystal_Crown",
        remarks="Lead from Marutham Properties (Urbantree)",
    ),
 
    # ── 6. Praganya (SalezRobot) ─────────────────────────────────────────
    Lead(
        leadsource_id=f"LEAD_PR_{TS}",
        first_name="Manoj PR",
        mobile=f"976544{TS[:4]}",
        email=f"pr_{TS}@simulator.com",
        project_type="Standard",
        remarks="Lead from Marutham Properties (Praganya)",
    ),
 
    # ── 7. Vista (RWD / Listez) ───────────────────────────────────────────
    Lead(
        leadsource_id=f"LEAD_VS_{TS}",
        first_name="Manoj VS",
        mobile=f"976545{TS[:4]}",
        email=f"vs_{TS}@simulator.com",
        remarks="Lead from Marutham Properties (Vista)",
    ),
]


# ─── Runner ───────────────────────────────────────────────────────────────────
def run():
    db = DatabaseUtilities(DB_CONFIG)

    print("=" * 65)
    print(f"🚀  CRM Simulator — pushing {len(TEST_LEADS)} leads")
    print("=" * 65)
    print(f"   Run timestamp: {TS}\n")
    print("   Make sure 'python main.py' is running in another terminal!\n")

    for i, lead in enumerate(TEST_LEADS, 1):
        print(f"[{i:02d}/{len(TEST_LEADS):02d}] {lead.leadsource_id:<20} → {lead.first_name} {lead.last_name}  ({lead.location} | {lead.project_type})")
        db.save_lead(lead)
        time.sleep(1)   # small delay to avoid DB lock contention

    print("\n" + "=" * 65)
    print(f"✅  All {len(TEST_LEADS)} leads inserted with status=RECEIVED.")
    print("   Watch 'python main.py' output for real-time CRM submissions.")
    print("   Verify results:  python check_verify.py")
    print("=" * 65)


if __name__ == "__main__":
    run()
