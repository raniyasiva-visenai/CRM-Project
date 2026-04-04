import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from datetime import datetime

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load .env file automatically
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                if key not in os.environ:
                    os.environ[key] = val

from config.db import DB_CONFIG

# --- EMAIL CONFIGURATION ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your_email@gmail.com") 
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "admin@maruthamprop.com").split(",")

class FailureWatcherService:
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.is_running = False

    def get_db_connection(self):
        return psycopg2.connect(**self.db_config)

    def start(self):
        self.is_running = True
        print("[FailureWatcher] Starting service. Polling every 10 seconds...")
        
        while self.is_running:
            try:
                self.check_for_failures()
            except Exception as e:
                print(f"[FailureWatcher] Error during polling cycle: {e}")
            
            time.sleep(10)

    def check_for_failures(self):
        """Finds FAILED distributions without an alert notification."""
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Query joins Leads + Builders to provide context for the email payload
                query = """
                    SELECT 
                        lcd.distribution_id, lcd.lead_id, lcd.builder_id, lcd.crm_type, 
                        lcd.crm_response, lcd.attempt_count, lcd.submitted_at,
                        b.builder_name,
                        l.first_name, l.last_name, l.mobile, l.email, l.project_name
                    FROM lead_crm_distribution lcd
                    JOIN builders b ON lcd.builder_id = b.builder_id
                    JOIN leads l ON lcd.lead_id = l.lead_id
                    WHERE lcd.status = 'FAILED'
                    AND NOT EXISTS (
                        SELECT 1 FROM alert_notifications an 
                        WHERE an.distribution_id = lcd.distribution_id
                          AND an.alert_type = 'CRM_FAILURE'
                    )
                """
                cur.execute(query)
                failed_records = cur.fetchall()

                if not failed_records:
                    return

                print(f"[FailureWatcher] Detected {len(failed_records)} new FAILED distributions!")

                for record in failed_records:
                    success = self.send_failure_email(record)
                    
                    if success:
                        self.mark_alert_sent(cur, record)
                        
                conn.commit()

        finally:
            conn.close()

    def send_failure_email(self, record):
        """Sends an email with failure details."""
        subject = f"Alert: CRM Submission FAILED - {record['builder_name']} ({record['crm_type']})"
        
        body = f"""
        A CRM submission has FAILED after {record['attempt_count']} attempts.

        --- BUILDER INFO ---
        Builder: {record['builder_name']}
        CRM Type: {record['crm_type']}
        
        --- LEAD DETAILS ---
        Name: {record['first_name']} {record.get('last_name', '')}
        Mobile: {record['mobile']}
        Email: {record.get('email', 'N/A')}
        Project Requested: {record.get('project_name', 'N/A')}

        --- FAILURE DETAILS ---
        Submission Time: {record['submitted_at']}
        CRM Response/Error: 
        {record.get('crm_response')}

        Please review the dashboard or database (Distribution ID: {record['distribution_id']}).
        """

        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = ", ".join(ADMIN_EMAILS)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            # We skip actual SMTP sending if default placeholder is used just to avoid crashing,
            # but usually you'd configure the real credentials.
            if SMTP_USERNAME == "your_email@gmail.com":
                print(f"[FailureWatcher] (Mock Email) Sending to {ADMIN_EMAILS}: {subject}")
                return True

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"[FailureWatcher] Email sent successfully for distribution {record['distribution_id']}")
            return True
        except Exception as e:
            print(f"[FailureWatcher] Error sending email: {e}")
            return False

    def mark_alert_sent(self, cur, record):
        """Inserts an alert_notifications record so we don't spam emails."""
        cur.execute("""
            INSERT INTO alert_notifications (
                lead_id, builder_id, distribution_id, 
                alert_type, alert_medium, alert_sent, sent_time
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            record['lead_id'], record['builder_id'], record['distribution_id'],
            'CRM_FAILURE', 'EMAIL', True
        ))

if __name__ == "__main__":
    watcher = FailureWatcherService(DB_CONFIG)
    watcher.start()
