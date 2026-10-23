---
name: rubric-evaluation
description: Scores one student's answers against the approved rubric, criterion by criterion, using exact quotes from the submission as evidence and retrieved course material as supporting citations. Use after submission-analysis, and after numerical-verification for numerical questions.
metadata:
  author: Siddharth Shivam
  version: "2.0"
---

# Rubric Evaluation

## Purpose
Propose marks for each rubric criterion, with evidence and citations.
Marks are proposals only. Faculty gives final approval.

## Inputs
- Submission analysis for the student (`evaluation_findings/submission_analysis_{student_id}.md`)
- The student's submission
- Assignment question and rubric (`Data/assignment_question.md`, `Data/assignment_rubric.md`)
- Numerical verification result, for numerical questions
- Scoring rules: `references/scoring_policy.md` (read it first)

## Steps
For every criterion in the rubric:
1. Retrieve reference context for this criterion:
   `python rag_pipeline.py query "<criterion text>" --top-k 4`
   Keep the filename and page of each chunk returned.
2. Find evidence in the student's answer. Copy it exactly.
   If there is none, write `No evidence found`.
3. Choose the rubric band that matches the evidence, then a mark inside that band.
4. For numerical criteria, use the verification result and the
   carry-forward rule in `references/scoring_policy.md`.
5. Write a short evaluation (1 to 2 sentences) and a confidence level.
6. Add citations only from the chunks retrieved in step 1.
7. Compute totals with `calculate_total_score` and check them with
   `check_score_consistency` (numerical-verification/scripts). Never add by hand.
8. Save to `evaluation_findings/rubric_evaluation_{student_id}.md`.

## Output
Write each criterion as its own ```json block with exactly these fields:
`question_id` (like "Q2"), `criterion` (copy the rubric heading text without the marks),
`max_marks`, `proposed_marks`, `band`, `evidence` (a list), `citations`
(a list of {"file", "page"}, or a "Context Limitation: ..." string),
`evaluation`, `confidence`, `unresolved_issues`.

## Guardrails
- Every mark above 0 needs at least one exact quote from the submission.
- Never write a quote, citation or fact that you did not read in a file.
- Reference material supports scoring. It never gives or removes marks.
- Do not change the rubric, its bands or its maximum marks.
- Do not release final marks. Faculty approves.