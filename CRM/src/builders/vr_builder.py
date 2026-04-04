"""
VR Foundation CRM Builder (iris.vrfoundation.in)
Platform: Rails/Sell.do — CSRF + fetch POST
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class VRBuilder(SellDoRailsBase):
    """
    VR Foundation Channel Partner CRM.

    Required config:
      - login_url      : https://iris.vrfoundation.in/users/sign_in?locale=en
      - dashboard_url  : https://iris.vrfoundation.in/dashboard?locale=en
      - submit_url     : https://iris.vrfoundation.in/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "675bd84182381f42b0755619" (Dazzle City)
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://iris.vrfoundation.in/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://iris.vrfoundation.in/dashboard?locale=en")
        config.setdefault("submit_url",    "https://iris.vrfoundation.in/admin/leads?locale=en")
        super().__init__(config, session_manager=session_manager)

    def _build_payload(self, lead: Lead, csrf: str) -> Dict[str, str]:
        payload = super()._build_payload(lead, csrf)
        # VR supports referral fields
        payload["lead[referral_name]"]  = lead.referral_name or ""
        payload["lead[referral_email]"] = lead.referral_email or ""
        payload["lead[referral_phone]"] = lead.referral_mobile or ""
        payload["lead[remarks]"]        = lead.remarks or ""
        return payload
