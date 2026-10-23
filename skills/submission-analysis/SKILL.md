---
name: submission-analysis
description: Reads one student submission, maps each answer to the assignment questions, classifies the answer type, copies calculation inputs and results exactly as written, and flags missing or unusual answers. Use first for every submission, before rubric evaluation.
metadata:
  author: Siddharth Shivam
  version: "1.1"
---

# Submission Analysis

## Purpose
Turn a raw student submission into a structured summary for the next skills.
This skill only reads and organizes. It does not judge quality.

## Inputs
- Student submission (for example `Data/submissions/student_submission_B.md`)
- Assignment question (`Data/assignment_question.md`)

## Steps
1. Read the assignment question and list its questions (Q1, Q2, ...).
2. Read the submission and match each answer to a question.
3. Mark each question as `answered`, `partial` or `missing`.
4. Set the answer type: `theoretical`, `MCQ`, `numerical`, `case-based`,
   `analytical`, `mixed` (more than one type) or `other`.
5. For numerical answers, copy the student's inputs and results exactly as
   written, even if they are wrong. Set `numerical_verification_required` to true.
6. Flag anything unusual, with the exact quote. Examples: answer placed under
   the wrong question, missing calculation steps, a recommendation that is not
   one of the listed options.
7. Save the result to `evaluation_findings/submission_analysis_{student_id}.md`.
   Take `student_id` from the file name (student_submission_B.md -> B).

## Output
One JSON block with: `student_id`, `source_file`, a `questions` list and
`recommended_next_action`. Each question has `question_id`, `status`,
`answer_type`, `numerical_verification_required`, `extracted_calculation`
(only for numerical answers) and `ambiguity_flags`.
See `examples/sample_analysis.md`.

## Guardrails
- Do not evaluate quality or assign marks.
- Do not invent or complete missing answers.
- Do not correct the student's numbers. Copy them as written.
- Quote only text that exists in the submission.
- Do not change the assignment requirements.