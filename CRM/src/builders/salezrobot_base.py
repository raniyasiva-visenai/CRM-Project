try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any
import time

class SalezRobotBase(BaseBuilder):
    """
    Base class for SalezRobot (thesalezrobot.com) CRM implementations.
    Handles multi-step UI interaction with robust event triggering.
    """
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = config.get("login_url", "https://www.thesalezrobot.com/public/login")
        self.username = config.get("username")
        self.password = config.get("password")
        self.company_name = config.get("company_name")
        self.enquiry_url = config.get("submit_url", "https://www.thesalezrobot.com/public/admin?Module=Enquiry&view=Edit")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "playwright not installed"}

        with sync_playwright() as p:
            self.log(f"🚀 Launching browser for {self.__class__.__name__}...")
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                # 1. Login
                self.log(f"🔐 Logging in to {self.login_url} (Company: {self.company_name})")
                page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
                
                page.wait_for_selector("#companyname", timeout=10000)
                page.fill("#companyname", self.company_name)
                page.fill("#email",       self.username)
                page.fill("#password",    self.password)
                page.click(".loginsubmit")
                
                # Handle session popup
                try:
                    page.wait_for_selector(".ajs-ok, button:has-text('Yes')", timeout=7000)
                    page.locator(".ajs-ok, button:has-text('Yes')").first.click()
                    time.sleep(2)
                except:
                    pass

                page.wait_for_url("**/admin/Dashboard**", timeout=30000)
                self.log("✅ Logged in successfully!")

                # 2. Go to Enquiry Form
                self.log(f"🔄 Loading enquiry form: {self.enquiry_url}")
                page.goto(self.enquiry_url, wait_until="networkidle", timeout=60000)
                time.sleep(2)

                # 3. Fill Fields
                self.log(f"📝 Filling lead: {lead.first_name}")
                
                # Helper for keyboard simulation
                def keyboard_fill(field_name, value):
                    try:
                        loc = page.locator(f"input[name='{field_name}'], textarea[name='{field_name}']").first
                        loc.wait_for(state="visible", timeout=10000)
                        loc.click()
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Delete")
                        loc.type(value, delay=30)
                        # Trigger JS events
                        loc.evaluate("(el) => { el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); el.dispatchEvent(new Event('blur', {bubbles:true})); }")
                        return True
                    except Exception as e:
                        self.log(f"⚠️ Error filling {field_name}: {e}")
                        return False

                # Helper for Select2
                def select2_fill(field_name, option_text):
                    try:
                        result = page.evaluate(f"""
                            () => {{
                                const sel = document.querySelector('select[name="{field_name}"]');
                                if (!sel) return {{ ok: false, reason: 'select not found' }};
                                const opts = Array.from(sel.options);
                                const query = '{option_text.lower()}';
                                const match = opts.find(o =>
                                    o.text.toLowerCase().replace(/\\s+/g, ' ').trim().includes(query) ||
                                    o.value.toLowerCase().includes(query)
                                );
                                if (!match) return {{ ok: false, reason: 'no match', options: opts.map(o => o.text.trim()) }};
                                sel.value = match.value;
                                sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                if (window.jQuery) {{
                                    jQuery(sel).trigger('change.select2');
                                    jQuery(sel).trigger('change');
                                }}
                                return {{ ok: true, selected: match.text.trim() }};
                            }}
                        """)
                        if result["ok"]:
                            self.log(f"✅ {field_name} set to: {result['selected']}")
                            return True
                        else:
                            self.log(f"❌ {field_name} match failed. Available: {result.get('options', [])[:5]}...")
                            return False
                    except Exception as e:
                        self.log(f"⚠️ Select2 error for {field_name}: {e}")
                        return False

                # Map Lead to SalesRobot names
                keyboard_fill("enquiry_name",        lead.first_name)
                keyboard_fill("enquiry_mobileno",    lead.mobile)
                keyboard_fill("enquiry_email",       lead.email)
                if lead.description:
                    keyboard_fill("enquiry_description", lead.description)

                # Project Selection (Builder Project from config or Lead project_type)
                project_name = self.config.get("project_name") or lead.project_type or "Crystal_Crown"
                select2_fill("enquiry_interestedproject", project_name)
                
                # Medium & Source
                select2_fill("enquiry_enquiremedium", "Channel Partner")
                select2_fill("enquiry_enquiresource", "Channel Partner")

                # 4. Submit
                self.log("💾 Clicking Save...")
                page.click("button.ModuleSubmit, button:has-text('Save')")
                time.sleep(5)

                final_url = page.url
                self.log(f"📍 Final URL: {final_url}")

                if "view=Detail" in final_url or "view=List" in final_url:
                    self.log("✨ SUCCESS: Lead submitted!")
                    return {
                        "success": True,
                        "status": "CREATED",
                        "message": "Lead submitted successfully",
                        "final_url": final_url
                    }
                else:
                    # Check for explicit errors
                    errors = page.evaluate("""
                        () => Array.from(document.querySelectorAll('.error, .alert, .invalid-feedback, [class*="error"], [class*="alert"]'))
                              .map(el => el.innerText.trim())
                              .filter(t => t.length > 0 && t.length < 300)
                              .slice(0, 5)
                    """)
                    error_msg = " | ".join(errors) if errors else "Submission failed to redirect"
                    self.log(f"⚠️ Errors detected: {error_msg}")
                    
                    # Duplicate check
                    if "Duplicate" in error_msg:
                        return {
                            "success": True,
                            "status": "DUPLICATE",
                            "message": "Lead already exists in SalezRobot",
                            "final_url": final_url
                        }
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "final_url": final_url
                    }

            except Exception as e:
                self.log(f"❌ Critical error: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    def validate_session(self) -> bool:
        return False
