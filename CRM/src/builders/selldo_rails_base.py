import json
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright
from src.builders.base import BaseBuilder
from src.models.lead import Lead

class SellDoRailsBase(BaseBuilder):
    """
    Base class for Sell.do portals which typically use Ruby on Rails.
    Handles login with cookie persistence and CSRF token extraction.
    """
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = self.config.get('submit_url', '')
        if '/users/sign_in' not in self.login_url and self.login_url:
            # Normalize to sign-in page if needed
            from urllib.parse import urlparse
            parsed = urlparse(self.login_url)
            self.login_url = f"{parsed.scheme}://{parsed.netloc}/users/sign_in?locale=en"
            
        self.username = self.config.get('username', '')
        self.password = self.config.get('secret_ref', '')
        self.login_type = self.config.get('extra_config', {}).get('login_type', 'email')
        
        # Determine paths
        self.session_file = os.path.join('data', 'sessions', f"cookies_{self.builder_id.lower()}.json")
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)

    def _new_context(self, p):
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        return browser, context

    def _login(self):
        """Standard Sell.do login flow using proven POC logic."""
        with sync_playwright() as p:
            browser, context = self._new_context(p)
            page = context.new_page()

            try:
                self.log(f"🔐 Logging in to {self.login_url}...")
                # Use Load state like the POC
                page.goto(self.login_url, wait_until="load", timeout=60000)
                page.wait_for_timeout(3000)

                self._fill_login_fields(page)

                # Click Sign In (POC Logic - Expanded)
                try:
                    self.log("🖱️ Clicking Sign In button (via POC JS logic)...")
                    clicked = page.evaluate("""() => {
                        const selectors = [
                            "input[type='submit'][name='commit']",
                            "input[type='submit'][value='Sign In']",
                            "input[type='button'][value='Sign In']",
                            "button[type='submit']"
                        ];
                        for (const sel of selectors) {
                            const btns = document.querySelectorAll(sel);
                            for (const btn of btns) {
                                const style = window.getComputedStyle(btn);
                                const rect  = btn.getBoundingClientRect();
                                if (style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0) {
                                    btn.click();
                                    return btn.value || btn.innerText;
                                }
                            }
                        }
                        return null;
                    }""")
                    if not clicked:
                        self.log("⚠️ No button clicked via JS, trying fallback...")
                        page.click("input[value='Sign In'], button:has-text('Sign In')", timeout=5000)
                except Exception as e:
                    self.log(f"⚠️ Button click failed: {e}")

                page.wait_for_timeout(5000)

                # Verify success
                if "sign_in" in page.url:
                    self.log(f"❌ Login failed — still on login page. URL: {page.url}")
                    # Save debug screenshot
                    debug_dir = os.path.join('data', 'debug')
                    os.makedirs(debug_dir, exist_ok=True)
                    screenshot_path = os.path.join(debug_dir, f"login_fail_{self.builder_id.lower()}.png")
                    page.screenshot(path=screenshot_path)
                    self.log(f"📸 Debug screenshot saved to {screenshot_path}")
                    return None

                self.log(f"✅ Logged in! Current URL: {page.url}")
                
                # Capture cookies
                cookies = context.cookies()
                try:
                    with open(self.session_file, 'w') as f:
                        json.dump(cookies, f)
                    self.log(f"[Session] Saved session for {self.builder_id} to {self.session_file}")
                except Exception as e:
                    self.log(f"[DB] Error saving session: {e}")
                
                return cookies

            except Exception as e:
                self.log(f"❌ Login Critical Error: {e}")
                return None
            finally:
                browser.close()

    def _fill_login_fields(self, page):
        """Default Sell.do filling logic with dual-login field support."""
        try:
            # 1. Fill Email/Login via JS
            self.log(f"⌨️ Filling email: {self.username}")
            
            # POC Fix: Site might have multiple user[login] inputs or specific email inputs
            login_selectors = ["input[name='user[login]'][type='email']", "#user_login"]
            
            page.evaluate(
                """([selectors, val]) => {
                    for (const sel of selectors) {
                        const els = document.querySelectorAll(sel);
                        for (const el of els) {
                            const style = window.getComputedStyle(el);
                            if (style.display !== 'none' && style.visibility !== 'hidden') {
                                el.value = val;
                                el.dispatchEvent(new Event('input',  {bubbles: true}));
                                el.dispatchEvent(new Event('change', {bubbles: true}));
                                return true;
                            }
                        }
                    }
                    return false;
                }""",
                [login_selectors, self.username]
            )
            page.wait_for_timeout(500)

            # 2. Fill Password via JS
            self.log("⌨️ Filling password...")
            page.evaluate(
                """([sel, val]) => {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        const style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            el.value = val;
                            el.dispatchEvent(new Event('input',  {bubbles: true}));
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            return true;
                        }
                    }
                    return false;
                }""",
                ["#user_password", self.password]
            )
            page.wait_for_timeout(500)
            
        except Exception as e:
            self.log(f"⚠️ Sell.do Login Fill Error: {e}")

    def _extract_csrf(self, page):
        """Extract CSRF token from page meta tag."""
        return page.evaluate("document.querySelector('meta[name=\"csrf-token\"]').content")

    def validate_session(self) -> bool:
        """Check if the current session is valid by visiting the dashboard."""
        if not os.path.exists(self.session_file):
            return False
            
        with sync_playwright() as p:
            browser, context = self._new_context(p)
            # Load cookies
            try:
                with open(self.session_file, 'r') as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
            except Exception:
                return False
                
            page = context.new_page()
            try:
                # Try to go to dashboard
                dashboard_url = self.login_url.replace('/users/sign_in', '/dashboard')
                page.goto(dashboard_url, wait_until="load", timeout=30000)
                
                if "sign_in" in page.url:
                    return False
                return True
            except Exception:
                return False
            finally:
                browser.close()

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """Perform lead submission using established session."""
        cookies = self._login()
        if not cookies:
            return {"message": "Login failed: _login() returned None"}
            
        return {"message": "Login successful via _login()"}
