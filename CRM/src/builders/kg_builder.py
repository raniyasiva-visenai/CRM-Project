from src.builders.stepstone import StepStoneBase

class KGBuilder(StepStoneBase):
    """
    KG Builders implementation.
    Includes custom phone formatting for +91 prefix.
    """
    def _prepare_payload(self, lead):
        # Override the payload generator to explicitly use 'lead[...]' format
        payload = {
            "lead[first_name]":       lead.first_name or "",
            "lead[last_name]":        lead.last_name or "",
            "lead[email]":            lead.email or "",
            "lead[phone]":            lead.mobile or "",
            "lead[project_id]":       self.config.get("crm_project_id", ""),
            "commit":                 "Save"
        }
        
        # KG specifically requires +91 prefix if not present
        dial = getattr(lead, 'dial_code', '+91')
        if payload["lead[phone]"] and not str(payload["lead[phone]"]).startswith("+"):
            # StepStone backends prefer the format +91-9876543210
            payload["lead[phone]"] = f"{dial}-{payload['lead[phone]']}"
            
        return payload
