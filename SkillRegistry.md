# Skill Registry

| Skill | What it does | Tools | Output |
|---|---|---|---|
| submission-analysis | Maps answers to questions, classifies them, copies calculation inputs exactly | none | evaluation_findings/submission_analysis_{student_id}.md |
| numerical-verification | Checks calculations step by step, separates new errors from carried-forward ones | scripts/numerical_verifier.py | verification_findings/numerical_verification_{student_id}.md |
| rubric-evaluation | Scores each criterion with exact quotes and citations | rag_pipeline.py query, score_calculator.py, consistency_checker.py | evaluation_findings/rubric_evaluation_{student_id}.md |
| quality-control | Automatic checks, then judgement checks, then escalation decision | scripts/qc_checks.py | quality_findings/quality_control_{student_id}.md |
| feedback-generation | Student-facing feedback with no marks | none | feedback/feedback_{student_id}.md |

## Order
submission-analysis -> numerical-verification (if calculations) -> rubric-evaluation
-> quality-control -> feedback-generation

```text
Reference PDFs -> rag_pipeline.py ingest -> chroma_db
                                              |
Submission -> [1 analysis] -> [2 verification] -> [3 rubric evaluation] <- retrieval
                                                          |
                                                   [4 quality control]
                                                    |             |
                                               PASS / review    FAIL -> back to step 3 (once),
                                                    |                   then faculty
                                              [5 feedback]
                                                    |
                                         Summary/batch_evaluation_summary.md
```

## Code
- `rag_pipeline.py`: `ingest` and `query` commands
- `skills/numerical-verification/scripts/`: numerical_verifier.py, score_calculator.py, consistency_checker.py
- `skills/quality-control/scripts/`: qc_checks.py

## Tests
```
python test_rag.py
python skills/numerical-verification/scripts/test_numerical_verifier.py
python skills/quality-control/scripts/test_qc_checks.py
```
`test_rag.py` needs internet the first time, to download the embedding model.