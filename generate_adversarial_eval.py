"""
generate_adversarial_eval.py — create a separate adversarial eval set to
stress-test the workflow.py mock extractor.

This script generates edge cases that the canonical eval_set.json may
not cover:
- Ambiguous dates (e.g. 03/04/2025 — is it March 4 or April 3?)
- Multiple vendor candidates (e.g. "Bill to: ACME / Vendor: Globex")
- Multiple total amounts (e.g. subtotal + tax + total)
- Mixed currency aliases
- Whitespace + HTML + unicode normalization

Per autoresearch-sboss/AGENTS.md §2, we do NOT modify eval_set.json
(canonical, frozen). Instead, we generate a separate eval_set_v2.json
and run eval against it. The workflow.py (the lever) is unchanged.

Run: python3 generate_adversarial_eval.py
Then: python3 eval.py --eval-set eval_set_v2.json
"""

import json
import random
from pathlib import Path

random.seed(42)

ADVERSARIAL_CASES = [
    # 1. Date ambiguity (slash format, no other context)
    {
        "input": {"document": "Bill #1\nDate: 03/04/2025\nTotal: $500"},
        "expected": {"vendor_name": "Bill #1", "invoice_date": "2025-04-03",
                     "total_amount": 500, "currency": "USD", "tax_id": None},
        "rationale": "Day-first per US convention (no Russian/Armenian/EUR cues)",
    },
    # 2. Multiple vendors — should pick the actual one, not the bill-to
    {
        "input": {"document": "Globex Industries\nBill to: Initech\nInvoice #42\nTotal: $1,000"},
        "expected": {"vendor_name": "Globex Industries", "invoice_date": None,
                     "total_amount": 1000, "currency": "USD", "tax_id": None},
        "rationale": "First non-cue company line wins; 'Bill to' is a skip prefix",
    },
    # 3. Subtotal + tax + total — should pick the LARGEST (or 'Total:' not 'Subtotal:')
    {
        "input": {"document": "ACME Corp\nSubtotal: $1,000\nTax (10%): $100\nTotal: $1,100"},
        "expected": {"vendor_name": "ACME Corp", "invoice_date": None,
                     "total_amount": 1100, "currency": "USD", "tax_id": None},
        "rationale": "Must skip 'Subtotal' and 'Tax' lines, pick 'Total:' line",
    },
    # 4. Russian with spaces in number (1 234,50 rub.)
    {
        "input": {"document": "ООО ТехноСтрой\nСчёт № 100\nот 15 марта 2025\nИтого: 1 234,50 руб."},
        "expected": {"vendor_name": "ООО ТехноСтрой", "invoice_date": "2025-03-15",
                     "total_amount": 1234.50, "currency": "RUB", "tax_id": None},
        "rationale": "1 234,50 → 1234.50 (space stripped, comma = decimal in ru)",
    },
    # 5. Armenian with ֏ symbol
    {
        "input": {"document": "ՀայՀաշվապահ ՓԲԸ\nՀաշիվ № 5\n15 մարտի 2025\nԸնդամենը: 50,000 ֏"},
        "expected": {"vendor_name": "ՀայՀաշվապահ ՓԲԸ", "invoice_date": "2025-03-15",
                     "total_amount": 50000, "currency": "AMD", "tax_id": None},
        "rationale": "15 մարտի 2025 = 15 March 2025, ֏ = AMD, 50,000 (no decimal)",
    },
    # 6. Date with 2-digit year (03/15/25)
    {
        "input": {"document": "Test Corp\nDate: 03/15/25\nTotal: $999"},
        "expected": {"vendor_name": "Test Corp", "invoice_date": "2025-03-15",
                     "total_amount": 999, "currency": "USD", "tax_id": None},
        "rationale": "2-digit year → assume 20xx (per _RE_DATE_SLASH handler)",
    },
    # 7. Tax ID with no separator (German VAT)
    {
        "input": {"document": "Test GmbH\nVAT: DE987654321\nTotal: EUR 500"},
        "expected": {"vendor_name": "Test GmbH", "invoice_date": None,
                     "total_amount": 500, "currency": "EUR", "tax_id": "DE987654321"},
        "rationale": "VAT: prefix matches _RE_TAX_ID, DE+9 digits = German VAT",
    },
    # 8. Ambiguous amount: $1000 in text body AND in Total: line
    {
        "input": {"document": "ACME\nDescription: $1000 services\nTotal: $1000"},
        "expected": {"vendor_name": "ACME", "invoice_date": None,
                     "total_amount": 1000, "currency": "USD", "tax_id": None},
        "rationale": "Total: line wins over Description line",
    },
    # 9. Negative test: garbage input
    {
        "input": {"document": ""},
        "expected": {"vendor_name": None, "invoice_date": None,
                     "total_amount": None, "currency": None, "tax_id": None},
        "rationale": "Empty input → all None (defensive default)",
    },
    # 10. Multiple currencies (EUR in body, USD in total)
    {
        "input": {"document": "ACME\nInvoice: 2025-01-15\nSubtotal: EUR 1,000\nTotal: USD 1,100"},
        "expected": {"vendor_name": "ACME", "invoice_date": "2025-01-15",
                     "total_amount": 1100, "currency": "USD", "tax_id": None},
        "rationale": "Currency follows the selected total (USD in this case)",
    },
]


def main():
    out_path = Path(__file__).parent / "eval_set_v2.json"
    out_path.write_text(json.dumps(ADVERSARIAL_CASES, indent=2, ensure_ascii=False))
    print(f"Wrote {len(ADVERSARIAL_CASES)} adversarial cases to {out_path}")
    print("Run with: python3 eval.py --eval-set eval_set_v2.json")


if __name__ == "__main__":
    main()