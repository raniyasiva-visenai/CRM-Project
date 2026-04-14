from src.builders.base import BaseBuilder
from src.models.lead import Lead
from src.utils.message_templates import generate_lead_message
from typing import Dict, Any

class WhatsAppBuilder(BaseBuilder):
    """
    Generic WhatsApp Builder for lead distribution.
    Pull phone number from the 'delivery_target' column.
    
    Required config:
      - delivery_target: WhatsApp number
    """
    
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.target_phone = config.get("delivery_target")
        
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Prepare and 'send' lead details via WhatsApp.
        """
        if not self.target_phone:
            self.log("Error: No delivery_target phone number found.")
            return {"success": False, "error": "Missing delivery_target phone."}
            
        try:
            # Generate WhatsApp-optimized message (using asterisks for bold etc)
            message = self.generate_whatsapp_content(lead)
            
            self.log(f"Preparing WhatsApp lead for: {self.target_phone}")
            self.log(f"Content:\n{message}")
            
            # TODO: Integrate with specific WhatsApp API (Cloud API, Interakt, etc.)
            # For now, we simulate a successful preparation
            
            return {
                "success": True, 
                "status": "QUEUED_WA", 
                "response": f"Lead prepared for WhatsApp: {self.target_phone}. [Mock Distribution Successful]"
            }
                
        except Exception as e:
            self.log(f"Error during WhatsApp distribution: {e}")
            return {"success": False, "error": str(e)}

    def generate_whatsapp_content(self, lead: Lead) -> str:
        builder_name = self.config.get("builder_name", "Builder")
        
        # Professional WhatsApp Markdown format
        message = f"""
*NEW LEAD RECEIVED FOR {builder_name.upper()}*

*CUSTOMER DETAILS:*
• *Name:* {lead.first_name} {lead.last_name or ''}
• *Phone:* {lead.mobile}
• *Email:* {lead.email or 'N/A'}

*PROJECT INTEREST:*
• *Project:* {lead.project_name or 'General Enquiry'}
• *Location:* {lead.location or 'Chennai'}

*REMARKS:*
_{lead.remarks or 'Looking for more info.'}_

---
_Sent via CRM Distribution System_
        """.strip()
        return message

    def validate_session(self) -> bool:
        return True
