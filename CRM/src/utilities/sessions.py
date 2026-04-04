import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.utilities.db.utilities import DatabaseUtilities

class SessionManager:
    def __init__(self, db: DatabaseUtilities, sessions_dir: str = "data/sessions"):
        self.db = db
        self.sessions_dir = sessions_dir
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir, exist_ok=True)

    def _get_file_path(self, builder_name: str) -> str:
        safe_name = builder_name.lower().replace(" ", "_")
        return os.path.join(self.sessions_dir, f"cookies_{safe_name}.json")

    def get_session(self, builder_id: str, credential_id: str, builder_name: str) -> Optional[List[Dict]]:
        """
        Attempts to retrieve a valid session from DB, then filesystem.
        """
        # 1. Try Database
        session_data = self.db.get_active_session(credential_id)
        if session_data and session_data.get('cookies'):
            print(f"[Session] Loaded session for {builder_name} from Database.")
            return session_data['cookies']

        # 2. Try Filesystem
        file_path = self._get_file_path(builder_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    cookies = json.load(f)
                print(f"[Session] Loaded session for {builder_name} from Filesystem ({file_path}).")
                # Sync back to DB if missing
                self.db.save_crm_session(builder_id, credential_id, "unknown", cookies)
                return cookies
            except Exception as e:
                print(f"[Session] Error reading session file {file_path}: {e}")

        return None

    def save_session(self, builder_id: str, credential_id: str, builder_name: str, crm_type: str, cookies: List[Dict], extra_tokens: Dict = None):
        """
        Saves session to both DB and Filesystem.
        """
        # 1. Save to Database
        self.db.save_crm_session(builder_id, credential_id, crm_type, cookies, extra_tokens)

        # 2. Save to Filesystem
        file_path = self._get_file_path(builder_name)
        try:
            with open(file_path, "w") as f:
                json.dump(cookies, f, indent=2)
            print(f"[Session] Saved session for {builder_name} to {file_path}")
        except Exception as e:
            print(f"[Session] Error saving session file {file_path}: {e}")

    def invalidate_session(self, credential_id: str, builder_name: str):
        """
        Marks session as invalid in DB and removes the local file.
        """
        # 1. Invalidate in DB
        conn = self.db.connect()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE crm_sessions SET is_valid = FALSE WHERE credential_id = %s", (credential_id,))
                conn.commit()
        finally:
            self.db.release(conn)

        # 2. Remove file
        file_path = self._get_file_path(builder_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[Session] Removed session file {file_path}")
