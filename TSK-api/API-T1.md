SCRIPT — API-T1 Marketing and promotion   (agent: pam)

Positions the x402 knowledge-base endpoint and its access packages to developer/commercial
audiences. Pre-launch: this drafts to the Marketing folder for xc — it publishes nothing.

INPUTS (from the ticket ASK):
  title         the piece's working title
  content-file  local .md with the positioning copy

RUN:    python C:\RPO-SAI\SYS\PLA\WIN\FRA\FAI\ORG\RPO-NZT\OPS\RPO-agt\TSK-bus\marketing_draft.py --unit API --title "{title}" --content-file {file}
VERIFY: exit 0 and a final line "RESULT: API marketing draft saved file=...".
CLOSE:  dol_close_ticket note = the RESULT line → [RESOLVED]
ON FAIL: non-zero exit → leave open, paste the ERROR line.
