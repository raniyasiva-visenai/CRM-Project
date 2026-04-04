from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any

class DRABuilder(SellDoRailsBase):
    """
    DRA Homes (Iris) CRM Builder.
    Inherits from SellDoRailsBase to handle the Rails-based CP portal.
    """
    def __init__(self, config: Dict[str, Any], session_manager=None):
        # Default DRA URLs if not provided in DB config
        if not config.get("login_url"):
            config["login_url"] = "https://cp-iris.drahomes.in/users/sign_in?locale=en"
        if not config.get("dashboard_url"):
            config["dashboard_url"] = "https://cp-iris.drahomes.in/dashboard?locale=en"
        if not config.get("submit_url"):
            config["submit_url"] = "https://cp-iris.drahomes.in/admin/leads?locale=en"
        
        super().__init__(config, session_manager=session_manager)

    def _build_payload(self, lead: Lead, csrf: str) -> Dict[str, str]:
        """Customizing payload for DRA requirements."""
        payload = super()._build_payload(lead, csrf)
        
        # DRA specific fields from POC
        payload.update({
            "lead[property_type]": lead.project_type or "Residential",  # Default if missing
            "lead[resident_type]": "Indian",                            # Standard for most leads
            "lead[remarks]":       lead.remarks or "Lead from Marutham Properties",
        })
        
        # Ensure project_id is prioritized from lead if provided
        if lead.project_id:
            payload["lead[project_id]"] = lead.project_id
            
        return payload
