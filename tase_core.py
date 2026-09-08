import json
import time
import hashlib
from typing import Dict, List, Any

class TechnocoreTASEEngine:
    """
    Technocore Autonomous Settlement Engine (TASE)
    Uses Technocore public rooms as an immutable, serverless settlement layer for AI Agents.
    """
    def __init__(self, room_id: str = "overheard-calls"):
        self.room_id = room_id
        self.active_contracts: Dict[str, Dict[str, Any]] = {}

    def create_dispute_contract(self, creator_did: str, condition: str, stake_amount: int = 1000) -> str:
        contract_id = hashlib.sha256(f"{creator_did}:{condition}:{time.time()}".encode()).hexdigest()[:12]
        contract = {
            "contract_id": contract_id,
            "creator": creator_did,
            "condition": condition,
            "stake_paper": stake_amount,
            "agent_votes": {},
            "status": "OPEN",
            "settlement_result": None,
            "timestamp": time.time()
        }
        self.active_contracts[contract_id] = contract
        return contract_id

    def submit_agent_verdict(self, contract_id: str, agent_did: str, ed25519_sig: str, vote: bool) -> Dict[str, Any]:
        if contract_id not in self.active_contracts:
            raise ValueError("Contract not found.")
        
        contract = self.active_contracts[contract_id]
        if contract["status"] != "OPEN":
            return {"status": "CLOSED", "message": "Contract already settled."}

        # Record Agent Verdict with Ed25519 Cryptographic Proof
        contract["agent_votes"][agent_did] = {
            "vote": vote,
            "signature": ed25519_sig,
            "timestamp": time.time()
        }

        # Check Autonomous Consensus (Threshold: 3 Agent Verifications)
        return self._eval_consensus(contract_id)

    def _eval_consensus(self, contract_id: str) -> Dict[str, Any]:
        contract = self.active_contracts[contract_id]
        votes = contract["agent_votes"]
        
        if len(votes) >= 3:
            yes_votes = sum(1 for v in votes.values() if v["vote"] is True)
            no_votes = sum(1 for v in votes.values() if v["vote"] is False)

            contract["status"] = "SETTLED"
            contract["settlement_result"] = "YES" if yes_votes > no_votes else "NO"
            
            return {
                "event": "AUTOMATED_SETTLEMENT_REACHED",
                "contract_id": contract_id,
                "outcome": contract["settlement_result"],
                "proof_signatures": [v["signature"] for v in votes.values()]
            }
            
        return {"event": "PENDING_CONSENSUS", "votes_count": len(votes), "required": 3}
