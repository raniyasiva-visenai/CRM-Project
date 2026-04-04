"""
Navins CRM Builder (cp.navins.in)
Platform: Rails/Sell.do — CSRF + fetch POST
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class NavinsBuilder(SellDoRailsBase):
    """
    Navins Channel Partner CRM.

    Required config:
      - login_url      : https://cp.navins.in/users/sign_in?locale=en
      - dashboard_url  : https://cp.navins.in/dashboard?locale=en
      - submit_url     : https://cp.navins.in/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "62cd87099f967d36b3eb0604"
      - login_type     : email
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://cp.navins.in/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://cp.navins.in/dashboard?locale=en")
        config.setdefault("submit_url",    "https://cp.navins.in/admin/leads?locale=en")
        config.setdefault("login_type",    "email")
        super().__init__(config, session_manager=session_manager)
