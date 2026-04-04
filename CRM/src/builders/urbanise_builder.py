try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any
import json

class UrbaniseBuilder(BaseBuilder):
    """
    Urbanise (Urbanrise Projects) Channel Partner CRM Builder.
    Uses Playwright to login and submit leads via the AngularJS web form.
    
    Required config keys:
      - login_url  : https://cpc.urbanriseprojects.in/
      - submit_url : https://cpc.urbanriseprojects.in/#!/leads
      - username   : CP login email
      - password   : CP login password
      - project    : Project value (e.g. "whispers_sky")
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = config.get("login_url", "https://cpc.urbanriseprojects.in/")
        self.submit_url = config.get("submit_url", "https://cpc.urbanriseprojects.in/#!/leads")
        self.username = config.get("username")
        self.password = config.get("password")
        self.project_val = config.get("project", "whispers_sky")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "Playwright not installed"}

        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            self.log("🚀 Launching browser for Urbanise submission...")
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
                page.fill("#email", self.username)
                page.fill("#password", self.password)
                page.click("#digit_login_signin_submit")
                page.wait_for_timeout(5000)

                if "/login" in page.url:
                    self.log("❌ Login failed — still on login page.")
                    return {"success": False, "error": "Urbanise login failed"}

                self.log(f"✅ Logged in! Current URL: {page.url}")
                
                # ── 2. NAVIGATE TO LEADS PAGE ────────────────────
                if "#!/leads" not in page.url:
                    self.log("🔄 Navigating to leads page...")
                    page.goto(self.submit_url, wait_until="networkidle", timeout=60000)
                    page.wait_for_timeout(3000)

                # ── 3. FILL INLINE LEAD FORM ─────────────────────
                full_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip()
                self.log(f"✍️ Filling lead: {full_name}")
                
                # Name
                name_sel = "input[placeholder*='Name'], input[ng-model*='name'], input[name*='name']"
                page.locator(name_sel).first.fill(full_name)
                
                # Mobile
                mobile_sel = "input[placeholder*='Mobile'], input[placeholder*='Phone'], input[placeholder*='Contact'], input[ng-model*='mobile']"
                page.locator(mobile_sel).first.fill(lead.mobile or "")
                page.wait_for_timeout(500)
                
                # Email
                if lead.email:
                    email_sel = "input[placeholder*='Email'], input[ng-model*='email'], input[type='email']"
                    try:
                        page.locator(email_sel).first.fill(lead.email)
                    except:
                        pass
                
                # Project Dropdown
                self.log(f"🏢 Selecting project: {self.project_val}")
                try:
                    proj_sel = "#select_project, select[name='project'], select[ng-model='project']"
                    page.locator(proj_sel).first.select_option(self.project_val)
                    page.wait_for_timeout(500)
                except Exception as e:
                    self.log(f"⚠️ Project selector error: {e}")

                # Capture responses
                captured = []
                def on_response(res):
                    if res.request.method in ["POST", "PUT"] and "leads" in res.url:
                        captured.append(res)
                page.on("response", on_response)

                # ── 4. SUBMIT ─────────────────────────────────────
                self.log("💾 Clicking Add...")
                add_btn = page.locator("button:has-text('Add'), input[value='Add'], .btn-primary:has-text('Add')").first
                add_btn.click(force=True)
                page.wait_for_timeout(5000)

                # ── 5. PARSE RESULT ───────────────────────────────
                # Check captured network responses first
                for r in reversed(captured):
                    try:
                        data = r.json()
                        self.log(f"📩 API Response captured: {r.status}")
                        # Urbanise AngularJS backend usually returns a JSON or 201
                        if r.status in [200, 201]:
                            return {"success": True, "status": "CREATED", "response": data}
                    except:
                        pass

                # Fallback: check page text for success/error
                page_text = page.evaluate("() => document.body.innerText").lower()
                if "success" in page_text or "added" in page_text:
                    self.log("✅ Success message detected on page.")
                    return {"success": True, "status": "SUCCESS", "message": "Lead submitted successfully"}
                
                if "already exist" in page_text or "duplicate" in page_text:
                    self.log("⚠️ Lead already exists.")
                    return {"success": True, "status": "DUPLICATE", "message": "Lead already exists in Urbanise CRM"}

                self.log("⚠️ Could not confirm submission status.")
                return {"success": False, "error": "Submission triggered but status unknown"}

            except Exception as e:
                self.log(f"❌ Error during Urbanise submission: {e}")
                try:
                    page.screenshot(path=f"urbanise_error_{lead.id}.png")
                except:
                    pass
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    def validate_session(self) -> bool:
        return False
