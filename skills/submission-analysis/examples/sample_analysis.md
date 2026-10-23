# Example: Student B

```json
{
  "student_id": "B",
  "source_file": "student_submission_B.md",
  "questions": [
    {
      "question_id": "Q1",
      "status": "answered",
      "answer_type": "theoretical",
      "numerical_verification_required": false,
      "ambiguity_flags": []
    },
    {
      "question_id": "Q2",
      "status": "answered",
      "answer_type": "numerical",
      "numerical_verification_required": true,
      "extracted_calculation": {
        "calc": "EOQ",
        "inputs": {"D": 10000, "S": 500, "H": 20},
        "student_results": {
          "EOQ": 500,
          "annual_ordering_cost": 10000,
          "annual_holding_cost": 5000,
          "total_cost": 15000
        }
      },
      "ambiguity_flags": []
    },
    {
      "question_id": "Q3",
      "status": "answered",
      "answer_type": "case-based",
      "numerical_verification_required": false,
      "ambiguity_flags": []
    }
  ],
  "recommended_next_action": "Run numerical-verification for Q2, then rubric-evaluation"
}
```

# Example flag: Student C, Q3

```json
{
  "question_id": "Q3",
  "status": "answered",
  "answer_type": "case-based",
  "numerical_verification_required": false,
  "ambiguity_flags": [
    {
      "issue": "Recommends a hybrid network instead of Option A or B",
      "quote": "Instead, I recommend a hybrid network."
    }
  ]
}
```