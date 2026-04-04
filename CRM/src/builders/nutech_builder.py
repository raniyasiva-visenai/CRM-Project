"""
Nutech CRM Builder (cp.nutechprojects.in)
Platform: Rails/Sell.do — CSRF + fetch POST
"""

from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any


class NutechBuilder(SellDoRailsBase):
    """
    Nutech Channel Partner CRM.

    Required config:
      - login_url      : https://cp.nutechprojects.in/users/sign_in?locale=en
      - dashboard_url  : https://cp.nutechprojects.in/dashboard?locale=en
      - submit_url     : https://cp.nutechprojects.in/admin/leads?locale=en
      - username / password
      - crm_project_id : e.g. "6840237febfeca1e0c66ccd7"
      - login_type     : email
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("login_url",     "https://cp.nutechprojects.in/users/sign_in?locale=en")
        # Nutech often needs to load the lead form state to get a valid CSRF or session state
        config.setdefault("dashboard_url", "https://cp.nutechprojects.in/dashboard?locale=en&remote-state=/admin/leads/new?locale=en")
        config.setdefault("submit_url",    "https://cp.nutechprojects.in/admin/leads?locale=en")
        config.setdefault("login_type",    "email")
        super().__init__(config, session_manager=session_manager)

    def _fill_login_fields(self, page):
        """Special login for Nutech: must click 'Email' tab first."""
        try:
            # Try multiple selectors for the Email tab as seen in POC
            for sel in ["label:has-text('Email')", "a:has-text('Email')", "li:has-text('Email')", "text=Email"]:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    self.log(f"🔗 Clicking '{sel}' tab...")
                    el.click()
                    page.wait_for_timeout(1000)
                    break
        except Exception as e:
            self.log(f"⚠️  Note: Could not toggle to Email tab: {e}")

        # Now fill standard fields (SellDoRailsBase will handle it if we call super or just do it here)
        page.wait_for_selector("#user_login", state="visible", timeout=5000)
        page.fill("#user_login", self.username)
        page.fill("#user_password", self.password)
