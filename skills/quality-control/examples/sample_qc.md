# Example 1: PASS with a review note (fictional data)

## Script output
```json
{
  "qc_status": "PASS",
  "checks": [
    {"check": "Rubric coverage", "status": "PASS", "issues": []},
    {"check": "Evidence found in submission", "status": "PASS", "issues": []}
  ],
  "totals": {"by_question": {"Q1": 9, "Q2": 3}, "total": 12},
  "confidence": "MEDIUM",
  "escalation_required": false,
  "escalation_reasons": [],
  "review_notes": ["Q1 Example: MEDIUM confidence"]
}
```
(The real output lists all 6 checks.)

## Judgement checks
| Check | Result | Notes |
|---|---|---|
| Band fit | PASS | Q1 Example 4/5 matches the 3-4 band: example given, no operational detail |
| Citation support | PASS | inventory_handout.pdf p4 contains the EOQ example cited |
| Conflicting evidence | PASS | None |
| Carry-forward | PASS | Ordering and holding cost not penalised twice |
| Unsupported assumptions | PASS | None |

## Result
QC status: PASS. Confidence: MEDIUM. Faculty review required: No.

---

# Example 2: FAIL (fictional data)

```json
{
  "qc_status": "FAIL",
  "checks": [
    {"check": "Evidence found in submission", "status": "FAIL",
     "issues": ["Q1 Definition: quote not found in submission: \"Responsiveness means fast delivery to every customer worldwide\""]}
  ],
  "escalation_required": true,
  "escalation_reasons": ["QC failed: Evidence found in submission"]
}
```
Action: the quote does not exist in the submission. Return to
rubric-evaluation with this issue. Do not generate feedback.