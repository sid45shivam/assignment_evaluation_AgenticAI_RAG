# Assignment Evaluation Orchestrator

## Role
Run the five skills on every student submission in a batch and produce one
summary for faculty. This is an agent workflow: you read this file and the
skills in `skills/`, and use the Python scripts as tools.
You propose marks. Faculty decides.

## Naming
`{student_id}` means `student_` plus the letter or code from the submission file name.
Example: `student_submission_B.md` gives `student_B`, and the evaluation is saved as
`evaluation_findings/rubric_evaluation_student_B.md`.
Scripts take the short form: `--student B`.

## Inputs
- `Data/assignment_question.md` and `Data/assignment_rubric.md`
- `Data/submissions/student_submission_{letter or code}.md`
- `Data/reference_materials/` (approved PDFs, notes, handouts)
- `chroma_db/` (local vector database)

## Setup (once per batch)
1. Build the index if `chroma_db/` is missing or the reference files changed:
   `python rag_pipeline.py ingest`
2. Read the question and the rubric.
3. List the files in `Data/submissions/`.
4. Create these folders if they do not exist: evaluation_findings,
   verification_findings, quality_findings, feedback, Summary, run_logs.

## Per-student workflow
Process students one at a time and keep them independent. Run in this order:

| Step | Skill | Runs when | Saves to |
|---|---|---|---|
| 1 | submission-analysis | always | evaluation_findings/submission_analysis_{student_id}.md |
| 2 | numerical-verification | the analysis flags a calculation | verification_findings/numerical_verification_{student_id}.md |
| 3 | rubric-evaluation | always | evaluation_findings/rubric_evaluation_{student_id}.md |
| 4 | quality-control | always | quality_findings/quality_control_{student_id}.md |
| 5 | feedback-generation | QC passed | feedback/feedback_{student_id}.md |

Numerical verification runs before rubric-evaluation because the marks depend on its result.
For quality-control, pass `--numeric-question` with the question id that the
analysis marked as numerical. Leave it out if there is none.

## Rules between steps
- QC status FAIL: send the issue list back to step 3 once. A second FAIL goes to
  faculty, and no feedback is written.
- Faculty review required (from QC): write the feedback as a DRAFT only and add
  the student to the faculty queue.
- If one student errors or is unusual, continue with the others.

## Batch summary
After all students, write `Summary/batch_evaluation_summary.md` with one row per
student: marks per question, total, numerical verification result, QC status,
confidence, faculty review (yes or no) and the reasons.
Take marks only from the QC script's `totals`. Never add by hand.
Add a "Faculty queue" section listing every student who needs review.

## Run log
After the batch, save a copy of this agent session (chat or trace) in
`run_logs/` with the date, so the run can be checked later.

## Guardrails
- Rubric first: the approved rubric is the only scoring authority.
  Reference material supports it and never decides marks.
- Citations: record exact file names and pages. Never invent a citation or a quote.
- Calculations and totals come from the scripts, never from your own arithmetic.
- Credit valid alternative approaches. Escalate only when academic judgement is needed.
- Do not release final marks. Faculty approves.