from src.models.lead import Lead
from typing import List, Optional, Dict, Any

class LeadDistributionService:
    @staticmethod
    def get_eligible_builders(lead: Lead, builder_configs: Dict[str, Any]) -> List[str]:
        """
        Match a lead to eligible builders based on location and project type.
        Uses the provided builder_configs dictionary.
        """
        eligible = []
        
        for builder_key, config in builder_configs.items():
            # 1. Match by location
            builder_location = (config.get("location") or "").lower()
            lead_location = (lead.location or "").lower()
            
            # 2. Match by Project Type
            builder_project = (config.get("project_type") or "").lower()
            lead_project = (lead.project_type or "").lower()
            
            # Simple match: if both match or if builder accepts any ('*')
            location_match = not builder_location or builder_location == "*" or builder_location in lead_location or lead_location in builder_location
            project_match = not builder_project or builder_project == "*" or builder_project == lead_project
            
            # 3. Match by Budget (Overlap check)
            # Logic: (Lead Max >= Project Min) AND (Lead Min <= Project Max)
            # If lead or project budgets are not specified (None or 0), assume they match.
            project_min = float(config.get("min_budget") or 0)
            project_max = float(config.get("max_budget") or 0)
            lead_min = float(lead.budget_min or 0)
            lead_max = float(lead.budget_max or 0)
            
            budget_match = True
            if project_min > 0 and lead_max > 0:
                if lead_max < project_min:
                    budget_match = False
            if project_max > 0 and lead_min > 0:
                if lead_min > project_max:
                    budget_match = False
                    
            if location_match and project_match and budget_match:
                eligible.append(builder_key)
                
        return eligible

    @staticmethod
    def select_best_builder(lead: Lead, builder_configs: Dict[str, Any]) -> Optional[str]:
        """Select the single best builder for a lead."""
        eligible = LeadDistributionService.get_eligible_builders(lead, builder_configs)
        if not eligible:
            return None
        # Return the first match for now
        return eligible[0]
