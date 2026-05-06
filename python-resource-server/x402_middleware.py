import base64
import json
import os
from functools import wraps

import requests
from flask import make_response, jsonify, request

FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")
NETWORK = os.getenv("NETWORK", "eip155:84532")
PRICE = os.getenv("PRICE_PER_REQUEST", "$0.001")
EVM_ADDRESS = os.getenv("EVM_ADDRESS", "")


def _requirements() -> list:
    return [{
        "scheme": "exact",
        "price": PRICE,
        "network": NETWORK,
        "description": "NZRT knowledge vault — Obsidian note content",
        "mimeType": "application/json",
        "payTo": EVM_ADDRESS,
    }]


def _payment_required():
    payload = {"x402Version": 1, "accepts": _requirements()}
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    resp = make_response(jsonify({"error": "Payment required", "x402Version": 1}), 402)
    resp.headers["X-Payment-Required"] = encoded
    return resp


def require_payment(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payment_header = request.headers.get("X-Payment")
        if not payment_header:
            return _payment_required()

        try:
            payment = json.loads(base64.b64decode(payment_header))
        except Exception:
            return _payment_required()

        reqs = _requirements()

        try:
            verify_resp = requests.post(
                f"{FACILITATOR_URL}/verify",
                json={"payment": payment, "paymentRequirements": reqs},
                timeout=10,
            )
            verify_data = verify_resp.json()
        except Exception as e:
            resp = make_response(jsonify({"error": f"Facilitator unreachable: {e}"}), 402)
            return resp

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
                json={"payment": payment, "paymentRequirements": reqs},
                timeout=10,
            )
            encoded = base64.b64encode(json.dumps(settle_resp.json()).encode()).decode()
            response.headers["X-Payment-Response"] = encoded
        except Exception:
            pass

        return response

    return decorated
