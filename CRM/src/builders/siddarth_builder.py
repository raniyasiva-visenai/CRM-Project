"""
Siddarth Housing CRM Builder (sidharth-housing.web.app)
Platform: Firebase Web App — Playwright UI automation
"""

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any


class SiddarthBuilder(BaseBuilder):
    """
    Siddarth (Sidharth) Housing Channel Partner CRM.
    Firebase-hosted web app with modal-based lead creation.

    Required config:
      - login_url  : https://sidharth-housing.web.app/
      - username / password
      - project    : e.g. "Crown"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = config.get("login_url", "https://sidharth-housing.web.app/")
        self.username  = config.get("username")
        self.password  = config.get("password")
        self.project   = config.get("project", "Crown")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "Playwright not installed"}

        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            self.log("🚀 Launching browser for Siddarth Housing submission...")
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
                self.log(f"🔐 Logging in to: {self.login_url}")
                page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                page.fill("input[name='email']", self.username)
                page.fill("input[name='password']", self.password)
                page.click("button[type='submit']")

                try:
                    page.wait_for_url("**/follow-up**", timeout=20000)
                    self.log(f"✅ Logged in: {page.url}")
                except Exception:
                    page.wait_for_timeout(4000)
                    self.log(f"⚠️ URL after login: {page.url}")

                # ── 2. OPEN ADD NEW → SINGLE LEAD ─────────────────
                self.log("🖱️ Clicking 'Add New'...")
                page.wait_for_selector("button:has-text('Add New')", state="visible", timeout=20000)
                page.click("button:has-text('Add New')")
                page.wait_for_timeout(1000)

                self.log("🖱️ Clicking 'Single Lead'...")
                page.wait_for_selector("#create-single-lead", state="visible", timeout=10000)
                page.click("#create-single-lead")

                # ── 3. WAIT FOR MODAL ─────────────────────────────
                self.log("⏳ Waiting for lead form modal...")
                modal_selector = "input[placeholder*='name' i]"
                try:
                    page.wait_for_selector(modal_selector, state="visible", timeout=10000)
                except Exception:
                    self.log("❌ Modal did not open")
                    return {"success": False, "error": "Siddarth lead modal did not open"}

                # ── 4. FILL FORM ──────────────────────────────────
                full_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip()
                self.log(f"✍️ Filling lead: {full_name}")

                self._fill_field(page, ["input[name='clientname']", "input[name='name']", "input[placeholder*='name' i]"], full_name, "name")
                self._fill_field(page, ["input[name='phoneNumber']", "input[name='phone']", "input[placeholder*='phone' i]"], lead.mobile or "", "phone")
                self._fill_field(page, ["input[name='email']", "input[type='email']", "input[placeholder*='email' i]"], lead.email or "", "email")

                # Project — combobox
                project_name = lead.project_name or self.project
                self._select_project(page, project_name)

                # ── 5. SUBMIT ─────────────────────────────────────
                self.log("💾 Clicking Submit...")
                submitted = False
                for sel in ["button[type='submit']", "button:has-text('Submit')", "button:has-text('Save')", "button:has-text('Add')", "button:has-text('Create')"]:
                    try:
                        page.wait_for_selector(sel, state="visible", timeout=3000)
                        page.click(sel)
                        submitted = True
                        self.log(f"✅ Clicked: {sel}")
                        break
                    except Exception:
                        continue

                if not submitted:
                    return {"success": False, "error": "Could not find submit button in Siddarth modal"}

                page.wait_for_timeout(3000)

                # ── 6. PARSE RESULT ───────────────────────────────
                body_text = page.evaluate("() => document.body.innerText.toLowerCase()")

                if any(w in body_text for w in ["success", "created", "added"]):
                    self.log("✅ Lead created successfully!")
                    return {"success": True, "status": "CREATED", "message": "Lead submitted to Siddarth Housing"}

                if "already exist" in body_text or "duplicate" in body_text:
                    self.log("⚠️ Duplicate lead")
                    return {"success": True, "status": "DUPLICATE"}

                if any(w in body_text for w in ["error", "invalid", "failed"]):
                    return {"success": False, "error": "Siddarth submission validation error"}

                # Assume success if modal closed
                try:
                    if not page.locator(modal_selector).is_visible(timeout=1000):
                        self.log("✅ Modal closed — assuming success")
                        return {"success": True, "status": "CREATED", "message": "Lead submitted to Siddarth Housing (modal closed)"}
                except Exception:
                    pass

                self.log("⚠️ Could not confirm submission")
                return {"success": False, "error": "Siddarth submission result unclear"}

            except Exception as e:
                self.log(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    def _fill_field(self, page, selectors, value, field_name):
        """Try multiple selectors to fill a field."""
        for sel in selectors:
            try:
                page.wait_for_selector(sel, state="visible", timeout=3000)
                page.fill(sel, value)
                self.log(f"✅ Filled {field_name}: {value}")
                return True
            except Exception:
                continue
        self.log(f"⚠️ Could not fill {field_name}")
        return False

    def _select_project(self, page, project_name):
        """Select project from combobox."""
        try:
            label = page.locator("label:text('Project Name')")
            label.wait_for(state="visible", timeout=5000)
            combobox = label.locator("xpath=following-sibling::div//button[@role='combobox']")
            combobox.click()
            page.wait_for_timeout(500)
            option = page.get_by_role("option", name=project_name)
            option.wait_for(state="visible", timeout=5000)
            option.click()
            self.log(f"✅ Selected Project: {project_name}")
        except Exception as e:
            self.log(f"⚠️ Could not select project: {e}")

    def validate_session(self) -> bool:
        return False
