"""
SIP (South India Properties) CRM Builder (southindiaprop.in)
Platform: ASP.NET WebForms — Playwright UI automation
Same structure as VNR Homes.
"""

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any


class SIPBuilder(BaseBuilder):
    """
    South India Properties (SIP) Channel Partner CRM.
    ASP.NET WebForms with Select2 and multiselect dropdowns.

    Required config:
      - login_url     : https://southindiaprop.in/cp_lead/default.aspx
      - submit_url    : https://southindiaprop.in/cp_lead/Marketing_CPlead.aspx
      - username / password
      - project       : e.g. "GREENPEARL"
      - location      : e.g. "ANNAMBEDU"
      - property_type : e.g. "Plots"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url     = config.get("login_url", "https://southindiaprop.in/cp_lead/default.aspx")
        self.submit_url    = config.get("submit_url", "https://southindiaprop.in/cp_lead/Marketing_CPlead.aspx")
        self.username      = config.get("username")
        self.password      = config.get("password")
        self.project       = config.get("project", "GREENPEARL")
        self.location      = config.get("location", "ANNAMBEDU")
        self.property_type = config.get("property_type", "Plots")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "Playwright not installed"}

        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            self.log("🚀 Launching browser for SIP submission...")
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                # ── 1. LOGIN ──────────────────────────────────────
                self.log(f"🌐 Navigating to login: {self.login_url}")
                page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)

                page.fill("input[name='txtusername']", self.username)
                page.fill("input[name='txtpassword']", self.password)
                page.click("input[name='btnSubmit']")

                page.wait_for_load_state("domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)

                self.log(f"📍 After login URL: {page.url}")

                # Navigate to lead form if not auto-redirected
                if "Marketing_CPlead" not in page.url:
                    self.log("⚠️ Navigating to lead page manually...")
                    page.goto(self.submit_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)

                # ── 2. WAIT FOR FORM ──────────────────────────────
                try:
                    page.wait_for_selector(
                        "input[name='ctl00$ContentPlaceHolder1$txtclientname']",
                        timeout=15000
                    )
                except Exception:
                    return {"success": False, "error": "SIP lead form not found"}

                # ── 3. FILL FORM ──────────────────────────────────
                full_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip()
                self.log(f"✍️ Filling lead: {full_name}")

                page.fill("input[name='ctl00$ContentPlaceHolder1$txtclientname']", full_name)

                # Country radio
                country = lead.country or "India"
                if country.lower() == "india":
                    page.check("input#ContentPlaceHolder1_rbtnIndia")
                else:
                    page.check("input#ContentPlaceHolder1_rbtnNRI")

                page.fill("input[name='ctl00$ContentPlaceHolder1$txtmobile']", lead.mobile or "")

                if lead.email:
                    page.fill("input[name='ctl00$ContentPlaceHolder1$txtemail']", lead.email)

                # Location — multiselect plugin
                location = lead.location or self.location
                if location:
                    self._multiselect_pick(page, "ContentPlaceHolder1_ddllocation", location)

                # Property type — Select2
                prop_type = lead.property_type or self.property_type
                if prop_type:
                    self._select2_pick(page, "select2-ContentPlaceHolder1_ddlproperty-container", prop_type)

                # Project — Select2
                project = lead.project_name or self.project
                if project:
                    self._select2_pick(page, "select2-ContentPlaceHolder1_ddlproject-container", project)

                # Remarks
                if lead.remarks:
                    page.fill("textarea[name='ctl00$ContentPlaceHolder1$txtremarks']", lead.remarks)

                # ── 4. SUBMIT ─────────────────────────────────────
                page.click("input[name='ctl00$ContentPlaceHolder1$txtclientname']")
                page.wait_for_timeout(500)

                self.log("💾 Clicking Save...")
                page.click("input[name='ctl00$ContentPlaceHolder1$btnlead']")
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)

                # ── 5. PARSE RESULT ───────────────────────────────
                body = page.inner_text("body")

                if "LeadID" in body and full_name in body:
                    self.log("✅ Lead submitted successfully!")
                    return {"success": True, "status": "CREATED", "message": "Lead submitted to SIP"}

                if any(w in body.lower() for w in ["success", "submitted", "saved", "thank"]):
                    self.log("✅ Lead submitted successfully!")
                    return {"success": True, "status": "CREATED", "message": "Lead submitted to SIP"}

                if "already exist" in body.lower() or "duplicate" in body.lower():
                    self.log("⚠️ Duplicate lead")
                    return {"success": True, "status": "DUPLICATE", "message": "Lead already exists in SIP"}

                if any(w in body.lower() for w in ["error", "invalid", "required"]):
                    return {"success": False, "error": f"SIP validation error: {body[:200]}"}

                # Check if form was reset
                try:
                    client_val = page.evaluate(
                        "() => { var el = document.querySelector(\"input[name='ctl00$ContentPlaceHolder1$txtclientname']\"); return el ? el.value : ''; }"
                    )
                    if not client_val:
                        self.log("✅ Form cleared — lead submitted!")
                        return {"success": True, "status": "CREATED", "message": "Lead submitted to SIP"}
                except Exception:
                    pass

                self.log("⚠️ Could not confirm submission")
                return {"success": False, "error": "Unclear SIP submission result"}

            except Exception as e:
                self.log(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    def _select2_pick(self, page, container_id, search_text):
        """Select a value in a Select2 dropdown."""
        try:
            page.click(f"span#{container_id}")
            page.wait_for_timeout(500)
            page.fill(".select2-search__field", search_text)
            page.wait_for_timeout(800)
            try:
                page.click(".select2-results__option--highlighted", timeout=5000)
            except Exception:
                page.keyboard.press("Enter")
            page.wait_for_timeout(300)
        except Exception as e:
            self.log(f"⚠️ Select2 pick failed for '{search_text}': {e}")

    def _multiselect_pick(self, page, select_id, value):
        """Select a value in a multiselect dropdown via JS."""
        try:
            page.evaluate(f"""() => {{
                const sel = document.getElementById('{select_id}');
                for (let opt of sel.options) {{
                    if (opt.value === '{value}') {{
                        opt.selected = true;
                        sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        break;
                    }}
                }}
            }}""")
            page.wait_for_timeout(300)
            try:
                page.click(f"button.multiselect-option[title='{value}']", timeout=3000)
                page.wait_for_timeout(300)
                page.keyboard.press("Escape")
            except Exception:
                pass
        except Exception as e:
            self.log(f"⚠️ Multiselect pick failed for '{value}': {e}")

    def validate_session(self) -> bool:
        return False
