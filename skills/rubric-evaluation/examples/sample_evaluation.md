# Example (fictional data)

Fictional rubric: Q2 EOQ. Assignment values: D = 12,000, S = 300, H = 6.
Verifier result: true EOQ = 1095.45. The student wrote 1200.

## Criterion: EOQ result (max 10)
```json
{
  "question_id": "Q2",
  "criterion": "EOQ result",
  "max_marks": 10,
  "proposed_marks": 3,
  "band": "3-5: correct setup, arithmetic error in result",
  "evidence": ["EOQ = 1200 units"],
  "citations": [{"file": "inventory_handout.pdf", "page": 4}],
  "evaluation": "Formula and inputs are correct, but the result differs from the verified 1095.45 by more than the tolerance.",
  "confidence": "HIGH",
  "unresolved_issues": "None"
}
```

## Criterion: Annual ordering cost (max 5), carry-forward applied
The student used their own Q = 1200: (12000/1200) x 300 = 3000.
The method is right and the arithmetic is right for their figure, so this
step keeps method marks. The error is not penalised a second time.
```json
{
  "question_id": "Q2",
  "criterion": "Annual ordering cost",
  "max_marks": 5,
  "proposed_marks": 3,
  "band": "partial: correct method with the student's own Q",
  "evidence": ["(12000/1200) x 300 = 3000"],
  "citations": [{"file": "inventory_handout.pdf", "page": 4}],
  "evaluation": "Correct formula applied to the student's own Q. Value differs from the true-EOQ cost only because of the earlier error.",
  "confidence": "HIGH",
  "unresolved_issues": "None"
}
```

## Criterion: Scalability (max 6), nothing written
```json
{
  "question_id": "Q3",
  "criterion": "Scalability",
  "max_marks": 6,
  "proposed_marks": 0,
  "band": "0: missing",
  "evidence": ["No evidence found"],
  "citations": ["Context Limitation: No specific reference context available in course database"],
  "evaluation": "The answer does not discuss future expansion or flexibility.",
  "confidence": "HIGH",
  "unresolved_issues": "None"
}
```

## What NOT to do
- Wrong: evidence `"Regional warehouses are necessary for fast delivery"` when the
  student never wrote that sentence. Quotes must exist in the submission.
- Wrong: giving 6/6 when the answer only mentions the topic in one line.
- Wrong: citing a source page that was not in the retrieved results.