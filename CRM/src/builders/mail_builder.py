from src.builders.base import BaseBuilder
from src.models.lead import Lead
from src.services.email_service import EmailService
from src.utils.message_templates import generate_lead_html_message, generate_lead_email_subject, generate_lead_message
from typing import Dict, Any

class MailBuilder(BaseBuilder):
    """
    Generic Mail Builder for lead distribution via Email.
    Uses HTML templates and SMTP configuration.
    
    Required config:
      - delivery_target: Email address(es) to receive the lead (stored in DB).
    """
    
    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.email_service = EmailService()
        self.target_email = config.get("delivery_target")
        
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Send lead details via Email.
        """
        if not self.target_email:
            self.log("Error: No delivery_target email found for this builder.")
            return {"success": False, "error": "Missing delivery_target email."}
            
        try:
            # Prepare subject and bodies
            subject = generate_lead_email_subject(lead, self.config.get("builder_name", "Builder"))
            html_body = generate_lead_html_message(lead, self.config.get("builder_name", "Builder"))
            plain_body = generate_lead_message(lead, self.config.get("builder_name", "Builder"))
            
            # recipients can be a comma-separated string
            recipients = [r.strip() for r in self.target_email.split(",")]
            
            self.log(f"Sending HTML Lead Email to: {self.target_email}")
            
            success = self.email_service.send_email(recipients, subject, html_body, plain_body)
            
            if success:
                self.log("Email distribution successful.")
                return {"success": True, "status": "SUCCESS", "response": f"Email sent to {self.target_email}"}
            else:
                self.log("Email distribution failed.")
                return {"success": False, "error": "Email service failed to send."}
                
        except Exception as e:
            self.log(f"Error during Mail distribution: {e}")
            return {"success": False, "error": str(e)}

    def validate_session(self) -> bool:
        return True
