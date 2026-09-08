import base64
import json
import time
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

class TechnocoreProofVerifier:
    """
    Validates incoming Ed25519 signed payloads from Technocore public rooms.
    Prevents replay attacks via strictly monotonically increasing nonces.
    """
    def __init__(self, max_clock_skew_seconds: int = 300):
        self.max_skew = max_clock_skew_seconds
        self.seen_nonces: Dict[str, float] = {}

    def parse_and_verify(self, raw_message: str) -> Tuple[bool, Dict[str, Any], str]:
        try:
            payload = json.loads(raw_message)
            header = payload.get("header", {})
            body = payload.get("body", {})
            signature_hex = payload.get("signature")

            if not all([header, body, signature_hex]):
                return False, {}, "ERR_INVALID_FRAME_STRUCTURE"

            # 1. Replay & Timestamp Check
            timestamp = header.get("timestamp", 0)
            nonce = header.get("nonce")
            sender_did = header.get("sender_did")

            if abs(time.time() - timestamp) > self.max_skew:
                return False, {}, "ERR_CLOCK_SKEW_EXCEEDED"

            nonce_key = f"{sender_did}:{nonce}"
            if nonce_key in self.seen_nonces:
                return False, {}, "ERR_REPLAY_ATTACK_DETECTED"
            
            self.seen_nonces[nonce_key] = time.time()

            # 2. Extract Public Key from DID
            # DID Format: did:technocore:ed25519:<hex_pubkey>
            pubkey_hex = sender_did.split(":")[-1]
            pubkey_bytes = bytes.fromhex(pubkey_hex)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pubkey_bytes)

            # 3. Canonicalize Body & Verify Signature
            canonical_body = json.dumps(body, sort_keys=True, separators=(',', ':')).encode('utf-8')
            signature_bytes = bytes.fromhex(signature_hex)

            public_key.verify(signature_bytes, canonical_body)
            return True, body, "OK_VERIFIED"

        except InvalidSignature:
            return False, {}, "ERR_CRYPTOGRAPHIC_SIGNATURE_INVALID"
        except Exception as e:
            return False, {}, f"ERR_INTERNAL_VERIFICATION_FAILURE: {str(e)}"
