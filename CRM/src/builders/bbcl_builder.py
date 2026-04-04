from src.builders.api_base import APIBase
from src.models.lead import Lead
from typing import Dict, Any

class BBCLBuilder(APIBase):
    """
    BBCL Freshworks CRM Builder.
    Submits lead data directly to the Freshworks smart form endpoint.
    """
    
    def _prepare_payload(self, lead: Lead) -> Dict[str, Any]:
        """
        Custom payload preparation for BBCL Freshworks.
        Includes required hidden fields (Owner ID, Asset Key, etc.).
        """
        config = self.config
        
        payload = {
            "entity_type": "2",
            "asset_key": config.get("asset_key", "9b96f1c662a5c426a7ecfacc85fd299e77cf9994dbbb1599c303ca9cf9a7018c"),
            "contact[first_name]": f"{lead.first_name} {lead.last_name or ''}".strip(),
            "contact[emails]": lead.email,
            "contact[mobile_number]": lead.mobile,
            "contact[custom_field][cf_project_name]": config.get("project_name", "BBCL Breeze"),
            "contact[custom_field][cf_channel_partner_lead_field]": config.get("cp_name", "CP - Marutham Prop Consulting"),
            "contact[custom_field][cf_country_code_checkbox_lead_field]": "1",
            "contact[owner_id]": config.get("owner_id", "113000000656"),
            "contact[lifecycle_stage_id]": config.get("lifecycle_stage_id", "114000001126"),
            "contact[lead_source_id]": config.get("lead_source_id", "13000232446")
        }
        
        # Override with any specific mapping from config if provided
        for key, field in self.payload_mapping.items():
            if hasattr(lead, str(field)):
                payload[key] = getattr(lead, str(field))
                
        return payload

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Execute the Freshworks submission.
        """
        # Set required headers for Freshworks
        self.headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://bbcl.freshworks.com"
        })
        
        self.log(f"🚀 Starting BBCL Freshworks submission for {lead.first_name}...")
        
        result = super().submit_lead(lead)
        
        if result.get("status") == 200:
            body_data = result.get("body")
            
            # Case 1: JSON response (dict)
            if isinstance(body_data, dict):
                if body_data.get("status") == "ok":
                    return {"success": True, "status": "SUCCESS", "response": body_data}
            
            # Case 2: String/Text response
            body_str = str(body_data).lower()
            if '"status":"ok"' in body_str or "success" in body_str:
                return {
                    "success": True,
                    "status": "SUCCESS",
                    "response": body_data
                }
        
        if result.get("status") == 400:
            body_data = result.get("body")
            if isinstance(body_data, dict):
                errors = body_data.get("errors", {})
                message = str(errors.get("message", "")).lower()
                if "already exists" in message or "not unique" in message:
                    return {
                        "success": True,
                        "status": "DUPLICATE",
                        "response": body_data
                    }
        
        return {
            "success": False,
            "status": "FAILED",
            "error": f"Submission failed with status {result.get('status')}",
            "response": result.get("body")
        }
