try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any, Optional
import json
import re


class RadianceBuilder(BaseBuilder):
    """
    Radiance Realty — Salesforce Experience Cloud (Aura framework).
    Flow:
      1. Login to portal, intercept aura.token + aura.context from page requests
      2. POST saveNewLead via aura://ApexActionController/ACTION$execute
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.portal_base   = "https://radiancerealty.my.site.com/radiancerealtyChannel"
        self.login_url     = config.get("login_url",  f"{self.portal_base}/s/")
        self.leads_url     = f"{self.portal_base}/s/leads"
        self.aura_endpoint = config.get("submit_url",
            f"{self.portal_base}/s/sfsites/aura?r=17&aura.ApexAction.execute=1")
        self.username      = config.get("username",  "")
        self.password      = config.get("password",  "")
        self.builder_id    = config.get("builder_id")
        self.credential_id = config.get("credential_id")

    # ── Playwright context ────────────────────────────────────────────────────
    def _new_context(self, playwright):
        browser = playwright.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )
        return browser, ctx

    # ── Login ─────────────────────────────────────────────────────────────────
    def _login(self, playwright) -> Optional[tuple]:
        """Login and capture aura token + context."""
        browser, bctx = self._new_context(playwright)
        page = bctx.new_page()
        captured = {}

        def on_request(request):
            if "aura" in request.url and request.method == "POST":
                try:
                    from urllib.parse import parse_qs
                    body   = request.post_data or ""
                    params = parse_qs(body)
                    if "aura.token" in params and not captured.get("token"):
                        captured["token"] = params["aura.token"][0]
                    if "aura.context" in params and not captured.get("context"):
                        try:
                            captured["context"] = json.loads(params["aura.context"][0])
                        except Exception:
                            pass
                except Exception:
                    pass

        page.on("request", on_request)

        try:
            self.log("Navigating to Radiance login page...")
            page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            # Fill login form
            for sel in ["#username", "input[name='username']", "input[type='email']", "input[type='text']"]:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.fill(self.username)
                    break

            for sel in ["#password", "input[name='password']", "input[type='password']"]:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.fill(self.password)
                    break

            for sel in ["#Login", "input[type='submit']", "button[type='submit']", "button"]:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    break

            try:
                page.wait_for_url(
                    lambda url: "login" not in url.lower() and "frontdoor" not in url.lower(),
                    timeout=20000
                )
            except Exception:
                pass

            page.wait_for_timeout(3000)

            if "login" in page.url.lower() and "frontdoor" not in page.url.lower():
                self.log("Login failed.")
                return None, None

            # Navigate to leads page to trigger Aura token generation
            self.log("Navigating to leads page to capture Aura token...")
            page.goto(self.leads_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            # Fallback: try to extract token from page source
            if not captured.get("token"):
                html = page.content()
                match = re.search(r'"token"\s*:\s*"([A-Za-z0-9._\-]{20,})"', html)
                if match:
                    captured["token"] = match.group(1)

            # Fallback: extract context from window.$A
            if not captured.get("context"):
                ctx_from_window = page.evaluate("""() => {
                    try {
                        const c = window.$A?.getContext?.() || {};
                        return { mode:'PROD', fwuid:c.fwuid||'', app:c.app||'siteforce:communityApp',
                                 loaded:c.loaded||{}, dn:c.dn||[], globals:c.globals||{}, uad:true };
                    } catch(e) { return null; }
                }""")
                if ctx_from_window:
                    captured["context"] = ctx_from_window

            self.log(f"Token captured: {'YES' if captured.get('token') else 'NO'}")

            cookies = bctx.cookies()
            if self.session_manager:
                self.session_manager.save_session(
                    self.builder_id, self.credential_id, self.builder_name, self.crm_type,
                    cookies, extra_tokens={"aura": captured}
                )

            return cookies, captured

        finally:
            browser.close()

    # ── Submit Lead ───────────────────────────────────────────────────────────
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "playwright not installed"}

        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        with sync_playwright() as p:
            cookies, aura = None, None

            if self.session_manager and self.credential_id:
                session = self.session_manager.db.get_active_session(self.credential_id)
                if session:
                    cookies = session.get("cookies")
                    extra = session.get("extra_tokens") or {}
                    aura  = extra.get("aura")

            if not cookies or not aura:
                self.log("No valid session — logging in...")
                cookies, aura = self._login(p)

            if not cookies or not aura:
                return {"success": False, "error": "Login / token capture failed"}

            browser, bctx = self._new_context(p)
            bctx.add_cookies(cookies)
            page = bctx.new_page()
            fresh = {}

            def on_request(request):
                if "aura" in request.url and request.method == "POST":
                    try:
                        from urllib.parse import parse_qs
                        params = parse_qs(request.post_data or "")
                        if "aura.token" in params and not fresh.get("token"):
                            fresh["token"] = params["aura.token"][0]
                        if "aura.context" in params and not fresh.get("context"):
                            try:
                                fresh["context"] = json.loads(params["aura.context"][0])
                            except Exception:
                                pass
                    except Exception:
                        pass

            page.on("request", on_request)

            try:
                self.log("Loading leads page to get fresh Aura token...")
                page.goto(self.leads_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)

                if "login" in page.url.lower():
                    self.log("Session expired — relogging...")
                    browser.close()
                    cookies, aura = self._login(p)
                    if not cookies:
                        return {"success": False, "error": "Session expired and re-login failed"}
                    browser, bctx = self._new_context(p)
                    bctx.add_cookies(cookies)
                    page = bctx.new_page()
                    page.goto(self.leads_url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(5000)

                token = fresh.get("token") or aura.get("token", "")
                ctx   = fresh.get("context") or aura.get("context", {})

                new_lead_params = {
                    "FirstName":            lead.first_name or "",
                    "LastName":             lead.last_name  or "",
                    "Email_c":              lead.email      or "",
                    "Phone_c":              lead.mobile     or "",
                    "Secondary_Email_c":    lead.secondary_email  or "",
                    "Secondary_Phone_c":    lead.secondary_mobile or "",
                    "Description":          lead.remarks    or "",
                    "Country_c":            lead.country    or "India",
                    "Secondary_Country_c":  lead.secondary_country or "India",
                    "Interested_Project_c": lead.project_name or "",
                }

                self.log("Submitting via Aura ApexAction saveNewLead...")
                result = page.evaluate(
                    """async ([newLeadParams, token, ctx, auraEndpoint]) => {
                        let useToken = token || '';
                        if (!useToken) {
                            for (const s of document.querySelectorAll('script')) {
                                const m = s.textContent.match(/"token":"([^"]{20,})"/);
                                if (m) { useToken = m[1]; break; }
                            }
                        }
                        let useCtx = ctx || {};
                        if (!useCtx.fwuid) {
                            try {
                                const c = window.$A?.getContext?.() || {};
                                useCtx = { mode:'PROD', fwuid:c.fwuid||'', app:c.app||'siteforce:communityApp',
                                           loaded:c.loaded||{}, dn:c.dn||[], globals:c.globals||{}, uad:true };
                            } catch(e) {}
                        }
                        const message = { actions: [{
                            id: '204;a',
                            descriptor: 'aura://ApexActionController/ACTION$execute',
                            callingDescriptor: 'UNKNOWN',
                            params: { namespace:'', classname:'LazyLoadingController',
                                      method:'saveNewLead', params:{ newlead: newLeadParams },
                                      cacheable:false, isContinuation:false }
                        }]};
                        const body = new URLSearchParams();
                        body.append('message',      JSON.stringify(message));
                        body.append('aura.context', JSON.stringify(useCtx));
                        body.append('aura.pageURI', '/radiancerealtyChannel/s/leads');
                        body.append('aura.token',   useToken);
                        const resp = await fetch(auraEndpoint, {
                            method:'POST', credentials:'include',
                            headers:{ 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'*/*' },
                            body: body.toString(),
                        });
                        const text = await resp.text();
                        let parsed; try { parsed = JSON.parse(text); } catch { parsed = text; }
                        return { status: resp.status, body: parsed };
                    }""",
                    [new_lead_params, token, ctx, self.aura_endpoint]
                )

                http_status = result.get("status")
                body        = result.get("body")
                success     = False
                crm_id      = None

                if isinstance(body, dict):
                    actions = body.get("actions", [])
                    for action in actions:
                        state  = action.get("state", "")
                        rv     = action.get("returnValue", {})
                        ret_val = rv.get("returnValue", "") if isinstance(rv, dict) else rv
                        if state == "SUCCESS":
                            success = True
                            crm_id  = str(ret_val)
                            self.log(f"SUCCESS: {ret_val}")
                        elif state == "ERROR":
                            self.log(f"FAILED: {action.get('error')}")

                return {
                    "success":    success,
                    "status":     200 if success else http_status,
                    "crm_lead_id": crm_id,
                    "response":   body,
                }

            finally:
                browser.close()

    def validate_session(self) -> bool:
        return True
