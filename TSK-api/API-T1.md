SCRIPT — API-T1 Marketing and promotion   (agent: pam)

Positions the x402 knowledge-base endpoint and its access packages to developer/commercial
audiences. Pre-launch: this renders a marketing PDF for xc and attaches it to the TIC — it publishes nothing.

INPUTS (from the ticket ASK):
  title         the piece's working title
  content-file  local .md with the positioning copy

RUN:    python C:\RPO-SAI\SYS\PLA\WIN\FRA\FAI\ORG\RPO-NZT\WIK\RPO-app\RPO-api\TSK-api\api-pdf-rpt.py --title "{title}" --content-file {file} --ticket-id {ticket-id}
VERIFY: exit 0 and a final line "RESULT: API marketing PDF saved pages=N file=... ticket=...".
CLOSE:  dol_close_ticket note = the RESULT line → [RESOLVED]
ON FAIL: non-zero exit → leave open, paste the ERROR line. 2 = bad content file; 3 = no DOLIBARR_API_KEY; 5 = PDF or attach failed.
