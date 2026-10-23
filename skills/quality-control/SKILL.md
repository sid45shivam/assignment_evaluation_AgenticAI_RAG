---
name: quality-control
description: Checks one student's proposed evaluation before feedback is written. Runs an automatic script (rubric coverage, score limits, quotes found in the submission, citations, totals, verifier consistency), then a few judgement checks. Use after rubric-evaluation.
metadata:
  author: Siddharth Shivam
  version: "2.0"
---

# Quality Control

## Purpose
Decide whether a proposed evaluation is reliable enough to move on.
Facts are checked by script. Only judgement is checked by you.

## Inputs
- `evaluation_findings/rubric_evaluation_{student_id}.md`
- The student's submission
- `verification_findings/numerical_verification_{student_id}.md` (if numerical)
- `evaluation_findings/submission_analysis_{student_id}.md`
- `references/qc_rules.md` (read it first)

## Steps
1. Run the script (leave out `--numeric-question` if there is no calculation):
   `python skills/quality-control/scripts/qc_checks.py --student {id} --numeric-question Q2`
2. Do the judgement checks listed in `references/qc_rules.md`.
3. Set the result:
   - QC status is FAIL if the script says FAIL or a judgement check fails.
   - Faculty review is required if the script says `escalation_required`
     or you cannot resolve a judgement check.
4. Save the report to `quality_findings/quality_control_{student_id}.md`.
5. If QC status is FAIL, send the issue list back to rubric-evaluation.
   After a second FAIL, escalate to faculty.

## Report
```
# Quality Control: Student {id}

## Script output
<paste the script's JSON in a json code block, unchanged>

## Judgement checks
| Check | Result | Notes |
(the 5 checks from qc_rules.md)

## Result
QC status / Confidence / Faculty review required / Reasons
```

## Guardrails
- Never write PASS for a script check without the script output in the report.
- Do not change marks yourself. Report the problem; rubric-evaluation fixes it.
- Do not hide uncertainty. Do not invent evidence.
- Do not override faculty policy.