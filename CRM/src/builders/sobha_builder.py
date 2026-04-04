"""
Sobha Developers CRM Builder (sobha-developers.my.site.com)
Platform: Salesforce Experience Cloud
Requires Playwright for full UI interaction.
"""

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any


class SobhaBuilder(BaseBuilder):
    """
    Sobha Developers Channel Partner CRM.
    Salesforce Community Portal — requires UI interaction.

    Required config:
      - login_url  : https://sobha-developers.my.site.com/cpportal/s/
      - submit_url : https://sobha-developers.my.site.com/cpportal/s/  (same page, flow-based)
      - username / password
      - project    : e.g. "Sobha Arbor Chennai"
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url  = config.get("login_url", "https://sobha-developers.my.site.com/cpportal/s/")
        self.submit_url = config.get("submit_url", "https://sobha-developers.my.site.com/cpportal/s/")
        self.username   = config.get("username")
        self.password   = config.get("password")
        self.project    = config.get("project", "Sobha Arbor Chennai")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "Playwright not installed"}

        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            self.log("🚀 Launching browser for Sobha submission...")
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
                page.goto(self.login_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)

                page.fill("input[name='username']", self.username)
                page.fill("input[name='password']", self.password)
                page.click("input[type='submit']")

                try:
                    page.wait_for_url("**/cpportal/s/**", timeout=15000)
                except Exception:
                    page.wait_for_timeout(5000)

                if "login" in page.url.lower():
                    self.log("❌ Sobha login failed")
                    return {"success": False, "error": "Sobha login failed — check credentials"}

                self.log(f"✅ Logged in: {page.url}")

                # ── 2. NAVIGATE TO ADD LEAD ───────────────────────
                page.goto(self.submit_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(5000)

                # ── 3. FILL FORM ──────────────────────────────────
                full_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip()
                self.log(f"✍️ Filling lead: {full_name}")

                try:
                    page.fill("input[placeholder='Customer Name']", full_name)
                except Exception:
                    try:
                        page.get_by_label("Customer Name").fill(full_name)
                    except Exception:
                        self.log("⚠️ Could not fill Customer Name")

                try:
                    page.fill("input[placeholder='Phone']", lead.mobile or "")
                except Exception:
                    try:
                        page.get_by_label("Phone").fill(lead.mobile or "")
                    except Exception:
                        pass

                if lead.email:
                    try:
                        page.fill("input[placeholder='Email']", lead.email)
                    except Exception:
                        pass

                # Select project dropdown
                project_name = lead.project_name or self.project
                try:
                    page.click("input[placeholder='Project']")
                    page.wait_for_timeout(1000)
                    page.click(f"text={project_name}")
                except Exception:
                    try:
                        page.get_by_label("Project").fill(project_name)
                    except Exception:
                        self.log(f"⚠️ Could not select project: {project_name}")

                # ── 4. SUBMIT ─────────────────────────────────────
                captured_responses = []
                def handle_response(res):
                    if res.request.method == "POST":
                        captured_responses.append(res)
                page.on("response", handle_response)

                self.log("💾 Clicking Next/Submit...")
                try:
                    btn = page.locator("button:has-text('Next'), button:has-text('Submit'), button:has-text('Save')").first
                    btn.click(force=True)
                except Exception as e:
                    self.log(f"⚠️ Submit button click issue: {e}")

                page.wait_for_timeout(5000)

                # ── 5. PARSE RESULT ───────────────────────────────
                page_text = page.evaluate("() => document.body.innerText")

                if any(w in page_text.lower() for w in ["success", "created", "added", "thank"]):
                    self.log("✅ Lead created successfully!")
                    return {"success": True, "status": "CREATED", "message": "Lead submitted to Sobha"}

                if "already exist" in page_text.lower() or "duplicate" in page_text.lower():
                    self.log("⚠️ Duplicate lead")
                    return {"success": True, "status": "DUPLICATE"}

                if any(w in page_text.lower() for w in ["error", "invalid", "failed"]):
                    return {"success": False, "error": f"Sobha error: {page_text[:200]}"}

                # Check network
                if captured_responses:
                    last = captured_responses[-1]
                    if last.status == 200:
                        return {"success": True, "status": "CREATED", "message": "Lead submitted to Sobha (200)"}

                self.log("⚠️ Could not confirm Sobha submission")
                return {"success": False, "error": "Sobha submission result unclear"}

            except Exception as e:
                self.log(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    def validate_session(self) -> bool:
        return False
