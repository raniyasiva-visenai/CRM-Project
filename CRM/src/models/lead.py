from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

@dataclass
class Lead:
    leadsource_id: str
    first_name: str
    lead_id: UUID = field(default_factory=uuid4)
    last_name: Optional[str] = None
    mobile: str = "0000000000"
    dial_code: str = "+91"
    secondary_mobile: Optional[str] = None
    secondary_dial_code: Optional[str] = None
    email: Optional[str] = None
    secondary_email: Optional[str] = None
    salutation: str = "Mr"
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    resident_type: Optional[str] = None     # NRI/Indian
    
    # Project & Requirements
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_type: Optional[str] = None      # Apartment/Villa
    property_type: Optional[str] = None     # Residential/Plot
    bhk_type: Optional[str] = None
    sqft_range: Optional[str] = None
    location: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_text: Optional[str] = None       # e.g. "50L"
    
    # Address
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    secondary_country: str = "India"
    pincode: Optional[str] = None

    # Status & Stage
    stage: str = "warm"
    status: str = "RECEIVED"
    lead_type: str = "NEW"                  # NEW/EXISTED
    
    # Site Visit
    site_visit: bool = False
    want_to_create_sitevisit: bool = False
    scheduled_on: Optional[datetime] = None
    count_given: Optional[str] = None
    
    # Broker/CP Info
    cp_id: Optional[str] = None
    cp_name: Optional[str] = None
    cp_company: Optional[str] = None
    cp_phone: Optional[str] = None
    cp_dial_code: Optional[str] = None
    withincptat: Optional[str] = None

    # Referral Info
    referral_name: Optional[str] = None
    referral_email: Optional[str] = None
    referral_mobile: Optional[str] = None
    
    remarks: Optional[str] = None
    source: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
 
    def to_dict(self):
        """Convert Lead to a dictionary mapping to DB columns."""
        return {
            "lead_id":                  str(self.lead_id),
            "leadsource_id":            self.leadsource_id,
            "first_name":               self.first_name,
            "last_name":                self.last_name,
            "mobile":                   self.mobile,
            "dial_code":                self.dial_code,
            "secondary_mobile":         self.secondary_mobile,
            "secondary_dial_code":      self.secondary_dial_code,
            "email":                    self.email,
            "secondary_email":          self.secondary_email,
            "salutation":               self.salutation,
            "gender":                   self.gender,
            "marital_status":           self.marital_status,
            "resident_type":            self.resident_type,
            "project_id":               self.project_id,
            "project_name":             self.project_name,
            "project_type":             self.project_type,
            "property_type":            self.property_type,
            "bhk_type":                 self.bhk_type,
            "sqft_range":               self.sqft_range,
            "location":                 self.location,
            "budget_min":               self.budget_min,
            "budget_max":               self.budget_max,
            "budget_text":              self.budget_text,
            "city":                     self.city,
            "state":                    self.state,
            "country":                  self.country,
            "secondary_country":        self.secondary_country,
            "pincode":                  self.pincode,
            "stage":                    self.stage,
            "status":                   self.status,
            "lead_type":                self.lead_type,
            "site_visit":               self.site_visit,
            "want_to_create_sitevisit": self.want_to_create_sitevisit,
            "scheduled_on":             self.scheduled_on,
            "count_given":              self.count_given,
            "cp_id":                    self.cp_id,
            "cp_name":                  self.cp_name,
            "cp_company":               self.cp_company,
            "cp_phone":                 self.cp_phone,
            "cp_dial_code":             self.cp_dial_code,
            "withincptat":              self.withincptat,
            "referral_name":            self.referral_name,
            "referral_email":           self.referral_email,
            "referral_mobile":          self.referral_mobile,
            "remarks":                  self.remarks,
            "source":                   self.source,
            "raw_payload":              self.raw_payload
        }
