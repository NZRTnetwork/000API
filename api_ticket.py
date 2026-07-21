"""
create_api_ticket.py — create an x402 API task ticket assigned to dan.
Hardcoded: type=000API, category=DAN, project=24, tag=51.

Usage: python create_api_ticket.py --subject "Add /knowledge endpoint for AI agents" [--message "..."] [--tag-id N]
Auth: set DOLIBARR_API_KEY env var (xc Dolibarr API key)
"""
import argparse
import os
import sys
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"C:\RPO-SAI\SYS\PLA\WIN\FRA\FAI\ORG\RPO-NZT\OPS\RPO-agt\SET\create_agents\.env")

DOL_HELPER_URL    = "https://nzrtnetwork.com/dol-sql-helper/"
DOL_HELPER_SECRET = "nzrt_f7a2c849e3d561b0"
DOL_BASE = "https://erp.nzrtnetwork.com/dolibarr/api/index.php"
DOL_WEB  = "https://erp.nzrtnetwork.com/dolibarr"

DAN_USER_ID  = 10
API_PROJECT  = 24


def dol_helper(op, **kwargs):
    payload = {"token": DOL_HELPER_SECRET, "op": op, **kwargs}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(DOL_HELPER_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"dol-sql-helper {op} failed {e.code}: {e.read().decode()}")


def api(method, endpoint, data=None, api_key=None):
    url = f"{DOL_BASE}/{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("DOLAPIKEY", api_key)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"API error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create an x402 API task ticket for dan")
    parser.add_argument("--subject", required=True, help="Ticket subject")
    parser.add_argument("--message", default="", help="Ticket body (optional)")
    parser.add_argument("--tag-id", type=int, default=51, help="Tag with llx_categorie rowid (default: 51 = 000API)")
    parser.add_argument("--soc-id", type=int, default=None, help="Link third party by socid (34=Association Dolibarr)")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without creating")
    args = parser.parse_args()

    api_key = os.environ.get("DOLIBARR_API_KEY") or os.environ.get("DOL_API_KEY")
    if not api_key:
        print("Error: set DOLIBARR_API_KEY env var", file=sys.stderr)
        sys.exit(1)

    message = args.message or args.subject

    ticket = {
        "subject":              args.subject,
        "type_code":            "000API",
        "category_code":        "DAN",
        "fk_user_assign":       DAN_USER_ID,
        "severity_code":        "NORMAL",
        "message":              message,
        "notify_tiers_at_create": 0,
    }
    if args.soc_id:
        ticket["fk_soc"] = args.soc_id

    if args.dry_run:
        print("DRY RUN — payload:")
        print(json.dumps(ticket, indent=2))
        print(f"  Would link to project {API_PROJECT}")
        return

    result    = api("POST", "tickets", ticket, api_key)
    ticket_id = result if isinstance(result, (int, str)) else result.get("id", result)
    print(f"Ticket created: ID={ticket_id}")
    print(f"  Subject:     {args.subject}")
    print(f"  Assigned to: dan (user ID {DAN_USER_ID}) — x402 API")
    if args.soc_id:
        print(f"  fk_soc = {args.soc_id}")
    print(f"  View: {DOL_WEB}/ticket/card.php?id={ticket_id}")

    res = dol_helper("link_ticket_project", ticket_id=int(ticket_id), project_id=API_PROJECT)
    print(f"  project {API_PROJECT} {'linked OK' if res.get('ok') else 'link ERROR: ' + str(res)}")

    if args.tag_id:
        res = dol_helper("tag_ticket_categorie", ticket_id=int(ticket_id), categorie_id=args.tag_id)
        print(f"  tag {args.tag_id} {'applied OK' if res.get('ok') else 'tag ERROR: ' + str(res)}")


if __name__ == "__main__":
    main()
