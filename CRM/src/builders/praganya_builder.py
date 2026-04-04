from src.builders.salezrobot_base import SalezRobotBase
from typing import Dict, Any

class PraganyaBuilder(SalezRobotBase):
    """
    Praganya SalezRobot CRM Implementation.
    """
    def __init__(self, config: Dict[str, Any], session_manager=None):
        # Specific URLs or defaults for Praganya
        if "login_url" not in config:
            config["login_url"] = "https://www.thesalezrobot.com/public/login"
        if "company_name" not in config:
            config["company_name"] = "PRAGNYA"
        if "submit_url" not in config:
            config["submit_url"] = "https://www.thesalezrobot.com/public/admin?Module=Enquiry&view=Edit"
        
        super().__init__(config, session_manager=session_manager)
