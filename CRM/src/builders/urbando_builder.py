try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any

class UrbandoBuilder(BaseBuilder):
    """
    Urbando Modal Form Builder.
    Uses Playwright to handle the 'ENQUIRE NOW' modal on urbando.in.
    """
    
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.form_url = config.get("submit_url", "https://urbando.in/channel-partners/")
    
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Submit lead via Urbando modal using Playwright.
        """
        if not sync_playwright:
            self.log("Playwright not installed")
            return {"success": False, "error": "Playwright not installed"}
        
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            self.log("Launching browser for Urbando submission...")
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
                # ── 1. NAVIGATE AND OPEN MODAL ─────────────────────────
                self.log(f"Navigating to: {self.form_url}")
                page.goto(self.form_url, wait_until="networkidle", timeout=60000)
                
                self.log("Opening 'ENQUIRE NOW' modal...")
                # Use the exact selector identified: a.ePop.pum-trigger
                enquire_btn = page.locator("a.ePop.pum-trigger").first
                enquire_btn.click()
                
                # Wait for modal container
                page.wait_for_selector(".pum-container, .wpcf7-form", timeout=15000)
                page.wait_for_timeout(2000) # Short wait for JS initialization
                
                # ── 2. FILL FORM FIELDS ──────────────────────────────
                self.log(f"Filling form for: {lead.first_name}")
                
                # Use robust selectors (name or placeholder or type)
                page.locator("input[name='your-name'], input[placeholder*='Name']").first.fill(f"{lead.first_name} {lead.last_name or ''}".strip())
                page.locator("input[name='your-email'], input[type='email']").first.fill(lead.email or "manoj@gmail.com")
                
                # Phone field
                phone_field = page.locator("input[name='your-tel'], input[type='tel'], input[placeholder*='Mobile']").first
                phone_field.fill(lead.mobile)
                
                # Project Select
                target_project = lead.project_name or "Urbando Evorise"
                self.log(f"Selecting Project: {target_project}")
                try:
                    page.select_option("select[name='menu-project'], select", label=target_project)
                except:
                    self.log(f"Project '{target_project}' not found by label, selecting first option")
                    page.select_option("select[name='menu-project'], select", index=1)
                
                # Message
                page.locator("textarea[name='your-message'], textarea").first.fill(lead.remarks or "Interested in the project")
                
                # Consent Checkbox
                self.log("Checking consent checkbox...")
                checkbox = page.locator("input[type='checkbox'], input[name*='acceptance']").first
                checkbox.check()
                
                # ── 3. SUBMIT FORM ───────────────────────────────────
                self.log("Clicking SUBMIT...")
                submit_btn = page.locator("input[type='submit'], button[type='submit'], .wpcf7-submit").first
                submit_btn.click()
                
                # Wait for response notification
                page.wait_for_timeout(5000)
                
                # ── 4. CHECK SUCCESS ─────────────────────────────────
                response_text = page.evaluate("() => document.querySelector('.wpcf7-response-output')?.innerText || ''").lower()
                page_inner_text = page.evaluate("() => document.body.innerText").lower()
                
                if any(w in response_text for w in ["thank you", "success", "submitted"]):
                    self.log("Urbando: Lead submitted successfully!")
                    return {"success": True, "status": "SUCCESS", "response": response_text}
                
                if "thank you" in page_inner_text or "success" in page_inner_text:
                     self.log("Urbando: Success message found in page text.")
                     return {"success": True, "status": "SUCCESS", "response": "Success detected in body text."}

                self.log(f"Urbando: Submission status unclear. Response text: {response_text}")
                return {"success": True, "status": "UNKNOWN", "response": response_text or "Form clicked, check CRM dashboard."}
                
            except Exception as e:
                self.log(f"Error during Urbando submission: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()
    
    def validate_session(self) -> bool:
        return True
