try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any, Optional
import json


class SameeraBuilder(BaseBuilder):
    """
    Sameera / Dexor — Salesforce Visualforce apexremote submission.
    Flow:
      1. Load portal page → intercept apexremote ctx (vid, csrf, ver)
      2. POST authenticateUser with ctx → get authorized ctx
      3. POST addLead with authorized ctx
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.base_url  = config.get("base_url",  "https://dexor.my.salesforce-sites.com/SLDPortal")
        self.api_url   = config.get("submit_url", f"{self.base_url}/apexremote")
        self.login_url = config.get("login_url",  self.base_url)
        self.username  = config.get("username",   "")
        self.password  = config.get("password",   "")
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

    # ── Login + ctx extraction ────────────────────────────────────────────────
    def _login_and_get_ctx(self, playwright) -> Optional[tuple]:
        browser, bctx = self._new_context(playwright)
        page = bctx.new_page()
        captured_ctx = {}

        def on_request(request):
            if "apexremote" in request.url and request.method == "POST":
                try:
                    body = json.loads(request.post_data or "[]")
                    if isinstance(body, list) and body:
                        ctx = body[0].get("ctx", {})
                        if ctx.get("vid") and not captured_ctx.get("vid"):
                            captured_ctx.update(ctx)
                except Exception:
                    pass

        page.on("request", on_request)

        try:
            self.log("Loading portal to intercept ctx...")
            page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            # If ctx not intercepted via request, extract from Visualforce RemotingManager
            if not captured_ctx.get("vid"):
                full_ctx = page.evaluate("""() => {
                    for (const s of document.querySelectorAll('script')) {
                        const src = s.textContent || '';
                        if (!src.includes('RemotingProviderImpl')) continue;
                        const marker = 'RemotingProviderImpl(';
                        const start  = src.indexOf(marker);
                        if (start === -1) continue;
                        let depth = 0, i = start + marker.length;
                        for (; i < src.length; i++) {
                            if      (src[i] === '{') depth++;
                            else if (src[i] === '}') { depth--; if (depth === 0) { i++; break; } }
                        }
                        let provider;
                        try { provider = JSON.parse(src.substring(start + marker.length, i)); }
                        catch(e) { continue; }
                        const vf = provider.vf || {};
                        const actions = provider.actions || {};
                        let ns = '', ver = 65, csrf = '';
                        for (const k of Object.keys(actions)) {
                            const ms = actions[k].ms || [];
                            if (ms.length > 0) { ns = ms[0].ns||''; ver = ms[0].ver||65; csrf = ms[0].csrf||''; break; }
                        }
                        return { vid: vf.vid||'', csrf, ns, ver, authorization: '' };
                    }
                    return null;
                }""")
                if full_ctx:
                    captured_ctx.update(full_ctx)

            if not captured_ctx.get("vid"):
                self.log("ERROR: Could not capture ctx.vid from page.")
                return None, None

            self.log(f"ctx acquired (vid: {captured_ctx.get('vid','')[:20]}...)")

            # Authenticate user
            auth_result = page.evaluate(
                """async ([email, password, apiUrl, ctx]) => {
                    const resp = await fetch(apiUrl, {
                        method: 'POST', credentials: 'include',
                        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                        body: JSON.stringify([{
                            action: 'SLDPortalApex', method: 'authenticateUser',
                            data: [email, password], type: 'rpc', tid: 3, ctx: ctx
                        }]),
                    });
                    const text = await resp.text();
                    try { return { status: resp.status, body: JSON.parse(text) }; }
                    catch { return { status: resp.status, body: text }; }
                }""",
                [self.username, self.password, self.api_url, captured_ctx]
            )

            body = auth_result.get("body", [])
            if isinstance(body, list):
                for item in body:
                    if isinstance(item, dict):
                        if item.get("statusCode") == 500:
                            self.log(f"Auth error: {item.get('message')}")
                            return None, None
                        captured_ctx.update(item.get("ctx", {}))

            cookies = bctx.cookies()
            self.log(f"Login successful. Cookies: {len(cookies)}")

            # Save session
            if self.session_manager:
                self.session_manager.save_session(
                    self.builder_id, self.credential_id, self.builder_name, self.crm_type,
                    cookies, extra_tokens={"ctx": captured_ctx}
                )

            return cookies, captured_ctx

        finally:
            browser.close()

    # ── Submit lead ───────────────────────────────────────────────────────────
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        if not sync_playwright:
            return {"success": False, "error": "playwright not installed"}

        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        with sync_playwright() as p:
            # Try loading saved session
            cookies, ctx = None, None
            if self.session_manager:
                session = self.session_manager.db.get_active_session(self.credential_id) if self.credential_id else None
                if session:
                    cookies = session.get("cookies")
                    ctx = session.get("extra_tokens", {}).get("ctx") if session.get("extra_tokens") else None

            if not cookies or not ctx:
                self.log("No valid session — logging in...")
                cookies, ctx = self._login_and_get_ctx(p)

            if not cookies or not ctx:
                return {"success": False, "error": "Login failed"}

            browser, bctx = self._new_context(p)
            bctx.add_cookies(cookies)
            page = bctx.new_page()
            refreshed_ctx = {}

            def on_request(request):
                if "apexremote" in request.url and request.method == "POST":
                    try:
                        body = json.loads(request.post_data or "[]")
                        if isinstance(body, list) and body:
                            c = body[0].get("ctx", {})
                            if c.get("vid") and not refreshed_ctx.get("vid"):
                                refreshed_ctx.update(c)
                    except Exception:
                        pass

            page.on("request", on_request)

            try:
                page.goto(self.login_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)

                use_ctx = {**ctx, **refreshed_ctx} if refreshed_ctx.get("vid") else ctx

                lead_payload = {
                    "cpName":               lead.cp_name or self.username,
                    "fullName":             f"{lead.first_name} {lead.last_name or ''}".strip(),
                    "email":                lead.email or "",
                    "secondaryEmail":       lead.secondary_email or "",
                    "phone":                lead.mobile or "",
                    "secondaryPhone":       lead.secondary_mobile or "",
                    "projectName":          lead.project_name or "",
                    "budget":               lead.budget_text or "",
                    "sqftRange":            lead.sqft_range or "",
                    "bhkSize":              lead.bhk_type or "",
                    "propertyType":         lead.property_type or "",
                    "countrycode":          lead.dial_code or "+91",
                    "secondaryCountryCode": lead.secondary_dial_code or "+91",
                    "notes":                lead.remarks or "",
                    "stage":                lead.stage or "warm",
                    "siteVisit":            lead.site_visit or False,
                    "countGiven":           lead.count_given or "No",
                }

                self.log(f"Submitting lead via apexremote addLead...")

                result = page.evaluate(
                    """async ([ctx, leadPayload, apiUrl]) => {
                        const resp = await fetch(apiUrl, {
                            method: 'POST', credentials: 'include',
                            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                            body: JSON.stringify([{
                                action: 'SLDPortalApex', method: 'addLead',
                                data: [leadPayload], type: 'rpc', tid: 6, ctx: ctx
                            }]),
                        });
                        const text = await resp.text();
                        try { return { status: resp.status, body: JSON.parse(text) }; }
                        catch { return { status: resp.status, body: text }; }
                    }""",
                    [use_ctx, lead_payload, self.api_url]
                )

                status    = result.get("status")
                body      = result.get("body")
                success   = False
                crm_id    = None

                if isinstance(body, list):
                    for item in body:
                        if isinstance(item, dict):
                            sc  = item.get("statusCode")
                            ret = item.get("returnValue") or item.get("result")
                            if sc == 500:
                                self.log(f"FAILED: {item.get('message')}")
                            elif ret is not None:
                                if isinstance(ret, dict) and ret.get("success") is False:
                                    self.log(f"FAILED: {ret}")
                                else:
                                    success = True
                                    crm_id  = str(ret)
                                    self.log(f"SUCCESS: Lead added. Return: {ret}")

                return {
                    "success":    success,
                    "status":     200 if success else status,
                    "crm_lead_id": crm_id,
                    "response":   body,
                }

            finally:
                browser.close()

    def validate_session(self) -> bool:
        return True
