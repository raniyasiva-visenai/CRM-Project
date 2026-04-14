from src.builders.api_base import APIBase
from src.models.lead import Lead
from typing import Dict, Any

class TVHBuilder(APIBase):
    """
    TVH (TrueValueHomes) SELLDO Builder.
    Submits lead data to the Sell.do form endpoint.
    Form URL: https://forms.sell.do/truevaluehomes/form.php
    """
    
    def _prepare_payload(self, lead: Lead) -> Dict[str, Any]:
        """
        Prepare payload for TVH SELLDO form submission using inspected field names.
        """
        # Mapping Lead attributes to form fields
        payload = {
            "salutation": "Mr",
            "name": f"{lead.first_name} {lead.last_name or ''}".strip(),
            "svleadphone": lead.mobile,
            "mail": lead.email or "",
            "project_lists": lead.project_name or "TVH QUADRANT",
            "cpname": "Marutham",
            "cpfirmname": "Marutham prop",
            "cpphone": "",
            "cpemail": "",
            "remarks": lead.remarks or "Feedback",
        }
        
        # Override with raw_payload if provided (useful for dynamic attributes)
        if lead.raw_payload and isinstance(lead.raw_payload, dict):
            payload.update(lead.raw_payload)
            
        return payload

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Execute the direct POST submission to TVH SELLDO form.
        """
        self.log(f"Starting TVH SELLDO submission for {lead.first_name}...")
        
        # Standard APIBase submit (uses requests.post)
        result = super().submit_lead(lead)
        
        # Handle Sell.do form response
        if result.get("status") == 200:
            body_data = result.get("body")
            
            # Case 1: JSON response
            if isinstance(body_data, dict):
                msg = str(body_data.get("message", "")).lower()
                status = str(body_data.get("status", "")).lower()
                
                if status == "success" or "added successfully" in msg or "thank you" in msg:
                    return {"success": True, "status": "SUCCESS", "response": body_data}
                elif "already exists" in msg or "duplicate" in msg:
                    return {"success": True, "status": "DUPLICATE", "response": body_data}
                
            # Case 2: String/Text response
            body_str = str(body_data).lower() if body_data else ""
            if "success" in body_str or "thank you" in body_str or "added successfully" in body_str or "received" in body_str:
                return {"success": True, "status": "SUCCESS", "response": body_data}
            elif "already exists" in body_str or "duplicate" in body_str:
                return {"success": True, "status": "DUPLICATE", "response": body_data}
        
        return {
            "success": False,
            "status": "FAILED",
            "error": f"Submission failed with status {result.get('status')}",
            "response": result.get("body")
        }
