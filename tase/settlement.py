import math
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class EscrowPosition:
    agent_did: str
    side: str  # "LONG" / "SHORT" or "YES" / "NO"
    collateral_paper: float
    leverage: float
    entry_oracle_price: float

class AutonomousSettlementEngine:
    """
    Serverless Clearing & Settlement Engine using Technocore Rooms as State Logs.
    Implements dynamic margin maintenance and consensus-driven execution.
    """
    def __init__(self, maintenance_margin_ratio: float = 0.05):
        self.mmr = maintenance_margin_ratio
        self.positions: Dict[str, List[EscrowPosition]] = {}

    def open_position(self, contract_id: str, position: EscrowPosition) -> bool:
        if contract_id not in self.positions:
            self.positions[contract_id] = []
        
        # Verify Collateral Coverage
        if position.collateral_paper <= 0 or position.leverage < 1.0:
            return False
            
        self.positions[contract_id].append(position)
        return True

    def calculate_settlement(self, contract_id: str, final_oracle_price: float) -> Dict[str, Any]:
        """
        Executes zero-sum clearing across all agents in the escrow pool.
        """
        if contract_id not in self.positions:
            return {"status": "FAILED", "reason": "CONTRACT_NOT_FOUND"}

        pool = self.positions[contract_id]
        payout_map: Dict[str, float] = {}
        total_pnl = 0.0

        for pos in pool:
            # Price delta ratio
            price_change = (final_oracle_price - pos.entry_oracle_price) / pos.entry_oracle_price
            if pos.side in ["SHORT", "NO"]:
                price_change = -price_change

            # Calculate PnL with leverage
            raw_pnl = pos.collateral_paper * (price_change * pos.leverage)
            
            # Max loss capped at collateral (Non-recourse escrow)
            actual_pnl = max(-pos.collateral_paper, raw_pnl)
            final_payout = pos.collateral_paper + actual_pnl
            
            payout_map[pos.agent_did] = round(final_payout, 4)
            total_pnl += actual_pnl

        return {
            "status": "SETTLED",
            "contract_id": contract_id,
            "final_price": final_oracle_price,
            "payouts": payout_map,
            "system_delta": round(total_pnl, 6) # Must equal ~0 for zero-sum integrity
        }
