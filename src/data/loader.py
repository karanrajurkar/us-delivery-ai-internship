import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
KB_DIR = os.path.join(DATA_DIR, "kb")

class DataLoader:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.kb_dir = os.path.join(data_dir, "kb")
        self._tickets: Optional[List[Dict[str, Any]]] = None
        self._accounts: Optional[List[Dict[str, Any]]] = None

    def get_tickets(self) -> List[Dict[str, Any]]:
        if self._tickets is None:
            tickets_file = os.path.join(self.data_dir, "tickets.json")
            if os.path.exists(tickets_file):
                with open(tickets_file, "r", encoding="utf-8") as f:
                    self._tickets = json.load(f)
            else:
                self._tickets = []
        return self._tickets

    def get_accounts(self) -> List[Dict[str, Any]]:
        if self._accounts is None:
            accounts_file = os.path.join(self.data_dir, "accounts.json")
            if os.path.exists(accounts_file):
                with open(accounts_file, "r", encoding="utf-8") as f:
                    self._accounts = json.load(f)
            else:
                self._accounts = []
        return self._accounts

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        accounts = self.get_accounts()
        for acc in accounts:
            if acc.get("account_id").lower() == account_id.lower():
                return acc
        return None

    def get_account_tickets(self, account_id: str, days: int = 90) -> List[Dict[str, Any]]:
        all_tickets = self.get_tickets()
        account_tickets = [t for t in all_tickets if t.get("account_id", "").lower() == account_id.lower()]
        
        # Filter last 90 days if created_at timestamp is present
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_tickets = []
        
        for ticket in account_tickets:
            created_str = ticket.get("created_at")
            if created_str:
                try:
                    # Clean ISO format
                    clean_str = created_str.replace("Z", "")
                    t_date = datetime.fromisoformat(clean_str)
                    if t_date >= cutoff_date:
                        filtered_tickets.append(ticket)
                except Exception:
                    filtered_tickets.append(ticket)
            else:
                filtered_tickets.append(ticket)
                
        # Sort by creation date descending
        filtered_tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return filtered_tickets

    def get_knowledge_base_docs(self) -> Dict[str, str]:
        docs = {}
        if os.path.exists(self.kb_dir):
            for fname in os.listdir(self.kb_dir):
                if fname.endswith(".md"):
                    path = os.path.join(self.kb_dir, fname)
                    with open(path, "r", encoding="utf-8") as f:
                        docs[fname] = f.read()
        return docs
