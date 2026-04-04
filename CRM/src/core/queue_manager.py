import queue
from src.models.lead import Lead
from typing import Optional

class MessageQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def push(self, lead: Lead):
        print(f"[Queue] Pushing lead: {lead.first_name} ({lead.mobile})")
        self._queue.put(lead)

    def pop(self) -> Optional[Lead]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def size(self) -> int:
        return self._queue.qsize()

# Global queue instance for the system
lead_queue = MessageQueue()
