"""
Altis CRM Builder (cp.altisproperties.in)
Platform: Rails/Sell.do — CSRF + fetch POST
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class AltisBuilder(SellDoRailsBase):
    """
    Altis Properties Channel Partner CRM.

    Required config:
      - login_url      : https://cp.altisproperties.in/users/sign_in?locale=en
      - dashboard_url  : https://cp.altisproperties.in/dashboard?locale=en
      - submit_url     : https://cp.altisproperties.in/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "68ad603bb791be713f97d69a"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://cp.altisproperties.in/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://cp.altisproperties.in/dashboard?locale=en")
        config.setdefault("submit_url",    "https://cp.altisproperties.in/admin/leads?locale=en")
        super().__init__(config, session_manager=session_manager)
