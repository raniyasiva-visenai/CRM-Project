"""
MP Developers CRM Builder (cp.mpdevelopers.com)
Platform: Rails/Sell.do — CSRF + fetch POST
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class MPBuilder(SellDoRailsBase):
    """
    MP Developers Channel Partner CRM.

    Required config:
      - login_url      : https://cp.mpdevelopers.com/users/sign_in?locale=en
      - dashboard_url  : https://cp.mpdevelopers.com/dashboard?locale=en
      - submit_url     : https://cp.mpdevelopers.com/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "68218230ebfeca69605090f0"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://cp.mpdevelopers.com/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://cp.mpdevelopers.com/dashboard?locale=en")
        config.setdefault("submit_url",    "https://cp.mpdevelopers.com/admin/leads?locale=en")
        super().__init__(config, session_manager=session_manager)

    def _build_payload(self, lead: Lead, csrf: str) -> Dict[str, str]:
        payload = super()._build_payload(lead, csrf)
        payload["lead[source]"]   = lead.source or "Website"
        payload["lead[medium]"]   = "Organic"
        payload["lead[campaign]"] = "Automation"
        return payload
