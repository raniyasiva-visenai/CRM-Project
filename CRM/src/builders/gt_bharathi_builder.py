"""
GT Bharathi CRM Builder (cpp.gtb.in)
Platform: Rails/Sell.do — CSRF + fetch POST
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class GTBharathiBuilder(SellDoRailsBase):
    """
    GT Bharathi Channel Partner CRM.

    Required config:
      - login_url      : https://cpp.gtb.in/users/sign_in?locale=en
      - dashboard_url  : https://cpp.gtb.in/dashboard?locale=en
      - submit_url     : https://cpp.gtb.in/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "6913091682381f779565f93d"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://cpp.gtb.in/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://cpp.gtb.in/dashboard?locale=en")
        config.setdefault("submit_url",    "https://cpp.gtb.in/admin/leads?locale=en")
        super().__init__(config, session_manager=session_manager)

    def _build_payload(self, lead: Lead, csrf: str) -> Dict[str, str]:
        payload = super()._build_payload(lead, csrf)
        # GTB-specific optional fields
        payload["lead[source]"]   = lead.source or "Website"
        payload["lead[medium]"]   = "Organic"
        payload["lead[campaign]"] = "Automation"
        payload["lead[remarks]"]  = lead.remarks or ""
        return payload
