---
name: feedback-generation
description: Writes short, specific, student-facing feedback from a QC-checked evaluation. Every point is tied to a criterion and to the student's own words. Use after quality-control. Does not state marks.
metadata:
  author: Siddharth Shivam
  version: "2.0"
---

# Feedback Generation

## Purpose
Turn a checked evaluation into feedback a student can act on.

## Inputs
- `quality_findings/quality_control_{student_id}.md`
- `evaluation_findings/rubric_evaluation_{student_id}.md`
- `verification_findings/numerical_verification_{student_id}.md` (if numerical)
- `assets/feedback_template.md`

## Gate (check first)
- QC status FAIL: stop. Write nothing. Report "Blocked: QC failed".
- Faculty review required: write a DRAFT only. Status line:
  `DRAFT: on hold until faculty review`. For the escalated criterion write
  "This part is being reviewed by your faculty." and nothing else about it.
- Otherwise: Status line `Ready for faculty release`.

## Steps
1. Read every criterion block in the evaluation. Group by question.
2. Strengths: up to 3 criteria scored at 80% of max or more.
   Add a short quote of the student's own words (at most 15 words).
3. Improvements: up to 3 criteria with the biggest gap between max and marks.
   Say what is missing, using the `evaluation` text.
4. Numerical answers: use the verification report. Name the first step that
   went wrong. If later steps are `CARRY-FORWARD-PASS`, say the method was
   right and only the earlier figure was wrong.
5. Next steps: one per improvement, starting with a verb. Name a study source
   only if it appears in that criterion's `citations`. Never invent a chapter or page.
6. Fill `assets/feedback_template.md`. Keep the student-facing part under 250 words.
7. Fill the trace table: one row per feedback point (point, criterion, evidence).
8. Save to `feedback/feedback_{student_id}.md`.

## Style
Write to the student ("you"). Be specific and respectful. Plain words.

## Guardrails
- Do not state marks, grades, rank, or comparisons with other students.
- Use only what the evaluation supports. No new strengths or weaknesses.
- Do not contradict the evaluation or a faculty decision.
- Do not release feedback. Faculty releases it.