r"""
api-pdf-rpt.py — X40-TSK-001. Marketing PDF RPT for the x402 Knowledge Base API.

Renders a local .md (positioning copy) to one PDF in %TEMP%\Marketing and, with --ticket-id,
attaches it to that DOL ticket and deletes the local copy. Publishes nothing.
Markdown handled: # / ## / ### headings, - or * bullets, paragraphs, **bold**.
Self-verifies, prints one RESULT: line. Exit 0 ok / 2 bad args / 3 no key / 5 write or attach failed.

Usage:
    python api-pdf-rpt.py --title "x402 KB API" --content-file positioning.md
    python api-pdf-rpt.py --title "x402 KB API" --content-file positioning.md --ticket-id 725

Credentials from the shared agents .env (DOLIBARR_API_KEY), needed only with --ticket-id.
"""
import argparse
import html
import os
import re
import sys
import tempfile
from datetime import date

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\RPO-SAI\SYS\PLA\WIN\FRA\FAI\ORG\RPO-NZT\OPS\RPO-agt")
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=r"C:\RPO-SAI\SYS\PLA\WIN\FRA\FAI\ORG\RPO-NZT\OPS\RPO-agt\.env")
except Exception:
    pass

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

SHARED_MARKETING = os.path.join(tempfile.gettempdir(), "Marketing")


def fail(msg, code=1):
    print(f"ERROR: {msg}")
    sys.exit(code)


def inline(text):
    text = html.escape(text, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def md_to_flowables(md, title):
    st = getSampleStyleSheet()
    heads = {1: st["Heading1"], 2: st["Heading2"], 3: st["Heading3"]}
    out = [Paragraph(inline(title), st["Title"])]
    bullets, para = [], []

    def flush():
        if para:
            out.append(Paragraph(inline(" ".join(para)), st["BodyText"]))
            para.clear()
        if bullets:
            out.append(ListFlowable([ListItem(Paragraph(inline(b), st["BodyText"])) for b in bullets],
                                    bulletType="bullet", leftIndent=12))
            bullets.clear()

    for line in md.splitlines():
        s = line.strip()
        h = re.match(r"^(#{1,3})\s+(.*)", s)
        b = re.match(r"^[-*]\s+(.*)", s)
        if not s:
            flush()
        elif h:
            flush()
            out.append(Paragraph(inline(h.group(2)), heads[len(h.group(1))]))
        elif b:
            if para:
                flush()
            bullets.append(b.group(1))
        else:
            if bullets:
                flush()
            para.append(s)
    flush()
    out.append(Spacer(1, 6 * mm))
    out.append(Paragraph(f"NZRT Network · X40 · {date.today()}", st["Italic"]))
    return out


def main():
    ap = argparse.ArgumentParser(description="x402 KB API marketing PDF (X40-TSK-001)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--content-file", required=True, help="local .md with the positioning copy")
    ap.add_argument("--ticket-id", type=int, help="DOL ticket id to attach the PDF to")
    args = ap.parse_args()

    if not os.path.isfile(args.content_file):
        fail(f"content file not found: {args.content_file}", 2)
    with open(args.content_file, encoding="utf-8") as f:
        md = f.read()
    if not md.strip():
        fail("content file is empty", 2)

    key = None
    if args.ticket_id:
        key = os.environ.get("DOLIBARR_API_KEY") or os.environ.get("DOL_API_KEY")
        if not key:
            fail("DOLIBARR_API_KEY not set (shared .env)", 3)

    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-") or "x40"
    out = os.path.join(SHARED_MARKETING, f"api-{slug}-{date.today()}.pdf")
    os.makedirs(SHARED_MARKETING, exist_ok=True)
    doc = SimpleDocTemplate(out, pagesize=A4, title=args.title, author="NZRT Network",
                            leftMargin=20 * mm, rightMargin=20 * mm, topMargin=20 * mm, bottomMargin=20 * mm)
    try:
        doc.build(md_to_flowables(md, args.title))
    except Exception as e:
        fail(f"PDF build failed: {e}", 5)

    with open(out, "rb") as f:
        if f.read(5) != b"%PDF-":
            fail(f"report not a PDF: {out}", 5)

    where = f"file={out}"
    if args.ticket_id:
        from ITG.dol_ema import dol_attach_file
        res = dol_attach_file(key, "ticket", args.ticket_id, out)
        if res.get("status") != "ok":
            fail(f"attach to ticket {args.ticket_id} failed: {res.get('error')}", 5)
        os.remove(out)
        where = f"file={os.path.basename(out)} ticket={args.ticket_id}"

    print(f"RESULT: API marketing PDF saved pages={doc.page} {where}")


if __name__ == "__main__":
    main()
