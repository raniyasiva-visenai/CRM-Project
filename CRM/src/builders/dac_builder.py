try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any


class DACBuilder(BaseBuilder):
    """
    DAC Promoters Channel Partner CRM Builder.
    Uses Playwright to login and submit leads via the ASP.NET web form.

    Required config keys (from DB extra_config):
      - login_url   : http://dacpromoters.net/CP_Lead/Default.aspx
      - submit_url  : http://dacpromoters.net/CP_Lead/Marketing_CPlead.aspx
      - username    : CP login email
      - password    : CP login password
      - project     : Project name as it appears in the CRM dropdown (e.g. "AEROPOLIS")
      - location    : Location tag to select (e.g. "Chromepet")
      - property_type: e.g. "Apartments"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url   = config.get("login_url", "http://dacpromoters.net/CP_Lead/Default.aspx")
        self.submit_url  = config.get("submit_url", "http://dacpromoters.net/CP_Lead/Marketing_CPlead.aspx")
        self.username    = config.get("username")
        self.password    = config.get("password")
        self.project     = config.get("project", "AEROPOLIS")
        self.location    = config.get("location", "Chromepet")
        self.property_type = config.get("property_type", "Apartments")

    # ──────────────────────────────────────────────────────────────
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            self.log("🚀 Launching browser for DAC Promoters submission...")
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                # ── 1. LOGIN ──────────────────────────────────────
                self.log(f"🌐 Navigating to login: {self.login_url}")
                page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)

                self.log(f"👤 Logging in as: {self.username}")
                page.fill("#txtusername", self.username)
                page.wait_for_timeout(300)
                page.fill("#txtpassword", self.password)
                page.wait_for_timeout(300)
                page.click("#btnSubmit")
                page.wait_for_timeout(4000)

                if "Default.aspx" in page.url and "ReturnUrl" not in page.url:
                    self.log("❌ Login failed — still on login page.")
                    return {"success": False, "error": "DAC login failed — bad credentials or account locked"}

                self.log(f"✅ Logged in: {page.url}")

                # ── 2. NAVIGATE TO FORM ───────────────────────────
                self.log(f"📋 Navigating to lead form: {self.submit_url}")
                page.goto(self.submit_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                if "Default.aspx" in page.url:
                    self.log("❌ Redirected to login — session not established.")
                    return {"success": False, "error": "DAC session not established after login"}

                # ── 3. FILL FORM ──────────────────────────────────
                full_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip()
                self.log(f"✍️ Filling lead: {full_name}")

                page.fill("#ContentPlaceHolder1_txtclientname", full_name)
                page.click("#ContentPlaceHolder1_rbtnIndia", force=True)  # Default India
                page.fill("#ContentPlaceHolder1_txtmobile", lead.mobile or "")
                page.fill("#ContentPlaceHolder1_txtemail", lead.email or "")

                # Location — backed by Select2, set via JS
                location_val = self.location
                self.log(f"📍 Selecting location: {location_val}")
                page.evaluate(f"""
                    var sel = document.getElementById('ContentPlaceHolder1_ddllocation');
                    if (sel) {{
                        for (var i = 0; i < sel.options.length; i++) {{
                            if (sel.options[i].text.trim().toLowerCase().includes('{location_val.lower()}')) {{
                                sel.selectedIndex = i;
                                sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                break;
                            }}
                        }}
                    }}
                """)
                page.wait_for_timeout(500)

                # Property Type — set via JS
                prop_val = self.property_type
                self.log(f"🏠 Selecting property type: {prop_val}")
                page.evaluate(f"""
                    var sel = document.getElementById('ContentPlaceHolder1_ddlproperty');
                    if (sel) {{
                        for (var i = 0; i < sel.options.length; i++) {{
                            if (sel.options[i].text.trim().toLowerCase().includes('{prop_val.lower()}')) {{
                                sel.selectedIndex = i;
                                sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                break;
                            }}
                        }}
                    }}
                """)

                # Remarks
                remarks = f"Lead from Marutham Properties - Source: {lead.source or 'Website'}"
                page.fill("#ContentPlaceHolder1_txtremarks", remarks)

                # Project — scan all selects since ASP.NET ID varies
                proj_val = self.project
                self.log(f"🏢 Selecting project: {proj_val}")
                page.evaluate(f"""
                    (function() {{
                        var selects = document.querySelectorAll('select');
                        selects.forEach(function(sel) {{
                            for (var i = 0; i < sel.options.length; i++) {{
                                if (sel.options[i].text.trim().toUpperCase().includes('{proj_val.upper()}')) {{
                                    sel.selectedIndex = i;
                                    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                }}
                            }}
                        }});
                    }})();
                """)
                page.wait_for_timeout(500)

                # ── 4. CAPTURE RESPONSE & SAVE ────────────────────
                captured_responses = []
                def on_response(res):
                    if res.request.method == "POST" and "CP_Lead" in res.url:
                        captured_responses.append(res)
                page.on("response", on_response)

                # Scroll save button into view
                save_btn = page.locator("#ContentPlaceHolder1_btnlead")
                save_btn.scroll_into_view_if_needed()
                page.mouse.click(10, 10)  # blur any open dropdowns
                page.wait_for_timeout(500)
                self.log("💾 Clicking Save...")
                save_btn.click(force=True)
                page.wait_for_timeout(5000)

                # ── 5. PARSE RESULT ───────────────────────────────
                # Check for duplicate error message
                try:
                    page_text = page.evaluate("() => document.body.innerText")
                except:
                    page_text = ""

                if "already exist" in page_text.lower():
                    self.log("⚠️ Lead already exists in DAC CRM.")
                    return {
                        "success": True,   # Treat as success — lead is in system
                        "status": "DUPLICATE",
                        "message": "Lead already exists in DAC Promoters CRM"
                    }

                # Check for visible validation errors
                try:
                    err_el = page.locator("[style*='color:red'], .text-danger, .alert-danger").first
                    if err_el.is_visible(timeout=1000):
                        err_msg = err_el.inner_text()
                        self.log(f"❌ Validation error: {err_msg}")
                        return {"success": False, "error": f"Validation: {err_msg}"}
                except:
                    pass

                # If POST response was captured, check status
                if captured_responses:
                    status = captured_responses[-1].status
                    self.log(f"📩 POST response status: {status}")
                    if status == 200:
                        self.log("✅ Lead submitted successfully to DAC Promoters!")
                        return {
                            "success": True,
                            "status": "CREATED",
                            "message": "Lead submitted to DAC Promoters CRM"
                        }

                # Default: check if form was reset (new blank form = success)
                client_val = page.evaluate(
                    "() => { var el = document.getElementById('ContentPlaceHolder1_txtclientname'); return el ? el.value : ''; }"
                )
                if not client_val:
                    self.log("✅ Form cleared after save — lead submitted successfully!")
                    return {
                        "success": True,
                        "status": "CREATED",
                        "message": "Lead submitted to DAC Promoters CRM"
                    }

                self.log("⚠️ Could not confirm lead submission.")
                return {
                    "success": False,
                    "error": "Could not confirm lead was saved — check DAC portal manually"
                }

            except Exception as e:
                self.log(f"❌ Error: {e}")
                try:
                    page.screenshot(path=f"dac_error_{lead.leadsource_id}.png")
                except:
                    pass
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    # ──────────────────────────────────────────────────────────────
    def validate_session(self) -> bool:
        """DAC uses per-request Playwright login — no persistent session."""
        return False
