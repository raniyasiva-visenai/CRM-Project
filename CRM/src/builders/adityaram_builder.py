try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

import time
from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any

class AdityaramBuilder(BaseBuilder):
    """
    Adityaram Properties Channel Partner CRM Builder (Sell.do based).
    Flow:
    1. Login (Email -> Login with password -> Password)
    2. Navigate to Dashboard with remote-state for New Lead modal
    3. Fill Lead Details
    4. Save and Capture Response
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = config.get("login_url", "https://cp.adityaramproperties.com/users/sign_in")
        self.submit_url = config.get("submit_url", "https://cp.adityaramproperties.com/admin/cp_lead_activities?locale=en&remote-state=/admin/leads/new?locale=en")
        self.username = config.get("username")
        self.password = config.get("password")
        self.project_label = config.get("project", "Adityaram Golden Gate")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "Playwright not installed"}

        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            self.log("🚀 Launching browser for Adityaram Properties (Sell.do)...")
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

                self.log(f"📧 Entering email: {self.username}")
                email_field = page.locator("#user_email, input[name*='user[email]'], input[type='email']").first
                email_field.wait_for(state="visible", timeout=10000)
                email_field.fill(self.username)
                
                login_with_pwd = page.locator("a:has-text('Login with password'), .login-password-link, [data-event-name='Login with password']").first
                if login_with_pwd.is_visible(timeout=3000):
                    self.log("🔑 Clicking 'Login with password'...")
                    login_with_pwd.click()
                    time.sleep(1)

                self.log("✍️ Filling password...")
                pwd_field = page.locator("#user_password, input[name*='user[password]'], input[type='password']").first
                pwd_field.wait_for(state="visible", timeout=10000)
                pwd_field.fill(self.password)
                
                self.log("🖱️ Clicking Sign In...")
                sign_in_btn = page.locator("input[type='submit'][value='Sign In'], input[type='submit'][value='Login'], button[type='submit']").first
                sign_in_btn.click()
                
                # Wait for redirect
                page.wait_for_function("() => !window.location.href.includes('/users/sign_in')", timeout=30000)
                self.log(f"✅ Logged in! URL: {page.url}")

                # ── 2. NAVIGATE TO LEAD FORM ─────────────────────
                self.log(f"📋 Navigating to lead form: {self.submit_url}")
                page.goto(self.submit_url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(5) 
                
                # Manual trigger if modal doesn't open
                form_locator = page.locator("#lead_first_name").first
                if not form_locator.is_visible(timeout=5000):
                    add_btn = page.locator("a:has-text('Add Lead'), button:has-text('Add Lead'), .btn-primary:has-text('Add')").first
                    if add_btn.is_visible():
                        self.log("🖱️ Clicking 'Add Lead' manually...")
                        add_btn.click()
                        time.sleep(2)
                
                form_locator.wait_for(state="visible", timeout=15000)

                # ── 3. FILL LEAD DETAILS ─────────────────────────
                self.log(f"✍️ Filling lead: {lead.first_name}")
                page.locator("#lead_first_name").fill(lead.first_name or "")
                page.locator("#lead_last_name").fill(lead.last_name or "")
                if lead.email:
                    page.locator("#lead_email").fill(lead.email)
                
                phone_field = page.locator("#lead_phone").first
                phone_field.fill(lead.mobile or "")
                phone_field.dispatch_event("input")
                phone_field.dispatch_event("change")
                phone_field.dispatch_event("blur")
                
                # Project Dropdown
                self.log(f"🏢 Selecting project: {self.project_label}")
                try:
                    page.locator("#lead_project_id").select_option(label=self.project_label)
                except Exception as e:
                    self.log(f"⚠️ Project selection failed: {e}. Trying fallback index...")
                    page.locator("#lead_project_id").select_option(index=1)

                # Remarks
                remarks = f"{lead.remarks or ''} | Source: Marutham Properties".strip()
                try:
                    page.locator("#lead_remarks").fill(remarks)
                except:
                    pass

                # Capture Network Response
                captured = []
                def on_response(res):
                    if res.request.method == "POST":
                        captured.append(res)
                page.on("response", on_response)

                # ── 4. SUBMIT ─────────────────────────────────────
                self.log("💾 Clicking Save...")
                save_btn = page.locator("button.btn-primary:has-text('Save'), [type='submit']").last
                save_btn.scroll_into_view_if_needed()
                save_btn.click(force=True)
                
                time.sleep(10)

                # ── 5. PARSE RESULT ───────────────────────────────
                page_text = page.evaluate("() => document.body.innerText").lower()
                
                if "already exist" in page_text:
                    self.log("⚠️ Lead already exists.")
                    return {"success": True, "status": "DUPLICATE", "message": "Lead already exists"}

                if "added successfully" in page_text or "successfully" in page_text:
                    self.log("✅ Lead created successfully!")
                    return {"success": True, "status": "CREATED"}

                for r in reversed(captured):
                    try:
                        data = r.json()
                        msg = str(data.get("message", "")).lower()
                        if "added successfully" in msg or "success" in msg:
                            return {"success": True, "status": "CREATED", "response": data}
                        if "already exist" in msg or "duplicate" in msg:
                            return {"success": True, "status": "DUPLICATE", "response": data}
                    except:
                        pass

                if not form_locator.is_visible(timeout=1000):
                    self.log("✅ Modal closed — assuming success.")
                    return {"success": True, "status": "SUCCESS"}

                self.log("⚠️ Status unknown.")
                return {"success": False, "error": "Submission triggered but status unknown"}

            except Exception as e:
                self.log(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    def validate_session(self) -> bool:
        return False
