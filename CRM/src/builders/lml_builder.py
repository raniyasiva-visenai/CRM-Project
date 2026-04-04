from src.builders.selldo_base import SellDoBase
from src.models.lead import Lead
from typing import Dict, Any


class LMLBuilder(SellDoBase):
    """LML Homes — SellDo checklead → sitevisit.php submission."""

    def __init__(self, config: Dict[str, Any], session_manager=None):
        config.setdefault("checklead_url", "https://forms.sell.do/lml-homes/checklead.php")
        config.setdefault("form_page_url", "https://forms.sell.do/lml-homes/form.php")
        super().__init__(config, session_manager=session_manager)
