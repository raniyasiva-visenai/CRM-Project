"""
SellDoBase — common base for SellDo checklead.php → sitevisit.php builders.
Used by Royal Land Developers and LML Homes.
"""

import requests
import json
from datetime import datetime
from src.builders.base import BaseBuilder
from src.models.lead import Lead
from typing import Dict, Any, Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0 Safari/537.36",
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://forms.sell.do",
}


def _fmt_date(dt: datetime) -> str:
    """Format datetime as 'D-M-YYYY HH:MM' (no zero-padding, Windows safe)."""
    return f"{dt.day}-{dt.month}-{dt.year} {dt.strftime('%H:%M')}"


def _with_91(phone: str) -> str:
    phone = phone.strip()
    if phone.startswith("+"): return phone
    if phone.startswith("91") and len(phone) == 12: return f"+{phone}"
    return f"+91{phone}"


class SellDoBase(BaseBuilder):
    """
    Two-step SellDo form submission:
      Step 1 — POST checklead.php  → get selldoid if lead exists
      Step 2 — POST sitevisit.php  → submit lead using selldoid
    """

    def __init__(self, config: Dict[str, Any], session_manager=None):
        super().__init__(config, session_manager=session_manager)
        self.checklead_url  = config.get("checklead_url", "")
        self.sitevisit_url  = config.get("submit_url",    "")
        self.form_page_url  = config.get("form_page_url", "")
        self.cp_id          = config.get("cp_id",     "")
        self.cp_name        = config.get("username",  "")
        self.cp_company     = config.get("cp_company","")
        self.cp_phone       = config.get("cp_phone",  "")
        self.cp_dial_code   = config.get("cp_dial_code", "91")

    # ── Step 1 ────────────────────────────────────────────────────────────────
    def _check_lead(self, phone: str, project_id: str, project_name: str) -> Dict:
        payload = {
            "projectidbyurl":   project_id,
            "projectnamebyurl": project_name,
            "inputvalue":       phone,
        }
        referer = f"{self.form_page_url}?projectid={project_id}&projectname={project_name}" \
                  if self.form_page_url else self.sitevisit_url

        try:
            resp = requests.post(
                self.checklead_url, data=payload,
                headers={**HEADERS, "Referer": referer}, timeout=30
            )
            raw = resp.text.strip()
            result = {"exists": False, "selldoid": "", "leadtype": "new", "currently_in": "pre_sales"}

            if raw.startswith("exists=="):
                result["exists"]   = True
                result["leadtype"] = "existed"
                parts = raw.split("==", 2)
                if len(parts) >= 2:
                    try:
                        data = json.loads(parts[1])
                        lead = data.get("lead", {})
                        result["selldoid"]     = str(lead.get("lead_id", ""))
                        result["currently_in"] = lead.get("currently_in", "pre_sales")
                    except json.JSONDecodeError:
                        pass
            return result
        except Exception as e:
            self.log(f"checklead.php error: {e}")
            return {"exists": False, "selldoid": "", "leadtype": "new", "currently_in": "pre_sales"}

    # ── Step 2 ────────────────────────────────────────────────────────────────
    def _submit_sitevisit(self, lead: Lead, check_result: Dict) -> Dict[str, Any]:
        project_id   = lead.project_id or ""
        project_name = lead.project_name or ""

        referer = f"{self.form_page_url}?projectid={project_id}&projectname={project_name}" \
                  if self.form_page_url else self.sitevisit_url

        broker_str = f"{self.cp_name}--{self.cp_company}--{self.cp_id}"

        phone = _with_91(lead.mobile or "")
        cp_fullphone = f"0{self.cp_phone}  {self.cp_phone}"

        scheduled = _fmt_date(lead.scheduled_on) if lead.scheduled_on else _fmt_date(datetime.now())

        payload = {
            "selldoid":               check_result.get("selldoid", ""),
            "leadtype":               check_result.get("leadtype",  "new"),
            "channelpartnername":     lead.cp_name or "",
            "currently_in":           check_result.get("currently_in", "pre_sales"),
            "projectidbyurl":         project_id,
            "withincptat":            lead.withincptat or "yes --",
            "salutation":             lead.salutation or "Mr",
            "name":                   f"{lead.first_name} {lead.last_name or ''}".strip(),
            "dial_code":              lead.dial_code or "+91",
            "phone":                  phone,
            "country":                "IN",
            "mail_id":                lead.email or "",
            "projects_details":       project_id,
            "custom_broker_name":     broker_str,
            "cpfullphone":            cp_fullphone,
            "cpdailcode":             self.cp_dial_code,
            "cpphone":                self.cp_phone,
            "remarks":                lead.remarks or "",
            "scheduledon":            scheduled,
            "want_to_create_sitevisit": "no" if not lead.want_to_create_sitevisit else "yes",
        }

        try:
            resp = requests.post(
                self.sitevisit_url, data=payload,
                headers={**HEADERS, "Referer": referer}, timeout=30
            )
            selldoid = resp.text.strip()
            success  = selldoid.isdigit()
            self.log(f"sitevisit.php responded: {resp.status_code} — selldoid={selldoid}")
            return {
                "success":    success,
                "status":     resp.status_code,
                "crm_lead_id": selldoid if success else None,
                "response":   resp.text,
            }
        except Exception as e:
            self.log(f"sitevisit.php error: {e}")
            return {"success": False, "error": str(e)}

    # ── Public entry point ────────────────────────────────────────────────────
    def submit_lead(self, lead: Lead) -> Dict[str, Any]:
        phone = lead.mobile or ""
        project_id   = lead.project_id   or ""
        project_name = lead.project_name or ""

        self.log(f"Step 1: checklead for phone {phone}...")
        check_result = self._check_lead(phone, project_id, project_name)
        self.log(f"  → exists={check_result['exists']}, selldoid={check_result['selldoid']}")

        self.log("Step 2: submitting to sitevisit.php...")
        return self._submit_sitevisit(lead, check_result)

    def validate_session(self) -> bool:
        return True   # No session for SellDo (stateless HTTP)
