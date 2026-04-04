"""
Earthen Spaces CRM Builder (cp.earthenspaces.com)
Platform: Rails/Sell.do — CSRF + fetch POST

Note: Login uses phone number (input[type='tel']) instead of standard #user_login.
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class ESBuilder(SellDoRailsBase):
    """
    Earthen Spaces Channel Partner CRM.

    Required config:
      - login_url      : https://cp.earthenspaces.com/users/sign_in?locale=en
      - dashboard_url  : https://cp.earthenspaces.com/dashboard?locale=en
      - submit_url     : https://cp.earthenspaces.com/admin/leads?locale=en
      - username       : Phone number (e.g. "8925820147")
      - password
      - crm_project_id : e.g. "66b072f69f967d7b4bc94288"
      - login_type     : "tel"  (IMPORTANT — uses phone number login)
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://cp.earthenspaces.com/users/sign_in?locale=en")
        config.setdefault("dashboard_url", "https://cp.earthenspaces.com/dashboard?locale=en")
        config.setdefault("submit_url",    "https://cp.earthenspaces.com/admin/leads?locale=en")
        config.setdefault("login_type",    "tel")
        super().__init__(config, session_manager=session_manager)

    def _fill_login_fields(self, page):
        """Override: Earthen Spaces uses a phone input and encrypted password field."""
        page.locator("input[type='tel']:visible").first.click()
        page.locator("input[type='tel']:visible").first.type(self.username, delay=100)

        page.locator("input[type='password']:visible").first.click()
        page.locator("input[type='password']:visible").first.type(self.password, delay=100)
