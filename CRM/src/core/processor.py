import os
import json
import time
from typing import List, Dict, Any, Optional
from src.models.lead import Lead
from config.builders import BUILDER_CLASS_MAP
from src.builders.base import BaseBuilder

class LeadProcessor:
    def __init__(self, db=None, session_manager=None, db_config=None, max_workers: int = 5):
        if db_config and not db:
            from src.utilities.db.utilities import DatabaseUtilities
            self.db = DatabaseUtilities(db_config)
        else:
            self.db = db
        self.session_manager = session_manager
        self.max_workers = max_workers
        
        # Caching logic
        self.builder_configs_cache = {}
        self.last_config_refresh = 0
        self.BUILDER_CONFIG_TTL = 60 # seconds

    def start(self, poll_interval: int = 30):
        """Main loop to process pending leads."""
        print(f"🚀 Lead Processor started (Polling every {poll_interval}s, Concurrency: {self.max_workers})...")
        
        while True:
            try:
                # 1. Fetch 'RECEIVED' leads
                leads = self.db.get_received_leads(batch_size=10)
                
                if leads:
                    print(f"\n[Processor] Found {len(leads)} leads to process.")
                    for lead in leads:
                        self.process_lead(lead, is_login_only=False)
                
                time.sleep(poll_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[Processor] Main Loop Error: {e}")
                time.sleep(poll_interval)

    def process_lead(self, lead: Lead, is_login_only: bool = True):
        """Process a lead and submit it to relevant builders or perform a login audit."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        print(f"\n[Processor] Found lead {lead.leadsource_id}. Matching to builder...")
        
        # 1. Fetch builders (with Caching logic)
        builder_configs = {}
        now = time.time()
        
        if self.builder_configs_cache and (now - self.last_config_refresh < self.BUILDER_CONFIG_TTL):
            builder_configs = self.builder_configs_cache
        else:
            if self.db:
                try:
                    if is_login_only:
                        builder_configs = self.db.get_matching_builder_configs(lead)
                    else:
                        print("[Processor] 📢 BROADCAST MODE: Fetching all active builders...")
                        all_builders = self.db.get_all_active_builders()
                        for b in all_builders:
                            builder_configs[b['builder_name']] = b
                    
                    self.builder_configs_cache = builder_configs
                    self.last_config_refresh = now
                except Exception as e:
                    print(f"[Processor] DB Query Error: {e}")
                    builder_configs = self.builder_configs_cache
        
        eligible_builders = list(builder_configs.keys())
        if not eligible_builders:
            print(f"[Processor] ERROR: No builders to process.")
            return

        print(f"[Processor] {'AUDIT' if is_login_only else 'DISTRIBUTION'} mode: {len(eligible_builders)} builders.")
        
        # Shared state for threads
        success_lock = threading.Lock()
        shared_state = {"success_count": 0}

        def _submit_to_builder(builder_key, config):
            builder_name = config.get('builder_name', builder_key)
            is_login_enabled = config.get('is_login', False)
            
            # 1. Filters (Audit only)
            if is_login_only:
                if not is_login_enabled: return False
                skip_list = ['ArunExcello', 'TPM', 'Urbantree', 'Pragnya', 'MP Developers', 'RLD', 'Nutech', 'Altis', 'VR Foundation', 'Earthen Spaces']
                if builder_name in skip_list:
                    print(f"[Processor] [SKIP] {builder_name} is in the skip list.")
                    return False

            # 2. Resolve builder class
            builder_class = config.get("class")
            if not builder_class:
                crm_type = config.get('crm_type', 'unknown')
                builder_class = BUILDER_CLASS_MAP.get(crm_type.lower())
                if builder_class in [None, BaseBuilder]:
                    name_key = builder_name.lower()
                    if name_key in BUILDER_CLASS_MAP:
                        builder_class = BUILDER_CLASS_MAP[name_key]

            if not builder_class:
                print(f"[Processor] ERROR: No implementation for {builder_name}")
                return False

            # 3. Execution
            success = False
            response_data = None
            crm_lead_id = None
            is_duplicate = False

            try:
                builder = builder_class(config, session_manager=self.session_manager)
                if is_login_only:
                    if hasattr(builder, '_login'):
                        cookies = builder._login()
                        success = bool(cookies)
                        response_data = {"message": "Login result captured"}
                    else:
                        success = True
                        response_data = {"message": "Instantiation verified"}
                else:
                    print(f"[Processor] 🚀 SUBMITTING to {builder_name}...")
                    result = builder.submit_lead(lead)
                    
                    success = result.get('success', False)
                    response_data = result.get('response_data') or result
                    crm_lead_id = result.get('crm_lead_id')
                    is_duplicate = result.get('status') == 'DUPLICATE' or "already exist" in str(response_data).lower()
                    
                    if success and not is_duplicate:
                        print(f"[Processor] ✅ SUCCESS: {builder_name} (CRM ID: {crm_lead_id})")
                    elif is_duplicate:
                        print(f"[Processor] ⚠️ DUPLICATE: {builder_name}")
                        success = True
                    else:
                        print(f"[Processor] ❌ FAILED: {builder_name} - {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"[Processor] Error for {builder_name}: {e}")
                response_data = {"error": str(e)}

            # 4. DB Logging
            if self.db and lead.lead_id:
                try:
                    status_str = 'SUCCESS' if success else 'FAILED'
                    if is_duplicate: status_str = 'DUPLICATE'
                    
                    # Convert UUID to string for PostgreSQL adapter if needed
                    lead_id_str = str(lead.lead_id)
                    
                    self.db.save_distribution_result(
                        lead_id=lead_id_str,
                        builder_id=config.get('builder_id', builder_key),
                        crm_type=config.get('crm_type', 'unknown'),
                        status=status_str,
                        response_data=response_data,
                        crm_lead_id=crm_lead_id,
                        is_duplicate=is_duplicate
                    )
                except Exception as db_err:
                    print(f"[Processor] DB Logging Error for {builder_name}: {db_err}")

            if success:
                with success_lock:
                    shared_state["success_count"] += 1
            return success

        # --- Parallel Execution ---
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(_submit_to_builder, k, builder_configs[k]): k for k in eligible_builders}
            for future in as_completed(futures):
                pass # Just ensuring all complete

        # 6. Final Lead Status Update
        if not is_login_only and self.db and lead.lead_id:
            try:
                final_status = 'PROCESSED' if shared_state["success_count"] > 0 else 'FAILED'
                self.db.update_lead_status(lead.lead_id, final_status)
            except Exception as e:
                print(f"[Processor] Error updating final status: {e}")

        print(f"\n=================================================================")
        print(f"DONE: Processed {len(eligible_builders)} builders in PARALLEL. Success: {shared_state['success_count']}")
        print(f"=================================================================\n")
