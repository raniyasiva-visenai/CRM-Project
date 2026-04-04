try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any

class SalesRobotBuilder(BaseBuilder):
    """
    SalesRobot CRM Builder Implementation.
    Handles multi-step UI interaction: login, session popups, and enquiry creation.
    """
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = config.get("login_url", "https://www.thesalezrobot.com/public/login")
        self.username = config.get("username")
        self.password = config.get("password")
        self.company_name = config.get("company_name", "LS")
        self.enquiry_url = config.get("submit_url")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        with sync_playwright() as p:
            self.log("🚀 Launching browser for SalesRobot submission...")
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                # 1. Login
                self.log(f"🌐 Navigating to login: {self.login_url}")
                page.goto(self.login_url, wait_until="networkidle")

                self.log(f"🏢 Entering company: {self.company_name}")
                page.fill("#companyname", self.company_name)
                page.wait_for_timeout(1000)
                
                self.log(f"👤 Entering credentials for: {self.username}")
                page.fill("#email", self.username)
                page.wait_for_timeout(500)
                page.fill("#password", self.password)
                page.wait_for_timeout(500)
                
                # Double check
                val = page.evaluate("() => document.querySelector('#email').value")
                if not val:
                    self.log("⚠️ Fields were cleared, re-filling...")
                    page.fill("#email", self.username)
                    page.fill("#password", self.password)

                page.click(".loginsubmit")
                
                # Wait for redirect or error
                try:
                    page.wait_for_url("**/admin**", timeout=15000)
                    self.log("✅ SalesRobot Login redirect successful!")
                except:
                    if "/login" in page.url:
                        self.log("⚠️ Login still on login page. Capturing debug info...")
                        page.screenshot(path=f"salesrobot_login_fail_{lead.leadsource_id}.png")
                        error_text = page.evaluate("() => document.body.innerText.split('\\n').filter(t => t.toLowerCase().includes('error') || t.toLowerCase().includes('invalid')).join(' | ')")
                        self.log(f"Login failure text: {error_text or 'No visible error message'}")
                    else:
                        self.log(f"❓ Unexpected URL after login: {page.url}")

                # Handle existing session popup
                try:
                    popup_yes = page.locator("button:has-text('Yes')")
                    if popup_yes.is_visible(timeout=3000):
                        self.log("🔔 Handling existing session popup...")
                        popup_yes.click()
                        # page.wait_for_timeout(2000)
                except:
                    pass

                self.log("⏳ Waiting for final dashboard load...")
                try:
                    page.wait_for_url("**/admin**", timeout=10000)
                except:
                    page.wait_for_timeout(3000)

                # 2. Navigate to Enquiry Create
                self.log(f"📋 Navigating to Enquiry Edit: {self.enquiry_url}")
                page.goto(self.enquiry_url, wait_until="networkidle")
                page.wait_for_timeout(3000)

                # 3. Fill Form
                self.log(f"✍️ Filling lead: {lead.salutation} {lead.first_name}")
                page.screenshot(path=f"salesrobot_debug_{lead.leadsource_id}.png")
                
                # Salutation (Name Prefix) - using text matcher
                if lead.salutation:
                    try:
                        page.click('span.select2-selection--single:has-text("Mr.")') # Default is Mr.
                        page.wait_for_selector(f"li.select2-results__option:has-text('{lead.salutation}')", state="visible")
                        page.click(f"li.select2-results__option:has-text('{lead.salutation}')")
                    except:
                        pass # Carry on if salutation selection fails

                page.fill("input[name='firstname'], input[name='enquiry_name'], input.massedit_enquiry_name", lead.first_name)

                self.log(f"📱 Filling mobile: {lead.mobile}")
                # Mobile Prefix is usually +91, handled by default or could be mapped if needed
                page.fill("input[name='mobile'], input[name='mobileno'], input.massedit_enquiry_mobileno", lead.mobile)

                # Interested Project (Select2)
                # Prioritize project_name from config (from DB builder_projects table)
                project_name = self.config.get("project_name") or lead.project_type or "Lifestyle Vardaan"
                self.log(f"🏢 Selecting project: {project_name}")
                page.click('span.select2-selection--single:has-text("Select An Option")')
                page.wait_for_selector("input.select2-search__field", state="visible")
                page.type("input.select2-search__field", project_name, delay=100)
                page.wait_for_selector(f"li.select2-results__option:has-text('{project_name}')", state="visible")
                page.click(f"li.select2-results__option:has-text('{project_name}')")

                # Internal Info Mapping
                if lead.source:
                    self.log(f"🔍 Mapping Enquire Source: {lead.source}")
                    try:
                        # Enquire Source is the second 'Channel Partner' dropdown (approx)
                        # Better to use text matcher for the specific sections if possible
                        # But for now, we'll try to find the one related to Source
                        # The audit showed Enquire Source is a Select2.
                        # We'll stick to defaults unless explicitly asked for complex mapping
                        pass 
                    except:
                        pass

                page.wait_for_timeout(2000)

                # 4. Save
                self.log("🖱️ Clicking Save...")
                page.locator("button.ModuleSubmit:has-text('Save')").first.click()

                self.log("⏳ Waiting for save completion...")
                page.wait_for_timeout(8000)

                final_url = page.url
                self.log(f"🏁 Final URL: {final_url}")
                
                if "view=Detail" in final_url or "view=List" in final_url:
                    self.log(f"✅ Lead successfully submitted. Final URL: {final_url}")
                    return {
                        "success": True,
                        "status": "CREATED",
                        "message": "Enquiry created successfully on SalesRobot",
                        "final_url": final_url
                    }
                else:
                    self.log(f"⚠️ Unexpected final URL: {final_url}")
                    return {
                        "success": False,
                        "error": "Submission failed to redirect to Detail/List view",
                        "final_url": final_url
                    }

            except Exception as e:
                self.log(f"❌ Error during submission: {e}")
                try:
                    with open("salesrobot_dump.txt", "w", encoding="utf-8") as f:
                        f.write(page.content())
                except: pass
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                browser.close()

    def validate_session(self) -> bool:
        """For now, we re-login for every submission in UI mode."""
        return False
