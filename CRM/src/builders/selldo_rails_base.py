"""
SellDoRailsBase — Common base for Rails/Sell.do CRM portals using
Playwright-based login + CSRF token extraction + fetch POST submission.

Used by: GT Bharathi, MP, Altis, Lancor, Earthen Spaces, VR, Taj, Voora
"""

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any, Optional
import json


class SellDoRailsBase(BaseBuilder):
    """
    Base builder for CRMs hosted on Rails/Sell.do platforms.
    
    Flow:
      1. Login via Playwright (cookie-based session)
      2. Load dashboard to extract CSRF token
      3. Submit lead via in-page fetch() POST
      4. Parse response for success/duplicate/error
    
    Config keys:
      - login_url      : e.g. https://cp.example.com/users/sign_in?locale=en
      - dashboard_url  : e.g. https://cp.example.com/dashboard?locale=en
      - submit_url     : e.g. https://cp.example.com/admin/leads?locale=en
      - username       : CP login username/email
      - password       : CP login password
      - crm_project_id : Project ID for lead assignment
      - login_type     : 'standard' (default), 'email', or 'tel'
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url     = config.get("login_url", "")
        self.dashboard_url = config.get("dashboard_url", "")
        self.submit_url    = config.get("submit_url", "")
        self.username      = config.get("username", "")
        self.password      = config.get("password", "")
        self.project_id    = config.get("crm_project_id", "")
        self.login_type    = config.get("login_type", "standard")  # standard | email | tel
        self.builder_id    = config.get("builder_id")
        self.credential_id = config.get("credential_id")

    def _new_context(self, p):
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
        )
        return browser, context

    # ── LOGIN ─────────────────────────────────────────────────────
    def _login(self, p) -> Optional[list]:
        """Login and return cookies."""
        browser, context = self._new_context(p)
        page = context.new_page()

        try:
            self.log(f"🔐 Logging in to {self.login_url}...")
            page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            self._fill_login_fields(page)

            # Click Sign In
            try:
                page.click("input[value='Sign In']", timeout=5000)
            except Exception:
                page.click("text=Sign In", timeout=5000)

            page.wait_for_timeout(5000)

            if "sign_in" in page.url:
                self.log("❌ Login failed — still on login page.")
                return None

            self.log(f"✅ Logged in: {page.url}")
            cookies = context.cookies()

            # Save session if session_manager available
            if self.session_manager:
                self.session_manager.save_session(
                    self.builder_id, self.credential_id,
                    self.builder_name, self.crm_type, cookies
                )

            return cookies
        finally:
            browser.close()

    def _fill_login_fields(self, page):
        """Fill login form fields. Override in subclasses for special login forms."""
        # Standard Sell.do often defaults to OTP login. Toggle to password login if possible.
        try:
            pwd_toggle = page.locator("a:has-text('Login with password'), .login-password-link").first
            if pwd_toggle.is_visible(timeout=3000):
                self.log("🔗 Toggling to password-based login...")
                pwd_toggle.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

        if self.login_type == "email":
            page.fill("input[name='user[login]'][type='email'], #user_login", self.username)
        elif self.login_type == "tel":
            page.locator("input[type='tel']:visible").first.click()
            page.locator("input[type='tel']:visible").first.type(self.username, delay=100)
        else:
            page.fill("#user_login", self.username)

        page.fill("#user_password", self.password)

    # ── SESSION CHECK ─────────────────────────────────────────────
    def _check_session(self, p, cookies) -> bool:
        browser, context = self._new_context(p)
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            page.goto(self.dashboard_url, wait_until="domcontentloaded", timeout=30000)
            valid = "sign_in" not in page.url
            self.log("✅ Session valid" if valid else "❌ Session expired")
            return valid
        finally:
            browser.close()

    # ── PAYLOAD BUILDING ──────────────────────────────────────────
    def _build_payload(self, lead: Lead, csrf: str) -> Dict[str, str]:
        """Build the form payload. Override to add CRM-specific fields."""
        payload = {
            "utf8": "✓",
            "authenticity_token": csrf,
            "lead[first_name]":          lead.first_name or "",
            "lead[last_name]":           lead.last_name or "",
            "lead[email]":               lead.email or "",
            "lead[phone]":               lead.mobile or "",
            "lead[country_code]":        "IN",
            "lead[phone_country_code]":  "+91",
            "lead[project_id]":          lead.project_id or self.project_id or "",
            "commit": "Save",
        }
        return payload

    # ── SUBMIT LEAD ───────────────────────────────────────────────
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "Playwright not installed"}

        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            # 1. Get cookies (session or fresh login)
            cookies = None
            if self.session_manager:
                cookies = self.session_manager.get_session(
                    self.builder_id, self.credential_id, self.builder_name
                )
                if cookies and not self._check_session(p, cookies):
                    cookies = None

            if not cookies:
                cookies = self._login(p)

            if not cookies:
                return {"success": False, "error": f"{self.builder_name} login failed"}

            # 2. Open dashboard and fetch CSRF
            browser, context = self._new_context(p)
            context.add_cookies(cookies)
            page = context.new_page()

            try:
                self.log("🔄 Loading dashboard for CSRF...")
                page.goto(self.dashboard_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)

                if "sign_in" in page.url:
                    self.log("❌ Session expired during submission")
                    return {"success": False, "error": "Session expired"}

                csrf = page.evaluate(
                    "() => document.querySelector('meta[name=\"csrf-token\"]')?.content"
                )
                if not csrf:
                    self.log("❌ CSRF token not found")
                    return {"success": False, "error": "CSRF token not found"}

                self.log(f"🔑 CSRF: {csrf[:25]}...")

                # 3. Build payload
                payload = self._build_payload(lead, csrf)

                # 4. Submit via fetch
                self.log(f"📤 Submitting lead to {self.submit_url}...")
                result = page.evaluate(
                    """async ([url, data, csrf]) => {
                        const form = new URLSearchParams();
                        for (const [k, v] of Object.entries(data)) {
                            form.append(k, v);
                        }
                        const resp = await fetch(url, {
                            method: "POST",
                            credentials: "include",
                            headers: {
                                "Content-Type": "application/x-www-form-urlencoded",
                                "X-CSRF-Token": csrf,
                                "X-Requested-With": "XMLHttpRequest"
                            },
                            body: form.toString(),
                            redirect: "follow"
                        });
                        return {
                            status: resp.status,
                            url: resp.url,
                            body: await resp.text()
                        };
                    }""",
                    [self.submit_url, payload, csrf]
                )

                # 5. Parse result
                return self._parse_result(result)

            except Exception as e:
                self.log(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()

    # ── PARSE RESULT ──────────────────────────────────────────────
    def _parse_result(self, result: Dict) -> Dict[str, Any]:
        """Parse the fetch response. Override for custom parsing."""
        status = result.get("status", 0)
        body = result.get("body", "")
        body_lower = body.lower() if body else ""

        self.log(f"📩 Response: status={status}")

        if status in [200, 201]:
            if "invalid" in body_lower or "error" in body_lower:
                if "already exist" in body_lower or "duplicate" in body_lower:
                    self.log("⚠️ Duplicate lead")
                    return {"success": True, "status": "DUPLICATE", "response": body}
                self.log("❌ Validation error in response")
                return {"success": False, "error": f"Validation error: {body[:200]}"}
            self.log("✅ Lead created successfully!")
            return {"success": True, "status": "CREATED", "message": f"Lead submitted to {self.builder_name}", "response": body}

        if status == 422:
            if "already exist" in body_lower or "duplicate" in body_lower:
                self.log("⚠️ Duplicate lead (422)")
                return {"success": True, "status": "DUPLICATE", "response": body}
            return {"success": False, "error": f"Validation error (422): {body[:200]}"}

        return {"success": False, "error": f"Failed with status {status}: {body[:200]}"}

    def validate_session(self) -> bool:
        return False
