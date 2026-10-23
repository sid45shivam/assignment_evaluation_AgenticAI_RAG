---
name: numerical-verification
description: Independently checks a student's calculations with a deterministic Python script, step by step, and reports whether each error is new or carried forward from an earlier step. Use when submission-analysis flags a numerical answer. Run before rubric-evaluation.
metadata:
  author: Siddharth Shivam
  version: "2.0"
---

# Numerical Verification

## Purpose
Check student calculations with code, not with LLM arithmetic.
The script output is the source of truth.

## Inputs
- `extracted_calculation` from submission-analysis (inputs and student results)
- `references/supported_calculations.md` (which calculations have scripts)

## Steps
1. Read `extracted_calculation`. If there is none, stop. Nothing to verify.
2. Look up the calculation in `references/supported_calculations.md`.
   If there is no script, write `UNVERIFIED` and escalate to faculty.
3. Run the script with the student's numbers copied exactly. Example:
   `python skills/numerical-verification/scripts/numerical_verifier.py eoq --D 10000 --S 500 --H 20 --eoq 500 --ordering 10000 --holding 5000 --total 15000`
   Leave out a flag if the student did not calculate that step.
4. Paste the script's JSON output into the report unchanged.
5. Fill the summary table (see Report) from that JSON only.
6. Save to `verification_findings/numerical_verification_{student_id}.md`.

## Status meanings
- `PASS`: matches the verified value (within 0.5%).
- `CARRY-FORWARD-PASS`: differs from the verified value, but is correct for
  the student's own earlier figure. The error is not new.
- `FAIL`: wrong, and not explained by an earlier figure. This is a new error.
- `NOT PROVIDED`: the student did not calculate this step.
- `UNVERIFIED`: no script exists for this calculation.

## Report
```
# Numerical Verification: Student {id}
Command run: `<the exact command>`

## Script output
<paste JSON in a json code block>

## Summary
| Step | Student | Verified | Status | Severity | Impact on marking |
```
Impact on marking, by status:
- PASS: full credit is possible.
- CARRY-FORWARD-PASS: method marks apply (scoring_policy.md, section 4).
- FAIL: this step loses marks.
- NOT PROVIDED: no evidence for this step.

## Guardrails
- Never calculate anything yourself. Use the script output only.
- Do not fix or round the student's numbers. Pass them exactly as written.
- Do not invent missing inputs. Leave the flag out.
- Do not change the rubric or propose marks. That is rubric-evaluation's job.
- If the script fails or gives unexpected output, escalate. Do not estimate.