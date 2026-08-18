import base64
import json
import os
import secrets
import time
from functools import wraps

import requests
from flask import make_response, jsonify, request

FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")
NETWORK = os.getenv("NETWORK", "eip155:84532")
PRICE = os.getenv("PRICE_PER_REQUEST", "$0.001")
EVM_ADDRESS = os.getenv("EVM_ADDRESS", "")

# --- Base mainnet via the Coinbase CDP facilitator ---------------------------------
# The public x402.org facilitator is unauthenticated but testnet-only. Base mainnet
# settlement goes through the CDP facilitator, which (a) authenticates every call with a
# short-lived Ed25519 JWT built from a CDP Secret API Key, and (b) speaks the standard
# x402 *v2* schema. cdp-sdk / x402 both need Python >=3.10 and the server runs 3.8, so
# the JWT and the v2 request bodies are built by hand here. Set CDP_API_KEY_ID +
# CDP_API_KEY_SECRET (and NETWORK=eip155:8453) to enable; unset = unchanged testnet path.
CDP_API_KEY_ID = os.getenv("CDP_API_KEY_ID", "")
CDP_API_KEY_SECRET = os.getenv("CDP_API_KEY_SECRET", "")
CDP_ENABLED = bool(CDP_API_KEY_ID and CDP_API_KEY_SECRET)
_CDP_HOST = "api.cdp.coinbase.com"

if CDP_ENABLED:
    FACILITATOR_URL = f"https://{_CDP_HOST}/platform/v2/x402"

# USDC asset + EIP-712 domain per network (values from the x402 SDK's network config).
_ASSETS = {
    "eip155:8453":  {"address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "name": "USD Coin", "version": "2", "decimals": 6},
    "eip155:84532": {"address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e", "name": "USDC",     "version": "2", "decimals": 6},
}


# HTTP header names differ by x402 version: v2 (CDP) uses bare names, v1 the legacy X- names.
_H_REQUIRED = "PAYMENT-REQUIRED" if CDP_ENABLED else "X-Payment-Required"
_H_PAYMENT = "PAYMENT-SIGNATURE" if CDP_ENABLED else "X-Payment"
_H_RESPONSE = "PAYMENT-RESPONSE" if CDP_ENABLED else "X-Payment-Response"


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _cdp_jwt(method: str, path: str) -> str:
    """Ed25519 (EdDSA) bearer JWT for a CDP REST call — mirrors cdp-sdk get_auth_headers."""
    from cryptography.hazmat.primitives.asymmetric import ed25519
    seed = base64.b64decode(CDP_API_KEY_SECRET)[:32]  # 64-byte key -> 32-byte Ed25519 seed
    key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    now = int(time.time())
    header = {"alg": "EdDSA", "kid": CDP_API_KEY_ID, "typ": "JWT",
              "nonce": "".join(secrets.choice("0123456789") for _ in range(16))}
    claims = {"sub": CDP_API_KEY_ID, "iss": "cdp", "nbf": now, "exp": now + 120,
              "uris": [f"{method} {_CDP_HOST}{path}"]}
    signing_input = _b64url(json.dumps(header, separators=(",", ":")).encode()) + "." + \
        _b64url(json.dumps(claims, separators=(",", ":")).encode())
    return signing_input + "." + _b64url(key.sign(signing_input.encode()))


def _facilitator_headers(op: str) -> dict:
    """Auth headers for a facilitator op ('verify'/'settle'). Empty for the public facilitator."""
    if not CDP_ENABLED:
        return {}
    return {"Authorization": f"Bearer {_cdp_jwt('POST', f'/platform/v2/x402/{op}')}",
            "Content-Type": "application/json"}


def _requirements() -> list:
    """Payment requirements advertised in the 402 'accepts' list."""
    if CDP_ENABLED:
        a = _ASSETS[NETWORK]
        amount = str(round(float(PRICE.lstrip("$")) * (10 ** a["decimals"])))
        return [{
            "scheme": "exact",
            "network": NETWORK,
            "asset": a["address"],
            "amount": amount,
            "payTo": EVM_ADDRESS,
            "maxTimeoutSeconds": 60,
            "extra": {"name": a["name"], "version": a["version"]},
        }]
    # Legacy public-x402.org (testnet) shape — unchanged.
    return [{
        "scheme": "exact",
        "price": PRICE,
        "network": NETWORK,
        "description": "NZRT knowledge vault — Obsidian note content",
        "mimeType": "application/json",
        "payTo": EVM_ADDRESS,
    }]


def _x402_version() -> int:
    return 2 if CDP_ENABLED else 1


def _payment_required():
    payload = {"x402Version": _x402_version(), "accepts": _requirements()}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    resp = make_response(jsonify({"error": "Payment required", "x402Version": _x402_version()}), 402)
    resp.headers[_H_REQUIRED] = encoded
    return resp


def _facilitator_body(payment, reqs) -> dict:
    """Request body for verify/settle. CDP wants the x402 v2 shape; legacy the old shape."""
    if CDP_ENABLED:
        # `payment` is the buyer's decoded X-Payment header (a v2 PaymentPayload).
        return {"x402Version": 2, "paymentPayload": payment, "paymentRequirements": reqs[0]}
    return {"payment": payment, "paymentRequirements": reqs}


def require_payment(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payment_header = request.headers.get(_H_PAYMENT)
        if not payment_header:
            return _payment_required()

        try:
            payment = json.loads(base64.b64decode(payment_header))
        except Exception:
            return _payment_required()

        reqs = _requirements()
        body = _facilitator_body(payment, reqs)

        try:
            verify_resp = requests.post(
                f"{FACILITATOR_URL}/verify",
                json=body,
                headers=_facilitator_headers("verify"),
                timeout=15,
            )
            verify_data = verify_resp.json()
        except Exception as e:
            return make_response(jsonify({"error": f"Facilitator unreachable: {e}"}), 402)

        if not verify_data.get("isValid"):
            return _payment_required()

        result = f(*args, **kwargs)
        if isinstance(result, tuple):
            response = make_response(*result)
        else:
            response = make_response(result)

        try:
            settle_resp = requests.post(
                f"{FACILITATOR_URL}/settle",
                json=body,
                headers=_facilitator_headers("settle"),
                timeout=15,
            )
            encoded = base64.b64encode(json.dumps(settle_resp.json()).encode()).decode()
            response.headers[_H_RESPONSE] = encoded
        except Exception:
            pass

        return response

    return decorated
