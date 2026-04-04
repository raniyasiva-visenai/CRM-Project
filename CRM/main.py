import sys
import os
from src.core.processor import LeadProcessor
from config.db import DB_CONFIG  # Assuming you'll create this config soon

def run_worker():
    """
    Official Entry Point for the CRM Lead Automation System.
    Starts the LeadProcessor to handle incoming leads from the queue/DB.
    """
    print("Lead Automation System starting...")
    
    # In production, pass your actual DB credentials here
    processor = LeadProcessor(db_config=DB_CONFIG) 
    
    try:
        processor.start()
    except KeyboardInterrupt:
        print("\nSystem shutting down gracefully...")

if __name__ == "__main__":
    run_worker()
