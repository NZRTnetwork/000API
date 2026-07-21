SCRIPT — API-T3 Client Delivery   (agent: cas)

INPUTS (from the ticket ASK):
  soc    the API consumer's Dolibarr thirdparty id
  note   what was delivered (access provisioned, onboarding step, support given)

RUN:    python C:\RPO-SAI\SYS\PLA\WIN\FRA\FAI\ORG\RPO-NZT\OPS\RPO-agt\TSK-bus\record_delivery.py --unit API --soc {soc} --note "{note}"
VERIFY: exit 0 and a final line "RESULT: recorded API delivery on thirdparty {soc}: ...".
CLOSE:  dol_close_ticket note = the RESULT line → [RESOLVED]
ON FAIL: non-zero exit → leave open, paste the ERROR line. 4 = thirdparty not found; 5 = did not persist.
