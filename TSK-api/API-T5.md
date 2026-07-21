SCRIPT — API-T5 Product and pricing packaging   (agent: pam)

Defines the x402 API access packages and per-query pricing as Dolibarr products.

INPUTS (from the ticket ASK):
  action    list | create | update
  create:   ref, label, price   |   update: id, price and/or label

RUN:    python C:\RPO-SAI\SYS\PLA\WIN\FRA\FAI\ORG\RPO-NZT\WIK\RPO-app\RPO-dol\TSK-dol\product_catalog.py --action {action} [args]
VERIFY: exit 0 and a final line "RESULT: ...".
CLOSE:  dol_close_ticket note = the RESULT line → [RESOLVED]
ON FAIL: non-zero exit → leave open, paste the ERROR line. 2 = missing args; 5 = write failed.
