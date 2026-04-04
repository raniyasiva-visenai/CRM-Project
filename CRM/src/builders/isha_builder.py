try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any

class IshaBuilder(BaseBuilder):
    """
    Isha Homes Channel Partner CRM Builder.
    Uses Playwright to login and submit leads.
    
    Required config keys:
      - login_url  : https://ishahomes.co/CP_Lead/
      - submit_url : https://ishahomes.co/CP_Lead/Marketing_CPlead.aspx
      - username   : CP login username
      - password   : CP login password
      - project    : Project name substring (e.g. "SYMPHONY")
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = config.get("login_url", "https://ishahomes.co/CP_Lead/")
        self.submit_url = config.get("submit_url", "https://ishahomes.co/CP_Lead/Marketing_CPlead.aspx")
        self.username = config.get("username")
        self.password = config.get("password")
        self.project_match = config.get("project", "SYMPHONY")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "Playwright not installed"}

        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            self.log("🚀 Launching browser for Isha Homes submission...")
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

                if page.locator("input[type='password']").count() > 0:
                    self.log(f"👤 Logging in as: {self.username}")
                    page.locator("input[type='text'], input[name*='user']").first.fill(self.username)
                    page.locator("input[type='password']").first.fill(self.password)
                    page.locator("button:has-text('Sign In'), input[value='Sign In'], button[type='submit']").first.click()
                    page.wait_for_timeout(5000)
                
                # ── 2. NAVIGATE TO LEAD FORM ─────────────────────
                if "Marketing_CPlead.aspx" not in page.url:
                    self.log(f"📋 Navigating to leads form: {self.submit_url}")
                    page.goto(self.submit_url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(3000)

                if "CP_Lead" not in page.url or "Login" in page.url:
                    self.log("❌ Login failed or redirected to login.")
                    return {"success": False, "error": "Isha login failed"}

                # ── 3. FILL LEAD FORM ────────────────────────────
                full_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip()
                self.log(f"✍️ Filling lead: {full_name}")
                
                name_sel = "input[id*='txtclientname'], input[name*='client'], input[placeholder*='Name']"
                page.locator(name_sel).first.fill(full_name)
                
                # Country - Default India
                try:
                    page.locator("input[id*='rbtnIndia'], label:has-text('India')").first.click()
                except:
                    pass

                page.locator("input[id*='txtmobile'], input[name*='mobile']").first.fill(lead.mobile or "")
                page.locator("input[id*='txtemail'], input[name*='email']").first.fill(lead.email or "")
                
                # Project Dropdown (ASP.NET complex select)
                self.log(f"🏢 Selecting project matching: {self.project_match}")
                page.evaluate(f"""
                    (function() {{
                        var selects = document.querySelectorAll('select');
                        selects.forEach(function(sel) {{
                            for (var i = 0; i < sel.options.length; i++) {{
                                if (sel.options[i].text.toUpperCase().includes('{self.project_match.upper()}')) {{
                                    sel.selectedIndex = i;
                                    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                }}
                            }}
                        }});
                    }})();
                """)
                page.wait_for_timeout(500)

                # Remarks
                remarks = f"{lead.remarks or ''} | Source: Marutham Properties".strip()
                try:
                    page.locator("textarea[id*='txtremark'], textarea[name*='remark']").first.fill(remarks)
                except:
                    pass

                # Capture Network Response
                captured = []
                def on_response(res):
                    if res.request.method == "POST" and "CP_Lead" in res.url:
                        captured.append(res)
                page.on("response", on_response)

                # ── 4. SUBMIT ─────────────────────────────────────
                self.log("💾 Clicking Save...")
                save_sel = "input[type='submit'][value*='Save'], button:has-text('Save'), input[id*='btnsave']"
                page.locator(save_sel).first.click(force=True)
                page.wait_for_timeout(5000)

                # ── 5. PARSE RESULT ───────────────────────────────
                page_text = page.evaluate("() => document.body.innerText").lower()
                
                if "already exist" in page_text:
                    self.log("⚠️ Lead already exists in Isha CRM.")
                    return {"success": True, "status": "DUPLICATE", "message": "Lead already exists in Isha Homes CRM"}
                
                if "success" in page_text or "inserted" in page_text:
                    self.log("✅ Lead submitted successfully!")
                    return {"success": True, "status": "CREATED", "message": "Lead submitted to Isha Homes CRM"}

                # Check if form cleared
                client_val = page.evaluate("() => { var el = document.querySelector('input[id*=\"txtclientname\"]'); return el ? el.value : 'N/A'; }")
                if not client_val or client_val == "":
                    self.log("✅ Form cleared — assuming success.")
                    return {"success": True, "status": "CREATED", "message": "Lead submitted (form cleared)"}

                self.log("⚠️ Could not confirm submission status.")
                return {"success": False, "error": "Submission triggered but result unknown"}

            except Exception as e:
                self.log(f"❌ Error during Isha submission: {e}")
                try:
                    page.screenshot(path=f"isha_error_{lead.id}.png")
                except:
                    pass
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    def validate_session(self) -> bool:
        return False
