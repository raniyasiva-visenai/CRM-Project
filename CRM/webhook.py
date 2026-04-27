from fastapi import FastAPI, Request, HTTPException
import os
import sys

# Ensure CRM/src is in path if running as a standalone script
sys.path.append(os.path.dirname(__file__))

from src.models.lead import Lead
from src.utilities.db.utilities import DatabaseUtilities
from config.db import DB_CONFIG

app = FastAPI()

# Database Utility Instance
db = DatabaseUtilities(DB_CONFIG)

# ✅ Handle BOTH GET + POST + trailing slash
@app.api_route("/webhook/lead", methods=["GET", "POST"])
@app.api_route("/webhook/lead/", methods=["GET", "POST"])
async def lead_webhook_handler(request: Request):
    try:
        # 🔹 GET → Validation / Ping
        if request.method == "GET":
            print("\n=== WEBHOOK VALIDATION (GET) ===")
            return {"status": "ok", "message": "Webhook is live"}

        # 🔹 POST → Actual lead reception
        try:
            body = await request.json()
        except Exception:
            body = {}

        if not body:
            raise HTTPException(status_code=400, detail="Empty request body")

        # 🛠️ MAPPING & MODEL CREATION
        # We create a Lead object matching the schema
        lead = Lead(
            leadsource_id=body.get("ProspectID"),
            first_name=body.get("FirstName", "Unknown"),
            last_name=body.get("LastName"),
            mobile=body.get("Phone", "0000000000"),
            email=body.get("EmailAddress"),
            project_name=body.get("mx_Project_Name"),
            location=body.get("mx_Locality"),
            city=body.get("mx_City"),
            source=body.get("Source", "External Webhook"),
            stage=body.get("ProspectStage", "warm"),
            status="RECEIVED",
            raw_payload=body
        )

        print(f"\n=== [PRODUCTION] NEW LEAD RECEIVED: {lead.leadsource_id} ===")

        # 🚀 SAVE LEAD TO DATABASE
        # Saving as 'RECEIVED' makes it visible to the LeadProcessor worker
        lead_id = db.save_lead(lead)
        
        if not lead_id:
            raise Exception("Failed to save lead to database")

        print(f"--- SUCCESS: Lead {lead_id} saved for distribution ---\n")

        return {
            "status": "success",
            "lead_id": lead_id,
            "message": "Lead received and queued for processing"
        }

    except Exception as e:
        print(f"!!! Error in Webhook: {str(e)} !!!")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


