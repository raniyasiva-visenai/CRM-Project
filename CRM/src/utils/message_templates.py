from src.models.lead import Lead

def generate_lead_html_message(lead: Lead, builder_name: str) -> str:
    """
    Generate a professional HTML lead message for Email.
    Includes ALL lead details categorized.
    """
    
    # Helper for table rows
    def row(label, value):
        if value is None or str(value).strip() == "" or str(value) == "None":
            return ""
        return f"<tr><th>{label}</th><td>{value}</td></tr>"

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; background-color: #f4f7f6; }}
            .container {{ max-width: 650px; margin: 20px auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); background-color: #ffffff; }}
            .header {{ background-color: #2c3e50; color: #ffffff; padding: 30px; text-align: center; }}
            .header h2 {{ margin: 0; letter-spacing: 2px; font-weight: 600; font-size: 24px; }}
            .section {{ padding: 25px 35px; border-bottom: 1px solid #f0f0f0; }}
            .section-title {{ color: #7f8c8d; font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 15px; font-weight: bold; border-left: 3px solid #3498db; padding-left: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
            th {{ text-align: left; width: 45%; padding: 12px 0; color: #7f8c8d; font-weight: 500; font-size: 14px; border-bottom: 1px solid #f9f9f9; }}
            td {{ padding: 12px 0; font-weight: 600; color: #2c3e50; font-size: 14px; border-bottom: 1px solid #f9f9f9; }}
            .footer {{ background-color: #f9f9f9; padding: 20px; text-align: center; font-size: 12px; color: #999; }}
            .status-badge {{ background-color: #e8f6f3; color: #1abc9c; padding: 4px 12px; border-radius: 12px; font-size: 11px; text-transform: uppercase; font-weight: bold; }}
            .remarks-box {{ background-color: #fdfefe; border-left: 4px solid #3498db; padding: 20px; font-size: 14px; font-style: italic; color: #555; margin-top: 10px; box-shadow: inset 0 0 10px rgba(0,0,0,0.02); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>NEW LEAD RECEIVED</h2>
            </div>
            
            <!-- Category: Customer Details -->
            <div class="section">
                <div class="section-title">CUSTOMER PROFILE</div>
                <table>
                    {row("Customer Name", f"{lead.salutation} {lead.first_name} {lead.last_name or ''}")}
                    {row("Contact Phone", f"{lead.dial_code} {lead.mobile}")}
                    {row("Secondary Phone", f"{lead.secondary_dial_code or ''} {lead.secondary_mobile or ''}")}
                    {row("Email Address", lead.email)}
                    {row("Secondary Email", lead.secondary_email)}
                    {row("Resident Type", lead.resident_type)}
                    {row("Gender", lead.gender)}
                </table>
            </div>

            <!-- Category: Requirement Details -->
            <div class="section">
                <div class="section-title">PROJECT & REQUIREMENTS</div>
                <table>
                    {row("Interested Project", lead.project_name)}
                    {row("Project Type", lead.project_type)}
                    {row("BHK Requirement", lead.bhk_type)}
                    {row("Preferred Location", lead.location)}
                    {row("Sqft Range", lead.sqft_range)}
                    {row("Budget", lead.budget_text or (f"{lead.budget_min} - {lead.budget_max}" if lead.budget_min else None))}
                    {row("Property Type", lead.property_type)}
                </table>
            </div>

            <!-- Category: CP / Broker / Referral -->
            <div class="section">
                <div class="section-title">SOURCE & CHANNEL PARTNER</div>
                <table>
                    {row("Distribution Builder", builder_name)}
                    {row("Lead Source", lead.source or lead.leadsource_id)}
                    {row("CP Name", lead.cp_name)}
                    {row("CP Company", lead.cp_company)}
                    {row("CP Phone", lead.cp_phone)}
                    {row("Referral Name", lead.referral_name)}
                </table>
            </div>

            <!-- Category: Site Visit Info (If available) -->
            {f'''
            <div class="section">
                <div class="section-title">SITE VISIT SCHEDULE</div>
                <table>
                    {row("Site Visit Requested", "YES" if lead.site_visit else "NO")}
                    {row("Scheduled On", lead.scheduled_on.strftime('%Y-%m-%d %H:%M') if lead.scheduled_on else None)}
                    {row("Visit Stages", lead.stage)}
                </table>
            </div>
            ''' if lead.site_visit or lead.scheduled_on else ''}

            <!-- Category: Address -->
            <div class="section">
                <div class="section-title">ADDRESS INFO</div>
                <table>
                    {row("City", lead.city)}
                    {row("State", lead.state)}
                    {row("Country", lead.country)}
                    {row("Pincode", lead.pincode)}
                </table>
            </div>

            <!-- Category: Remarks -->
            <div class="section" style="border-bottom: none;">
                <div class="section-title">CUSTOMER REMARKS</div>
                <div class="remarks-box">
                    {lead.remarks or 'Looking for more details regarding the mentioned project. Please coordinate for future actions.'}
                </div>
            </div>

            <div class="footer">
                Lead ID: {lead.lead_id}<br>
                Received at: {lead.created_at.strftime('%Y-%m-%d %H:%M:%S')}<br>
                &copy; 2026 CRM Distribution Hub
            </div>
        </div>
    </body>
    </html>
    """
    return html

def generate_lead_message(lead: Lead, builder_name: str) -> str:
    """Fallback plain text message with more details."""
    return f"""
New Lead for {builder_name}
-----------------------------
Name: {lead.first_name} {lead.last_name or ''}
Phone: {lead.mobile}
Email: {lead.email}
Project: {lead.project_name}
Budget: {lead.budget_text or 'N/A'}
Location: {lead.location}
Remarks: {lead.remarks}
    """.strip()

def generate_lead_email_subject(lead: Lead, builder_name: str) -> str:
    return f"New Lead: {lead.first_name} - Interested in {lead.project_name or builder_name}"
