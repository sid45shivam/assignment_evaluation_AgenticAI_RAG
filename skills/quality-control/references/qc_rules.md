# QC Rules

## 1. Automatic checks (qc_checks.py)
| Check | FAIL when |
|---|---|
| Rubric coverage | a rubric criterion is missing, duplicated, or not in the rubric |
| Score limits and rubric maximums | marks below 0 or above max, or max_marks differs from the rubric |
| Evidence found in submission | marks above 0 with no quote, or a quote that is not in the submission |
| Citations | no citation, cited file not in the reference folder, or page outside the PDF |
| Question totals | a question total is above its maximum |
| Numerical verification consistency | the verifier found errors but the numerical question has full marks |

The script cannot tell whether a cited page really supports a claim, or whether
a mark fits its band. Those are the judgement checks below.

## 2. Judgement checks (you)
1. Band fit: does each mark sit in the band the quoted evidence supports?
   Check the 3 highest and the 3 lowest criteria.
2. Citation support: open each cited chunk. Does it actually say what the evaluation claims?
3. Conflicting evidence: is one quote used for opposite conclusions, or does an evaluation contradict the verifier?
4. Carry-forward: does the numerical question follow `rubric-evaluation/references/scoring_policy.md`, section 4 (no double penalty)?
5. Unsupported assumptions: does the evaluation credit something the student did not write?

## 3. Confidence
Overall confidence is the lowest confidence of any criterion.
- HIGH: evidence and rubric clearly support the marks.
- MEDIUM: band edge, valid alternative approach, or some uncertainty.
- LOW: significant academic judgement is needed.

## 4. Escalation
Faculty review is required when:
- QC fails twice,
- any criterion has LOW confidence,
- any unresolved issue is not "None",
- the verification is UNVERIFIED,
- you cannot resolve a judgement check.

Review is recommended, not required, for MEDIUM confidence, analysis ambiguity
flags, or a credited alternative approach. If the assignment allows alternative
answers, crediting a valid one is not an escalation by itself.