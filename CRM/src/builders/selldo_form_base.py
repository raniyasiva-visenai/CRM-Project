from src.builders.base import BaseBuilder
try:
    import requests
except ImportError:
    requests = None
import json
from datetime import datetime

class SellDoFormBase(BaseBuilder):
    """
    Specialized base for two-step SellDo forms (checklead.php -> sitevisit.php).
    Does NOT require Playwright/Browser (uses requests).
    """
    def __init__(self, config):
        super().__init__(config)
        self.check_url = config.get("check_url")
        self.submit_url = config.get("submit_url")

    def submit_lead(self, lead):
        # Implementation will involve two-step POST logic
        pass

    def _get_safe_date(self) -> str:
        dt = datetime.now()
        return f"{dt.day}-{dt.month}-{dt.year} {dt.strftime('%H:%M')}"

    def validate_session(self) -> bool:
        """SellDo form submissions usually don't have a persistent session to validate."""
        return True
