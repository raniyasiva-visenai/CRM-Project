"""
Taj Sky View CRM Builder (channelpartner.tajskyviewresidences.com)
Platform: Rails/Sell.do — CSRF + fetch POST

Note: Login uses email input type (input[type='email'][name='user[login]'])
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class TajBuilder(SellDoRailsBase):
    """
    Taj Sky View Residences Channel Partner CRM.

    Required config:
      - login_url      : https://channelpartner.tajskyviewresidences.com/users/sign_in?locale=en
      - dashboard_url  : https://channelpartner.tajskyviewresidences.com/dashboard?locale=en
      - submit_url     : https://channelpartner.tajskyviewresidences.com/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "6912e2cb82381f4a43ca7f49"
      - login_type     : "email"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://channelpartner.tajskyviewresidences.com/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://channelpartner.tajskyviewresidences.com/dashboard?locale=en")
        config.setdefault("submit_url",    "https://channelpartner.tajskyviewresidences.com/admin/leads?locale=en")
        config.setdefault("login_type",    "email")
        super().__init__(config, session_manager=session_manager)

    def _build_payload(self, lead: Lead, csrf: str) -> Dict[str, str]:
        payload = super()._build_payload(lead, csrf)
        payload["lead[referral_name]"]  = lead.referral_name or ""
        payload["lead[referral_email]"] = lead.referral_email or ""
        payload["lead[referral_phone]"] = lead.referral_mobile or ""
        payload["lead[remarks]"]        = lead.remarks or ""
        return payload
