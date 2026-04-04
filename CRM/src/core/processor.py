from src.core.queue_manager import lead_queue
from src.core.distribution import LeadDistributionService
from config.builders import BUILDER_CLASS_MAP
from src.utilities.db.utilities import DatabaseUtilities
from src.utilities.sessions import SessionManager
import time
from concurrent.futures import ThreadPoolExecutor

class LeadProcessor:
    def __init__(self, db_config: dict = None, run_once: bool = False, max_workers: int = 5):
        self.run_once = run_once
        self.db = DatabaseUtilities(db_config) if db_config else None
        self.session_manager = SessionManager(self.db) if self.db else None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def start(self):
        print(f"[Processor] Starting Lead Processor worker (Parallel mode, max_workers={self.executor._max_workers})...")
        while True:
            # Poll database for leads with status='RECEIVED'
            leads = self.db.get_received_leads() if self.db else []
            
            if leads:
                print(f"[Processor] Found {len(leads)} new leads. Submitting to parallel execution...")
                for lead in leads:
                    self.executor.submit(self.process_lead, lead)
            
            if self.run_once:
                break
            
            time.sleep(2) # Poll every 2 seconds

    def process_lead(self, lead):
        print(f"\n[Processor] Found lead {lead.leadsource_id}. Matching to builder...")
        
        # 0. Update status to PROCESSING so other workers don't pick it up
        if self.db:
            self.db.update_lead_status(str(lead.lead_id), "PROCESSING")
 
        # 1. Fetch builder configs (Prefer DB, fallback to empty)
        builder_configs = {}
        if self.db:
            try:
                db_configs = self.db.get_active_builder_configs()
                if db_configs:
                    builder_configs = db_configs
                    print("[Processor] Using dynamic builder configurations from database.")
            except Exception as e:
                print(f"[Processor] DB Config Fetch Error: {e}. Falling back to static config.")

        # 2. Find ALL eligible builders
        eligible_builders = LeadDistributionService.get_eligible_builders(lead, builder_configs)
        
        if not eligible_builders:
            print(f"[Processor] ERROR: No matching builder found for lead {lead.lead_id}")
            if self.db:
                self.db.update_lead_status(str(lead.lead_id), "FAILED")
            return

        print(f"[Processor] SUCCESS: Lead matched to {len(eligible_builders)} builders: {eligible_builders}")
        
        success_count = 0
        
        for builder_key in eligible_builders:
            config = builder_configs[builder_key]
            
            # 3. Resolve builder class
            builder_class = config.get("class")
            if not builder_class:
                crm_type = config.get("crm_type", "").lower()
                builder_class = BUILDER_CLASS_MAP.get(crm_type)
            
            if not builder_class:
                actual_type = config.get("crm_type", "unknown")
                print(f"[Processor] ERROR: No implementation class found for CRM type '{actual_type}' (Builder: {builder_key})")
                continue

            print(f"[Processor] Submitting lead {lead.lead_id} to builder: {config.get('builder_name', builder_key)}")
            
            # 4. Instantiate and submit
            max_retries = 3
            attempt = 0
            success = False
            is_duplicate = False
            response_data = None
            crm_lead_id = None
            
            while attempt < max_retries and not success and not is_duplicate:
                attempt += 1
                try:
                    builder = builder_class(config, session_manager=self.session_manager)
                    result = builder.submit_lead(lead) # Actual submission
                    
                    response_str = str(result).lower()
                    duplicate_keywords = ['already registered', 'duplicate', 'already exists', 'has already been taken', 'already exist', 'mobile number already']
                    
                    if any(kw in response_str for kw in duplicate_keywords):
                        is_duplicate = True
                        success = False
                        response_data = result
                        print(f"[Processor] Lead identified as DUPLICATE for builder {builder_key}")
                        break
                        
                    if result.get("success"):
                        success = True
                        response_data = result
                        crm_lead_id = result.get("crm_lead_id")
                    else:
                        success = False
                        response_data = result
                        if attempt < max_retries:
                            print(f"[Processor] Attempt {attempt} failed for {builder_key}. Retrying...")
                            time.sleep(2)
                            
                except Exception as e:
                    response_data = {"error": str(e)}
                    success = False
                    
                    error_str = str(e).lower()
                    duplicate_keywords = ['already registered', 'duplicate', 'already exists', 'has already been taken', 'already exist', 'mobile number already']
                    
                    if type(e).__name__ == "DuplicateLeadError" or any(kw in error_str for kw in duplicate_keywords):
                        is_duplicate = True
                        print(f"[Processor] Lead identified as DUPLICATE via Exception for builder {builder_key}")
                        break
                        
                    if attempt < max_retries:
                        print(f"[Processor] Attempt {attempt} raised error on {builder_key}: {e}. Retrying...")
                        time.sleep(2)

            status = "SUCCESS" if success else "FAILED"
            if is_duplicate:
                status = "DUPLICATE"

            if status in ["SUCCESS", "DUPLICATE"]:
                success_count += 1
                
            self.log_submission(lead, builder_key, config, status=status, response=response_data, crm_lead_id=crm_lead_id, attempt_count=attempt, is_duplicate=is_duplicate)
            print(f"[Processor] {status}: Result from {builder_class.__name__}.submit_lead (Attempts: {attempt}) -> {response_data}")

        # 5. Finalize lead status in DB
        if self.db:
            if success_count == len(eligible_builders):
                final_status = "SUCCESS"
            elif success_count > 0:
                final_status = "PARTIAL"
            else:
                final_status = "FAILED"
                
            self.db.update_lead_status(str(lead.lead_id), final_status)

    def log_submission(self, lead, builder_key, config, status="SUCCESS", response=None, crm_lead_id=None, attempt_count=1, is_duplicate=False):
        if self.db:
            builder_id = config.get("builder_id") # From DB config
            crm_type = config.get("crm_type", "unknown")
            self.db.save_distribution_result(
                lead_id=str(lead.lead_id),
                builder_id=builder_id,
                crm_type=crm_type,
                status=status,
                response_data=response,
                crm_lead_id=crm_lead_id,
                attempt_count=attempt_count,
                is_duplicate=is_duplicate
            )
