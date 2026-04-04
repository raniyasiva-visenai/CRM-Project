try:
    import requests
except ImportError:
    requests = None
from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any

class APIBase(BaseBuilder):
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.submit_url = config.get("submit_url")
        self.headers = config.get("headers", {})
        self.payload_mapping = config.get("payload_mapping", {})

    def _prepare_payload(self, lead: Lead) -> Dict[str, Any]:
        payload = {}
        for key, field in self.payload_mapping.items():
            payload[key] = getattr(lead, field, "")
        return payload

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        self.log(f"Submitting lead to API {self.submit_url}...")
        
        # Get payload (dynamic from lead or fallback to mapping)
        payload = self._get_payload(lead)
        if not payload:
            payload = self._prepare_payload(lead)

        response = requests.post(self.submit_url, data=payload, headers=self.headers, timeout=5)
        
        try:
            return {
                "status": response.status_code,
                "body": response.json()
            }
        except:
            return {
                "status": response.status_code,
                "body": response.text
            }

    def validate_session(self) -> bool:
        return True # API keys usually don't expire in the same way
