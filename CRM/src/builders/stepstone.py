try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any, Optional
import json
import os

class StepStoneBase(BaseBuilder):
    def __init__(self, config: Dict[str, Any], session_manager: Any = None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = config.get("login_url")
        self.dashboard_url = config.get("dashboard_url")
        self.submit_url = config.get("submit_url")
        self.username = config.get("username")
        self.password = config.get("password")
        self.builder_id = config.get("builder_id") # Needed for session tracking
        self.credential_id = config.get("credential_id") # Needed for session tracking
        self.payload_mapping = config.get("payload_mapping", {})

    def new_context(self, playwright):
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )
        return browser, context

    def login(self, p=None) -> Optional[list]:
        if p:
            browser, context = self.new_context(p)
            return self._perform_login(browser, context)
            
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        with sync_playwright() as playw:
            browser, context = self.new_context(playw)
            return self._perform_login(browser, context)

    def _perform_login(self, browser, context) -> Optional[list]:
        page = context.new_page()
        try:
            self.log(f"Logging in to {self.login_url}...")
            page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
            
            # Default selectors, can be overridden in config
            user_sel = self.config.get("selectors", {}).get("username", "#user_login")
            pass_sel = self.config.get("selectors", {}).get("password", "#user_password")

            # Robust DOM manipulation from POC script
            for sel, val in [(user_sel, self.username), (pass_sel, self.password)]:
                page.evaluate(
                    """([sel, val]) => {
                        const el = document.querySelector(sel);
                        if (!el) return;
                        el.value = val;
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                    }""",
                    [sel, val]
                )
                page.wait_for_timeout(300)
                
            # Verify inputs were filled
            filled = page.evaluate("""() => {
                return {
                    user: document.querySelector("#user_login")?.value,
                    pass: document.querySelector("#user_password")?.value ? 'PRESENT' : 'MISSING'
                }
            }""")
            self.log(f"Input check before click: {filled}")

            clicked = page.evaluate("""() => {
                const allBtns = [...document.querySelectorAll("input[type='submit'], button[type='submit'], button")];
                for (const btn of allBtns) {
                    const label = (btn.value || btn.innerText || btn.textContent || '').trim();
                    if (label === 'Sign In' || label === 'Login') { btn.click(); return label; }
                }
                for (const btn of allBtns) {
                    const label = (btn.value || btn.innerText || btn.textContent || '').trim();
                    const s = window.getComputedStyle(btn);
                    if (label !== 'Get OTP' && s.display !== 'none' && btn.getBoundingClientRect().width > 0) {
                        btn.click(); return label;
                    }
                }
                return null;
            }""")
            self.log(f"Clicked login button: {clicked}")
            
            # Use POC style URL wait
            try:
                page.wait_for_url(lambda url: "sign_in" not in url, timeout=10000)
            except:
                page.wait_for_timeout(2000) # Final fallback
            
            if "sign_in" in page.url:
                self.log("Login failed. Capturing debug info...")
                page.screenshot(path=f"login_fail_{self.builder_name.replace(' ', '_')}.png")
                error_msg = page.evaluate("""() => {
                    const alert = document.querySelector('.alert, .error, .notice, #error_explanation, #flash_alert');
                    return alert ? alert.innerText : 'No visible error message';
                }""")
                self.log(f"Page error text: {error_msg}")
                return None

            self.log(f"Login successful! Current URL: {page.url}")
            cookies = context.cookies()
            if self.session_manager:
                self.session_manager.save_session(
                    self.builder_id, self.credential_id, self.builder_name, self.crm_type, cookies
                )
            return cookies
        finally:
            browser.close()

    def _prepare_payload(self, lead: Lead) -> Dict[str, Any]:
        payload = {}
        for key, field in self.payload_mapping.items():
            val = getattr(lead, field, "")
            # Phone formatting as required by SellDo/Rails backends
            if field in ['mobile', 'phone'] and val:
                dial_code = getattr(lead, 'dial_code', '+91')
                if not str(val).startswith('+'):
                    val = f"{dial_code}-{val}"
            payload[key] = val
        return payload

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        with sync_playwright() as p:
            browser, context = self.new_context(p)
            
            # Load cookies if available
            cookies = None
            if self.session_manager:
                cookies = self.session_manager.get_session(self.builder_id, self.credential_id, self.builder_name)
            
            if not cookies:
                self.log("No valid session found, attempting login...")
                cookies = self.login(p)
            
            if cookies:
                context.add_cookies(cookies)
            else:
                return {"success": False, "error": "Login failed, could not establish session."}

            page = context.new_page()
            try:
                self.log(f"Loading dashboard to get CSRF...")
                dash_url = self.dashboard_url or self.login_url.replace("/users/sign_in", "")
                page.goto(dash_url, wait_until="domcontentloaded", timeout=60000)
                
                csrf_token = page.evaluate("() => document.querySelector('meta[name=\"csrf-token\"]')?.content")
                
                # Transform lead to payload
                payload = self._prepare_payload(lead)

                self.log(f"Submitting lead via fetch...")
                result = page.evaluate("""async ([submitUrl, fields, csrf]) => {
                    const payload = new URLSearchParams();
                    payload.append("utf8", "✓");
                    if (csrf) payload.append("authenticity_token", csrf);
                    
                    for (const [k, v] of Object.entries(fields)) payload.append(k, v);
                    const headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest',
                    };
                    if (csrf) headers['X-CSRF-Token'] = csrf;
                    const resp = await fetch(submitUrl, {
                        method: 'POST',
                        headers: headers,
                        body: payload.toString()
                    });
                    return { status: resp.status, body: await resp.text() };
                }""", [self.submit_url, payload, csrf_token or ""])
                
                return result
            finally:
                browser.close()

    def validate_session(self) -> bool:
        # Simple session check by visiting dashboard
        return True # Simplified for now
