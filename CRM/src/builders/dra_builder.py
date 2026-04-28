from src.builders.selldo_rails_base import SellDoRailsBase
from src.models.lead import Lead
from typing import Dict, Any

class DRABuilder(SellDoRailsBase):
    """
    DRA Homes (Iris) CRM Builder.
    Inherits from SellDoRailsBase to handle the Rails-based CP portal.
    """
    def __init__(self, config: Dict[str, Any], session_manager=None):
        # Use submit_url from DB as login_url if it looks like a login/admin page
        db_url = config.get("submit_url", "")
        if "users" in db_url or "sign_in" in db_url or "admin" in db_url:
            config["login_url"] = db_url

        if not config.get("login_url"):
            config["login_url"] = "https://cp-iris.drahomes.in/users/sign_in?locale=en"
        if not config.get("dashboard_url"):
            config["dashboard_url"] = "https://cp-iris.drahomes.in/dashboard?locale=en"
        if not config.get("submit_url"):
            config["submit_url"] = "https://cp-iris.drahomes.in/admin/leads?locale=en"
        
        super().__init__(config, session_manager=session_manager)

    def _fill_login_fields(self, page):
        """DRA specific login handling using proven POC evaluate-based filling."""
        try:
            # 1. Wait for page to initialize (from POC)
            self.log("⏳ Waiting for page initialization...")
            page.wait_for_timeout(3000)
            
            # 2. Fill Email via JS (from POC)
            self.log(f"⌨️ Filling email: {self.username}")
            page.evaluate(
                """([sel, val]) => {
                    const el = document.querySelector(sel);
                    if(el) {
                        el.value = val;
                        el.dispatchEvent(new Event('input',  {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                        return true;
                    }
                    return false;
                }""",
                ["#user_login", self.username]
            )
            page.wait_for_timeout(500)

            # 3. Fill Password via JS (from POC)
            self.log("⌨️ Filling password...")
            page.evaluate(
                """([sel, val]) => {
                    const el = document.querySelector(sel);
                    if(el) {
                        el.value = val;
                        el.dispatchEvent(new Event('input',  {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                        return true;
                    }
                    return false;
                }""",
                ["#user_password", self.password]
            )
            page.wait_for_timeout(500)
            
        except Exception as e:
            self.log(f"⚠️ DRA Login Fill Error: {e}")
            super()._fill_login_fields(page)
            
        except Exception as e:
            self.log(f"⚠️ DRA Login Fill Error: {e}")
            super()._fill_login_fields(page)

    def _build_payload(self, lead: Lead, csrf: str) -> Dict[str, str]:
        """Customizing payload for DRA requirements."""
        payload = super()._build_payload(lead, csrf)
        
        # DRA specific fields from POC
        payload.update({
            "lead[property_type]": lead.project_type or "Residential",  # Default if missing
            "lead[resident_type]": "Indian",                            # Standard for most leads
            "lead[remarks]":       lead.remarks or "Lead from Marutham Properties",
        })
        
        # Ensure project_id is prioritized from lead if provided
        if lead.project_id:
            payload["lead[project_id]"] = lead.project_id
            
        return payload
