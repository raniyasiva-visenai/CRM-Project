import requests
from src.builders.base_builder import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any

class MaruthamBuilder(BaseBuilder):
    """
    Marutham Group Lead.
    Form URL: https://metro-affiliates.com/intake/Maruthamprop
    Platform: Custom (CodeIgniter with CSRF)
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.submit_url = config.get("submit_url", "https://metro-affiliates.com/intake/Maruthamprop")
        self.admin_uid = config.get("admin_uid", "H9XRfwkL6kovBL7d5KZmnO7jVjiuprkXK6T0kJiUK1QxvFahAxhK4LrfJyaeoBEkZP8DU3yogoIAWI5FwzDSWQ==")
        self.affiliat_name = config.get("affiliat_name", "TWFydXRoYW0gUHJvcA==")
        self.affiliat_phone = config.get("affiliat_phone", "KzkxODkyNTgyMDE0Nw==")

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        self.log(f"Fetching form for CSRF from {self.submit_url}...")
        try:
            # Initial GET to get cookies and CSRF
            resp = session.get(self.submit_url, headers=headers, timeout=10)
            csrf_token = session.cookies.get("csrf_cookie_name")
            
            if not csrf_token:
                self.log("Failed to extract CSRF token from cookies.")
                return {"success": False, "error": "CSRF token missing"}

            # Map lead fields to form fields
            # Full Name -> name
            # Your Email -> email
            # Your Phone -> phone
            # Project -> project
            
            # The project name should match one of the values in the dropdown
            project_name = lead.project_name or self.config.get("default_project", "Marutham Breeze Hi")

            payload = {
                "csrf_test_name": csrf_token,
                "admin_uid":      self.admin_uid,
                "name":           lead.full_name or f"{lead.first_name} {lead.last_name}".strip(),
                "email":          lead.email or "",
                "phone":          lead.mobile or "",
                "affiliat_name":  self.affiliat_name,
                "affiliat_phone": self.affiliat_phone,
                "project":        project_name,
                "message":        lead.remarks or ""
            }

            self.log(f"Submitting lead to Marutham: {payload['name']} for {payload['project']}...")
            response = session.post(self.submit_url, data=payload, headers=headers, timeout=15)

            if response.status_code == 200 and ("success" in response.text.lower() or "thank you" in response.text.lower()):
                self.log("Success: Lead submitted successfully.")
                return {
                    "success": True,
                    "status": 200,
                    "response": "Lead submitted successfully."
                }
            else:
                self.log(f"Failure: Status {response.status_code}. Response preview: {response.text[:200]}")
                return {
                    "success": False,
                    "status": response.status_code,
                    "error": "Submission failed or success message not found",
                    "response": response.text[:500]
                }

        except Exception as e:
            self.log(f"Error during submission: {str(e)}")
            return {"success": False, "error": str(e)}

    def validate_session(self) -> bool:
        return True # Marutham uses per-submission CSRF
