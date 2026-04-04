"""
TVS Emerald CRM Builder (tvsemeraldpartnerclub.com)
Platform: Salesforce Experience Cloud (Aura framework)
Requires Playwright for full UI interaction.
"""

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any


class TVSBuilder(BaseBuilder):
    """
    TVS Emerald Channel Partner CRM.
    Salesforce Lightning form — requires full UI interaction.

    Required config:
      - login_url    : https://www.tvsemeraldpartnerclub.com/login
      - submit_url   : https://www.tvsemeraldpartnerclub.com/s/createrecord/CPSiteVisit
      - username / password
      - project      : Project name to select (e.g. "TVS Emerald Luxor")
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url  = config.get("login_url", "https://www.tvsemeraldpartnerclub.com/login")
        self.submit_url = config.get("submit_url", "https://www.tvsemeraldpartnerclub.com/s/createrecord/CPSiteVisit")
        self.base_url   = config.get("base_url", "https://www.tvsemeraldpartnerclub.com")
        self.username   = config.get("username")
        self.password   = config.get("password")
        self.project    = config.get("project", "TVS Emerald Luxor")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "Playwright not installed"}

        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            self.log("🚀 Launching browser for TVS Emerald submission...")
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
                page.goto(self.login_url, wait_until="networkidle", timeout=60000)

                self.log(f"👤 Logging in as: {self.username}")
                page.fill("#username", self.username)
                page.wait_for_timeout(500)
                page.fill("#password", self.password)
                page.wait_for_timeout(500)
                page.click("#Login")

                try:
                    page.wait_for_url(
                        lambda url: "login" not in url.lower() and "frontdoor" not in url.lower(),
                        timeout=30000
                    )
                except Exception:
                    pass

                page.wait_for_timeout(5000)

                if "login" in page.url.lower():
                    self.log("❌ TVS Login failed")
                    return {"success": False, "error": "TVS Emerald login failed — check credentials"}

                self.log(f"✅ Logged in: {page.url}")

                # ── 2. NAVIGATE TO SITE VISIT FORM ────────────────
                self.log(f"📋 Navigating to form: {self.submit_url}")
                page.goto(self.submit_url, wait_until="domcontentloaded")
                page.wait_for_timeout(6000)

                # ── 3. FILL FORM ──────────────────────────────────
                self.log(f"✍️ Filling lead: {lead.first_name} {lead.last_name or ''}")

                # Lightning form fields (label-based)
                try:
                    page.get_by_label("First Name").fill(lead.first_name or "")
                except Exception:
                    self.log("⚠️ Could not fill First Name via label")

                try:
                    page.get_by_label("Last Name").fill(lead.last_name or "")
                except Exception:
                    pass

                try:
                    page.get_by_label("Mobile").fill(lead.mobile or "")
                except Exception:
                    pass

                try:
                    page.get_by_label("Email").fill(lead.email or "")
                except Exception:
                    pass

                # Full Name (may not auto-calculate)
                try:
                    full_name = f"{lead.salutation or 'Mr'} {lead.first_name or ''} {lead.last_name or ''}".strip()
                    full_name_input = page.locator("//label[contains(., 'Full Name')]/..//input").first
                    if full_name_input.is_visible():
                        full_name_input.fill(full_name)
                except Exception:
                    pass

                # Scroll to reveal remaining fields
                page.evaluate("window.scrollBy(0, 500)")
                page.wait_for_timeout(1000)

                # Budget combobox
                try:
                    budget = page.get_by_role("combobox", name="Budget").first
                    if budget.is_visible():
                        budget.click(force=True)
                        page.wait_for_timeout(500)
                        page.keyboard.press("ArrowDown")
                        page.keyboard.press("ArrowDown")
                        page.keyboard.press("Enter")
                except Exception:
                    pass

                # SFT Range
                try:
                    sft = page.get_by_role("combobox", name="SFT Range").first
                    if sft.is_visible():
                        sft.click(force=True)
                        page.wait_for_timeout(500)
                        page.keyboard.press("ArrowDown")
                        page.keyboard.press("ArrowDown")
                        page.keyboard.press("Enter")
                except Exception:
                    pass

                # Property type
                try:
                    bhk = lead.bhk_type or "2 BHK"
                    page.locator(f"text='{bhk}'").first.click(force=True)
                    page.wait_for_timeout(500)
                    page.locator("button[title*='Chosen'], button[title*='Move selected']").first.click(force=True)
                    page.wait_for_timeout(500)
                except Exception:
                    pass

                # Project Interested
                try:
                    project_name = lead.project_name or self.project
                    project_input = (
                        page.locator("input[placeholder='Select Project Interested']")
                        .or_(page.locator("//label[contains(., 'Project Interested')]/..//button"))
                        .or_(page.locator("button[aria-label*='Project']"))
                    ).first
                    if project_input.is_visible():
                        project_input.click(force=True, timeout=5000)
                        page.wait_for_timeout(1000)
                        page.locator(f"text='{project_name}'").first.click(force=True)
                except Exception:
                    pass

                # ── 4. CAPTURE RESPONSE & SUBMIT ──────────────────
                captured_responses = []
                def handle_response(res):
                    if res.request.method == "POST" and ("aura" in res.url or "save" in res.url.lower()):
                        captured_responses.append(res)
                page.on("response", handle_response)

                self.log("💾 Clicking Save...")
                try:
                    save_btn = page.locator(
                        "button:has-text('Save'), button:has-text('Submit'), button[title='Save']"
                    ).first
                    if save_btn.is_visible(timeout=5000):
                        page.mouse.click(10, 10)  # blur
                        page.wait_for_timeout(1000)
                        save_btn.scroll_into_view_if_needed()
                        save_btn.evaluate("el => el.click()")
                except Exception as e:
                    self.log(f"⚠️ Save button click issue: {e}")

                page.wait_for_timeout(5000)

                # ── 5. PARSE RESULT ───────────────────────────────
                # Check toast message
                try:
                    toast = page.locator(".forceToastMessage, .toastMessage, .slds-notify_toast, [role='alert']").first
                    if toast.is_visible(timeout=2000):
                        toast_text = toast.inner_text()
                        self.log(f"🔔 Toast: {toast_text}")
                        if "success" in toast_text.lower() or "created" in toast_text.lower():
                            return {"success": True, "status": "CREATED", "message": f"TVS: {toast_text}"}
                        if "error" in toast_text.lower():
                            return {"success": False, "error": f"TVS: {toast_text}"}
                except Exception:
                    pass

                # Check network response
                if captured_responses:
                    last_resp = captured_responses[-1]
                    if last_resp.status == 200:
                        self.log("✅ Lead submitted to TVS (200 response)")
                        return {"success": True, "status": "CREATED", "message": "Lead submitted to TVS Emerald"}

                self.log("⚠️ Could not confirm TVS submission")
                return {"success": False, "error": "TVS submission result unclear"}

            except Exception as e:
                self.log(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    def validate_session(self) -> bool:
        return False
