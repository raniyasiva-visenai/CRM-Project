from abc import ABC, abstractmethod
from src.models.lead import Lead
from typing import Dict, Any

class BaseBuilder(ABC):
    def __init__(self, config: Dict[str, Any], session_manager: Any = None):
        self.config = config
        self.builder_name = config.get("builder_name")
        self.crm_type = config.get("crm_type")
        self.base_url = config.get("base_url")
        self.session_manager = session_manager

    @abstractmethod
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """Submit the lead to the builder's CRM."""
        pass

    @abstractmethod
    def validate_session(self) -> bool:
        """Check if the current session is valid."""
        pass

    def _get_payload(self, lead: Lead) -> Dict[str, Any]:
        """
        Get the payload for submission. 
        Prioritizes lead.raw_payload if it's a dictionary.
        """
        if lead.raw_payload and isinstance(lead.raw_payload, dict):
            self.log("📋 Using dynamic payload from lead.raw_payload")
            return lead.raw_payload
        return {}

    def log(self, message: str):
        print(f"[{self.builder_name}] {message}")
