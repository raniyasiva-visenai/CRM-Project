from src.builders.api_base import APIBase
from src.models.lead import Lead
from typing import Dict, Any

class StepsStoneSellDoBuilder(APIBase):
    """
    StepsStone Sell.do Direct API Builder.
    Submits lead data directly to the Sell.do form endpoint.
    """
    
    def _prepare_payload(self, lead: Lead) -> Dict[str, Any]:
        """
        Custom payload preparation for StepsStone Sell.do form.
        """
    def _prepare_payload(self, lead: Lead) -> Dict[str, Any]:
        """
        Dynamically use raw_payload from the lead simulation.
        This allows the simulator to fully control the submission data.
        """
        if lead.raw_payload and isinstance(lead.raw_payload, dict):
            self.log("📋 Using full dynamic payload from lead.raw_payload")
            return lead.raw_payload
            
        # Fallback to a minimal payload if raw_payload is missing
        self.log("⚠️ Warning: No raw_payload found for StepsStone Sell.do. Using minimal fallback.")
        return {
            "name": f"{lead.first_name} {lead.last_name or ''}".strip(),
            "phone": lead.mobile,
            "project_id": self.config.get("crm_project_id"),
            "comments": lead.remarks or "Interested in project"
        }

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Execute the direct POST submission.
        """
        self.log(f"🚀 Starting StepsStone Sell.do submission for {lead.first_name}...")
        
        result = super().submit_lead(lead)
        
        # Sell.do form often returns 200 even for duplicates, but we can check the body
        if result.get("status") == 200:
            body_data = result.get("body")
            
            # Case 1: JSON response
            if isinstance(body_data, dict):
                msg = str(body_data.get("message", "")).lower()
                status = str(body_data.get("status", "")).lower()
                
                if status == "success" or "added successfully" in msg:
                    return {"success": True, "status": "SUCCESS", "response": body_data}
                elif "already exists" in msg or "duplicate" in msg:
                    return {"success": True, "status": "DUPLICATE", "response": body_data}
                
            # Case 2: String/Text response
            body_str = str(body_data).lower()
            if "success" in body_str or "thank you" in body_str or "added successfully" in body_str:
                return {"success": True, "status": "SUCCESS", "response": body_data}
            elif "already exists" in body_str or "duplicate" in body_str:
                return {"success": True, "status": "DUPLICATE", "response": body_data}
        
        return {
            "success": False,
            "status": "FAILED",
            "error": f"Submission failed with status {result.get('status')}",
            "response": result.get("body")
        }
