try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
import requests, json, os, time
from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any

class VistaBuilder(BaseBuilder):
    """
    Vista (Realty World / Listez) CRM Builder.
    Uses Playwright for login and token extraction, then REST API for submission.
    """
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.login_url = config.get("login_url", "https://rwd.listez.in/auth")
        self.submit_url = config.get("submit_url", "https://rwdnode.listez.in/orgContacts/save_contact_auto_assign/contacts")
        self.username = config.get("username", "marutham@rwd.in")
        self.password = config.get("password")
        self.token_file = "token_listez.json"

    def get_auth(self) -> Dict[str, Any]:
        """Fetch token from file or re-login if needed."""
        if os.path.exists(self.token_file):
            try:
                auth = json.load(open(self.token_file))
                # Validate token
                test = requests.get(
                    "https://rwdnode.listez.in/orgContacts/contacts",
                    headers={
                        "Authorization": auth["token"],
                        "org-id": str(auth["org_id"])
                    },
                    timeout=10
                )
                if test.status_code == 200:
                    return auth
            except:
                pass
        
        return self.login_and_extract_token()

    def login_and_extract_token(self) -> Dict[str, Any]:
        if not sync_playwright:
            raise Exception("playwright not installed")

        with sync_playwright() as p:
            self.log("🔐 Launching browser for Vista login...")
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()

            captured = {"token": None, "org_id": None}

            page.goto(self.login_url, wait_until="load", timeout=60000)
            page.wait_for_selector("input[name='email']", timeout=10000)
            page.fill("input[name='email']", self.username)
            page.fill("input[name='password']", self.password)
            page.click("button[type='submit']")
            
            try:
                page.wait_for_url("**/menu/**", timeout=30000)
                self.log("✅ Logged in successfully!")
                
                # Polling for storage to be populated with kt-auth-react-v
                for _ in range(20):
                    storage = page.evaluate("() => localStorage.getItem('kt-auth-react-v')")
                    if storage:
                        data = json.loads(storage)
                        captured["token"] = data['api_token']
                        captured["org_id"] = str(data.get("org_id", "2"))
                        break
                    time.sleep(1)
            except Exception as e:
                self.log(f"❌ Login redirect failed: {e}")
            
            browser.close()

            if captured["token"]:
                with open(self.token_file, "w") as f:
                    json.dump(captured, f)
                return captured

            raise Exception("Could not extract token from Vista storage")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        try:
            auth = self.get_auth()
            
            headers = {
                "Authorization": auth["token"],
                "org-id":        str(auth["org_id"]),
                "Accept":        "application/json",
                "Origin":        "https://rwd.listez.in",
                "Referer":       "https://rwd.listez.in/",
                "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            }

            # Map Lead to Vista fields
            payload = {
                "salutation":    "1", # Default Mr.
                "first_name":    lead.first_name,
                "last_name":     lead.last_name or "",
                "mobile":        lead.mobile,
                "email":         lead.email or "",
                "contact_type":  "8", # Default Lead?
                "assign_to":     "222", # Assigned to Marutham
                "source":        "63", # Map source if needed
                "property_id":   "1",
                "contact_status":"2", # New
                "is_secondary_contact": "0",
            }

            # Merge with raw_payload if exists
            if lead.raw_payload:
                payload.update(lead.raw_payload)

            # Send as multipart/form-data
            files = {k: (None, str(v) if v is not None else "") for k, v in payload.items()}

            self.log(f"📤 Submitting lead to Vista (Org: {auth['org_id']})...")
            resp = requests.post(self.submit_url, files=files, headers=headers, timeout=30)
            
            if resp.status_code in [200, 201]:
                self.log("✨ SUCCESS: Lead submitted to Vista!")
                return {
                    "success": True,
                    "status": "CREATED",
                    "response": resp.json()
                }
            else:
                self.log(f"❌ Submission failed (Status: {resp.status_code}): {resp.text}")
                return {
                    "success": False,
                    "error": resp.text,
                    "status_code": resp.status_code
                }

        except Exception as e:
            self.log(f"❌ Critical error: {e}")
            return {"success": False, "error": str(e)}

    def validate_session(self) -> bool:
        auth = self.get_auth()
        return auth is not None
