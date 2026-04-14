from src.builders.api_base import APIBase
from src.models.lead import Lead
from typing import Dict, Any

class BSCPLBuilder(APIBase):
    """
    BSCPL PropFlo Builder.
    Submits lead data to PropFlo's public partner lead API.
    """
    
    def _prepare_payload(self, lead: Lead) -> Dict[str, Any]:
        """
        Prepare JSON payload for PropFlo API.
        """
        # BSCPL Specific IDs from the integrated URL
        project_id = "67f61c72cb0678bb5f3a1293"
        partner_code = "BSC026"
        
        payload = {
            "customerName": f"{lead.first_name} {lead.last_name or ''}".strip(),
            "customerPhone": lead.mobile,
            "customerEmail": lead.email or "",
            "projectId": project_id,
            "partnerCode": partner_code,
            "remark": lead.remarks or "Interested in the project"
        }
        
        # Override with any dynamic config if present
        if lead.raw_payload and isinstance(lead.raw_payload, dict):
            payload.update(lead.raw_payload)
            
        return payload

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Submit lead to PropFlo API.
        Endpoint: https://api.propflo.ai/leads/v1/public/partner-lead
        """
        self.log(f"Starting BSCPL PropFlo submission for {lead.first_name}...")
        
        # PropFlo standard API endpoint
        # The API URL should ideally be in the DB, but we'll use the one captured.
        api_url = self.config.get("submit_url") or "https://api.propflo.ai/leads/v1/public/partner-lead"
        
        result = super().submit_lead(lead)
        
        if result.get("status") in [200, 201]:
            body = result.get("body")
            if isinstance(body, dict):
                # PropFlo usually returns a message
                msg = str(body.get("message", "")).lower()
                if "success" in msg or "created" in msg or "thank you" in msg:
                    return {"success": True, "status": "SUCCESS", "response": body}
                elif "duplicate" in msg or "already exists" in msg:
                    return {"success": True, "status": "DUPLICATE", "response": body}
            
            # Fallback for successful HTTP status
            return {"success": True, "status": "SUCCESS", "response": body}
            
        return {
            "success": False,
            "status": "FAILED",
            "error": f"PropFlo submission failed: {result.get('status')}",
            "response": result.get("body")
        }
