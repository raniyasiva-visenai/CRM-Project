try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any

class IYRABuilder(BaseBuilder):
    """
    IYRA MINT360 Form Builder.
    Uses Playwright for full UI interaction with JavaScript-based form.
    
    Required config:
      - submit_url : https://mint360.in/client_form.html?key=c7e69-5a560-614e9-4a600-5c935f160e7e
    """
    
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.form_url = config.get("submit_url", "https://mint360.in/client_form.html?key=c7e69-5a560-614e9-4a600-5c935f160e7e")
    
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Submit lead via MINT360 form using Playwright.
        """
        if not sync_playwright:
            self.log("❌ Playwright not installed")
            return {"success": False, "error": "Playwright not installed"}
        
        # Ensure we have an event loop if needed (standard for sync playwright in shared envs)
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            self.log("Launching browser for IYRA MINT360 submission...")
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
                # ── 1. NAVIGATE TO FORM ──────────────────────────────
                self.log(f"Navigating to: {self.form_url}")
                page.goto(self.form_url, wait_until="networkidle", timeout=60000)
                
                # ── 2. FILL FORM FIELDS ──────────────────────────────
                self.log(f"Filling form for: {lead.first_name}")
                
                # Name
                page.locator("input#name").fill(f"{lead.first_name} {lead.last_name or ''}".strip())
                
                # Mobile
                page.locator("input#phone").fill(lead.mobile)
                
                # Email
                page.locator("input#email").fill(lead.email or "")
                
                # Source Dropdown (Select2)
                # Value 'Marutham prop' as seen in screenshot
                self.log("Handling Source Dropdown...")
                page.click("span#select2-leadsource-container")
                page.wait_for_selector(".select2-results__option", timeout=5000)
                page.click("li.select2-results__option:has-text('Marutham prop')")
                
                # Project Dropdown (Select2)
                # Using lead.project_name or fallback to 'Iyra Anuhya'
                target_project = lead.project_name or "Iyra Anuhya"
                self.log(f"Handling Project Dropdown -> {target_project}...")
                page.click("span#select2-project-container")
                page.wait_for_selector(".select2-results__option", timeout=5000)
                
                # Try to find exactly matching project or partial
                try:
                    page.click(f"li.select2-results__option:has-text('{target_project}')")
                except:
                    self.log(f"Exact project '{target_project}' not found, picking first available result")
                    page.click("li.select2-results__option")
                
                # Comments/Remarks
                page.locator("textarea#remarks").fill(lead.remarks or "Interested in the project")
                
                # ── 3. SUBMIT FORM ───────────────────────────────────
                self.log("Clicking submit button...")
                page.click("button#submitForm")
                
                # Wait for response/navigation
                page.wait_for_timeout(5000)
                
                # ── 4. CHECK SUCCESS ─────────────────────────────────
                page_text = page.evaluate("() => document.body.innerText").lower()
                
                if any(w in page_text for w in ["success", "thank you", "submitted", "created", "registered"]):
                    self.log("IYRA: Lead submitted successfully!")
                    return {"success": True, "status": "SUCCESS", "response": "Success message found on page"}
                
                if any(w in page_text for w in ["duplicate", "already exist", "already registered"]):
                    self.log("IYRA: Duplicate lead detected")
                    return {"success": True, "status": "DUPLICATE", "response": "Duplicate message found on page"}
                
                self.log("IYRA: Could not confirm submission result from text")
                return {"success": True, "status": "UNKNOWN", "response": "Form clicked, but no clear confirmation text found"}
                
            except Exception as e:
                self.log(f"Error during IYRA submission: {e}")
                return {"success": False, "error": str(e)}
            finally:
                browser.close()
    
    def validate_session(self) -> bool:
        """MINT360 forms don't require session validation."""
        return True
