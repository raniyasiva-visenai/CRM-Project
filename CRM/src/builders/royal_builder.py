from src.builders.selldo_base import SellDoBase
from src.models.lead import Lead
from typing import Dict, Any


class RoyalBuilder(SellDoBase):
    """Royal Land Developers — SellDo checklead → sitevisit.php submission."""

    def __init__(self, config: Dict[str, Any], session_manager=None):
        # Inject Royal-specific URLs into config before calling super
        config.setdefault("checklead_url", "https://forms.sell.do/royal-land-developers-cp/checklead.php")
        config.setdefault("form_page_url", "https://forms.sell.do/royal-land-developers-cp/form.php")
        # submit_url already set in DB as sitevisit.php
        super().__init__(config, session_manager=session_manager)
