"""
Voora CRM Builder (cpportal.voora.co.in)
Platform: Rails/Sell.do — CSRF + fetch POST

Note: Login uses email input type (same as Taj)
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class VooraBuilder(SellDoRailsBase):
    """
    Voora Channel Partner CRM.

    Required config:
      - login_url      : https://cpportal.voora.co.in/users/sign_in?locale=en
      - dashboard_url  : https://cpportal.voora.co.in/dashboard?locale=en
      - submit_url     : https://cpportal.voora.co.in/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "69a0333febfeca3dd68cff4f"
      - login_type     : "email"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://cpportal.voora.co.in/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://cpportal.voora.co.in/dashboard?locale=en")
        config.setdefault("submit_url",    "https://cpportal.voora.co.in/admin/leads?locale=en")
        config.setdefault("login_type",    "email")
        super().__init__(config, session_manager=session_manager)

    def _build_payload(self, lead: Lead, csrf: str) -> Dict[str, str]:
        payload = super()._build_payload(lead, csrf)
        payload["lead[flat_preference]"] = lead.bhk_type or ""
        payload["lead[budget]"]          = lead.budget_text or ""
        payload["lead[remarks]"]         = lead.remarks or ""
        return payload
