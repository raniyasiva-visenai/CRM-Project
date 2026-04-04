"""
Lancor CRM Builder (cp.lancor.in)
Platform: Rails/Sell.do — CSRF + fetch POST
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class LancorBuilder(SellDoRailsBase):
    """
    Lancor Channel Partner CRM.

    Required config:
      - login_url      : https://cp.lancor.in/users/sign_in?locale=en
      - dashboard_url  : https://cp.lancor.in/dashboard?locale=en
      - submit_url     : https://cp.lancor.in/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "667948099f967d68f97973f7"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://cp.lancor.in/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://cp.lancor.in/dashboard?locale=en")
        config.setdefault("submit_url",    "https://cp.lancor.in/admin/leads?locale=en")
        super().__init__(config, session_manager=session_manager)
