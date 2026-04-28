from abc import ABC, abstractmethod
from src.models.lead import Lead
from typing import Dict, Any

class BaseBuilder(ABC):
    def __init__(self, config: Dict[str, Any], session_manager: Any = None):
        self.config = config
        self.builder_id = config.get("builder_id")
        self.builder_name = config.get("builder_name")
        self.crm_type = config.get("crm_type")
        self.base_url = config.get("base_url")
        self.session_manager = session_manager

    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """Default submission method (No-op)"""
        self.log(f"No submission logic implemented for builder {self.config.get('builder_name')}")
        return {"success": False, "error": "Not implemented"}

    def validate_session(self) -> bool:
        """Default session validation (Always valid)"""
        return True

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
