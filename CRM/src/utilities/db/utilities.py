try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    pool = None
from typing import List, Dict, Any, Optional
from src.models.lead import Lead

class DatabaseUtilities:
    _pool = None

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        if DatabaseUtilities._pool is None and pool:
            print("[DB] Initializing Threaded Connection Pool (min=1, max=10)...")
            DatabaseUtilities._pool = pool.ThreadedConnectionPool(1, 10, **db_config)

    def connect(self):
        """Gets a connection from the pool."""
        return DatabaseUtilities._pool.getconn()

    def release(self, conn):
        """Returns a connection to the pool."""
        if DatabaseUtilities._pool and conn:
            DatabaseUtilities._pool.putconn(conn)

    def save_lead(self, lead: Lead):
        """Inserts a Lead into the database using its to_dict method."""
        data = lead.to_dict()
        columns = data.keys()
        
        # Prepare values, ensuring raw_payload is JSON stringified for safety
        import json
        values = []
        for v in data.values():
            if isinstance(v, dict):
                values.append(json.dumps(v))
            else:
                values.append(v)

        # Build the UPDATE clause dynamically for all columns except keys
        update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['lead_id', 'leadsource_id']])
        
        sql = f"""
            INSERT INTO leads ({', '.join(columns)}) 
            VALUES ({', '.join(['%s'] * len(columns))})
            ON CONFLICT (leadsource_id) DO UPDATE SET
                {update_clause},
                updated_at = NOW()
            RETURNING lead_id
        """
        
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, values)
                lead_id = cur.fetchone()[0]
                conn.commit()
                print(f"[DB] Lead {lead.leadsource_id} saved/updated (ID: {lead_id})")
                return lead_id
        except Exception as e:
            conn.rollback()
            print(f"[DB] Error saving lead {lead.leadsource_id}: {e}")
            return None
        finally:
            self.release(conn)

    def update_lead_status(self, lead_id: str, status: str):
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE leads SET status = %s, updated_at = NOW() WHERE lead_id = %s", (status, lead_id))
                conn.commit()
        finally:
            self.release(conn)
 
    def save_distribution_result(self, lead_id: str, builder_id: str, crm_type: str, status: str, response_data: dict = None, crm_lead_id: str = None, attempt_count: int = 1, is_duplicate: bool = False):
        """Logs the result of a CRM submission attempt."""
        import json
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO lead_crm_distribution (
                        lead_id, builder_id, crm_type, status, crm_response, crm_lead_id, attempt_count, is_duplicate, submitted_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    lead_id, builder_id, crm_type, status, 
                    json.dumps(response_data) if response_data else None,
                    crm_lead_id, attempt_count, is_duplicate
                ))
                conn.commit()
                print(f"[DB] Distribution result logged for lead {lead_id} -> builder {builder_id}")
        except Exception as e:
            conn.rollback()
            print(f"[DB] Error logging distribution: {e}")
        finally:
            self.release(conn)

    def get_matching_builder_configs(self, lead: Lead) -> Dict[str, Any]:
        """
        matches leads to builders/projects using SQL queries.
        Matches based on location and property type (Villa, Plot, Apartment).
        """
        # Safety Guard: If no search criteria are provided, return empty to prevent mass-distribution
        if not any([lead.location, lead.property_type, lead.project_type, lead.project_name]):
            print(f"[DB] Safety Guard: Lead {lead.leadsource_id} has no location, type, or project name. Skipping matching.")
            return {}

        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Prepare lead search terms
                location = lead.location if lead.location else ""
                prop_type = lead.property_type if lead.property_type else ""
                proj_type = lead.project_type if lead.project_type else ""
                proj_name = lead.project_name if lead.project_name else ""
                
                sql = """
                    SELECT 
                        b.builder_id,
                        b.builder_name,
                        b.crm_type,
                        bp.project_name,
                        bp.crm_project_id,
                        bp.location,
                        bp.property_type as project_type,
                        bp.min_budget,
                        bp.max_budget,
                        bcc.crm_url as submit_url,
                        bcc.username,
                        bcc.credential_id,
                        bcc.extra_config
                    FROM builders b
                    JOIN builder_projects bp ON b.builder_id = bp.builder_id
                    JOIN builder_crm_credentials bcc ON b.builder_id = bcc.builder_id
                    WHERE b.is_active = TRUE 
                      AND bp.is_active = TRUE 
                      AND bcc.is_active = TRUE
                      AND (
                        
                          bp.location = '*' OR 
                          bp.location ILIKE %s OR 
                          %s ILIKE bp.location OR
                          bp.location IS NULL
                      )
                      AND (
                         
                          bp.property_type = '*' OR
                          bp.property_type ILIKE %s OR 
                          bp.property_type ILIKE %s OR
                          bp.project_name ILIKE %s OR 
                          bp.property_type IS NULL
                      )
                """
                
                cur.execute(sql, (
                    f"%{location}%", location, 
                    f"%{prop_type}%", f"%{proj_type}%", f"%{proj_name}%"
                ))
                
                rows = cur.fetchall()
                
                configs = {}
                for row in rows:
                    # Create a unique key for each project implementation
                    key = f"{row['crm_type'].upper()}_{row['builder_name'].upper().replace(' ', '_')}_{row['project_name'].upper().replace(' ', '_')}"
                    
                    config = dict(row)
                    if row['extra_config']:
                        config.update(row['extra_config'])
                    
                    configs[key] = config
                    
                return configs
        finally:
            self.release(conn)

    def get_pending_distributions(self) -> List[Dict[str, Any]]:
        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM lead_crm_distribution WHERE status = 'PENDING'")
                return cur.fetchall()
        finally:
            self.release(conn)

    def get_received_leads(self) -> List[Lead]:
        """Fetches leads with status='RECEIVED' and returns them as Lead objects."""
        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM leads WHERE status = 'RECEIVED' ORDER BY created_at ASC")
                rows = cur.fetchall()
                
                leads = []
                for row in rows:
                    # Convert RealDictRow to regular dict
                    data = dict(row)
                    
                    # Cleanup internal DB fields
                    # The Lead dataclass constructor will take Lead(**data)
                    # We should ensure lead_id is a UUID object if it's a string, 
                    # but psycopg2 usually gives UUID objects for UUID columns.
                    
                    # Remove timestamps if present to avoid confusion with Lead defaults
                    data.pop('created_at', None)
                    data.pop('updated_at', None)
                    
                    try:
                        leads.append(Lead(**data))
                    except TypeError as e:
                        print(f"[DB] Error mapping row to Lead: {e}")
                return leads
        finally:
            self.release(conn)

    # -------------------------------------------------------------
    # SESSION MANAGEMENT
    # -------------------------------------------------------------
    def save_crm_session(self, builder_id: str, credential_id: str, crm_type: str, cookies: List[Dict], extra_tokens: Dict = None):
        """Saves or updates a CRM session in the database."""
        import json
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO crm_sessions (
                        builder_id, credential_id, crm_type, cookies, extra_tokens, is_valid, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, TRUE, NOW())
                    ON CONFLICT (credential_id) DO UPDATE SET
                        cookies = EXCLUDED.cookies,
                        extra_tokens = EXCLUDED.extra_tokens,
                        is_valid = TRUE,
                        updated_at = NOW()
                """, (
                    builder_id, credential_id, crm_type, 
                    json.dumps(cookies), 
                    json.dumps(extra_tokens) if extra_tokens else json.dumps({})
                ))
                conn.commit()
                print(f"[DB] Session saved for builder {builder_id} (Type: {crm_type})")
        except Exception as e:
            conn.rollback()
            print(f"[DB] Error saving session: {e}")
        finally:
            self.release(conn)

    def get_active_session(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a valid session for a given credential ID."""
        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT cookies, extra_tokens 
                    FROM crm_sessions 
                    WHERE credential_id = %s AND is_valid = TRUE
                """, (credential_id,))
                return cur.fetchone()
        finally:
            self.release(conn)
