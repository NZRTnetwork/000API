import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'), override=True)
from flask import Flask, jsonify, request, send_from_directory
from vault import read_note, search_vault
from x402_middleware import require_payment, NETWORK, PRICE, FACILITATOR_URL, EVM_ADDRESS

app = Flask(__name__)

DOMAIN_MAP = {
    "ncl": "NextCloud",
    "dol": "Dolibarr",
    "wor": "Wordpress",
    "git": "Github",
    "inf": "Infrastructure",
    "bch": "Blockchain",
    "k8s": "Kubernetes",
}

TOGAF_PHASES = {
    "1": "01 - Preliminary Phase",
    "2": "02 - Architecture Vision",
    "3": "03 - Business Architecture",
    "4": "04 - Information Systems",
    "5": "05 - Technology Architecture",
    "6": "06 - Opportunities & Solutions",
    "7": "07 - Migration Planning",
    "8": "08 - Implementation Governance",
    "9": "09 - Requirements Management",
    "11": "11 - NZRT Architecture",
    "catalogs": "Catalogs_Matricies_Diagrams",
}


@app.get("/")
def landing():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "network": NETWORK,
        "price": PRICE,
        "facilitator": FACILITATOR_URL,
        "domains": list(DOMAIN_MAP.keys()) + ["wiki", "togaf"],
        "endpoints": [
            "GET /health (free)",
            "GET /wiki/search?q=... (paid)",
            "GET /wiki/note?section=...&file=... (paid)",
            "GET /togaf/search?q=... (paid)",
            "GET /togaf/phase?n=2&doc=Architecture+Vision (paid)",
            "GET /<domain>/search?q=... (paid) — domains: " + ", ".join(DOMAIN_MAP.keys()),
            "GET /<domain>/note?section=...&file=... (paid)",
        ],
    })


@app.get("/wiki/search")
@require_payment
def wiki_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query param: q"}), 400
    results = search_vault(q)
    return jsonify({"query": q, "results": results})


@app.get("/wiki/note")
@require_payment
def wiki_note():
    section = request.args.get("section", "").strip()
    file = request.args.get("file", "").strip()
    if not section or not file:
        return jsonify({"error": "Missing params: section, file"}), 400
    try:
        content = read_note(section, file)
        return jsonify({"section": section, "file": file, "content": content})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.get("/togaf/search")
@require_payment
def togaf_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query param: q"}), 400
    results = search_vault(q, subfolder="togaf")
    return jsonify({"query": q, "results": results})


@app.get("/togaf/phase")
@require_payment
def togaf_phase():
    n = request.args.get("n", "").strip()
    doc = request.args.get("doc", "").strip()
    if not n:
        return jsonify({"error": "Missing param: n"}), 400
    if not doc:
        return jsonify({"error": "Missing param: doc"}), 400
    folder = TOGAF_PHASES.get(n)
    if not folder:
        return jsonify({"error": f"Unknown phase: {n}"}), 400
    try:
        content = read_note(f"togaf/{folder}", doc)
        return jsonify({"phase": n, "folder": folder, "doc": doc, "content": content})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.get("/<domain>/search")
@require_payment
def domain_search(domain):
    if domain not in DOMAIN_MAP:
        return jsonify({"error": f"Unknown domain: {domain}"}), 404
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query param: q"}), 400
    results = search_vault(q, subfolder=DOMAIN_MAP[domain])
    return jsonify({"domain": domain, "query": q, "results": results})


@app.get("/<domain>/note")
@require_payment
def domain_note(domain):
    if domain not in DOMAIN_MAP:
        return jsonify({"error": f"Unknown domain: {domain}"}), 404
    section = request.args.get("section", "").strip()
    file = request.args.get("file", "").strip()
    if not section or not file:
        return jsonify({"error": "Missing params: section, file"}), 400
    try:
        content = read_note(os.path.join(DOMAIN_MAP[domain], section), file)
        return jsonify({"domain": domain, "section": section, "file": file, "content": content})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
