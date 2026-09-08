import json
from typing import Dict, Any

class TASEMCPAdapter:
    """
    Exposes TASE Settlement Layer as Native Tools to LLM Agents via MCP Protocol.
    """
    def __init__(self, verifier_instance, settlement_instance):
        self.verifier = verifier_instance
        self.settlement = settlement_instance

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "tase_submit_proof_and_settle",
                "description": "Submits cryptographic Ed25519 proof to settle an open Technocore Escrow contract.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "raw_payload": {"type": "string", "description": "Raw JSON payload from Technocore room."},
                        "contract_id": {"type": "string", "description": "Target settlement contract ID."},
                        "settlement_price": {"type": "number", "description": "Verified consensus value."}
                    },
                    "required": ["raw_payload", "contract_id", "settlement_price"]
                }
            }
        ]

    def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "tase_submit_proof_and_settle":
            valid, body, err_code = self.verifier.parse_and_verify(arguments["raw_payload"])
            if not valid:
                return {"success": False, "error": f"Verification failed: {err_code}"}

            settlement_result = self.settlement.calculate_settlement(
                contract_id=arguments["contract_id"],
                final_oracle_price=arguments["settlement_price"]
            )
            return {"success": True, "data": settlement_result}

        return {"success": False, "error": "UNKNOWN_MCP_TOOL"}
