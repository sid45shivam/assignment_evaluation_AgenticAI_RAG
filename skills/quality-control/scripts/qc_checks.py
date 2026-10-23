"""
QC checks: automatic, repeatable checks of one student's rubric evaluation.
The agent must not mark a check PASS unless this script says so.

Usage (from project root):
  python skills/quality-control/scripts/qc_checks.py --student B --numeric-question Q2

Defaults (override with flags if your files are elsewhere):
  --submission  Data/submissions/student_submission_{student}.md
  --evaluation  evaluation_findings/rubric_evaluation_{student}.md   (student file name: student_B)
  --verification verification_findings/numerical_verification_student_{student}.md  (optional)
  --analysis    evaluation_findings/submission_analysis_student_{student}.md        (optional)
  --rubric      Data/assignment_rubric.md
  --reference-dir Data/reference_materials

Prints one JSON object. Paste it into the QC report unchanged.
This script checks facts. It cannot judge whether a mark fits the rubric band;
that judgement stays with the agent (see references/qc_rules.md).
"""
import argparse
import json
import re
from pathlib import Path

DECODER = json.JSONDecoder()
CONFIDENCE_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


# ---------- helpers ----------

def norm(s):
    """Remove markdown/LaTeX noise so formatting differences do not matter."""
    s = re.sub(r"[\\*`$_>#]", "", str(s))
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_in_text(quote, text):
    """A quote may use '...' to skip words; every fragment must appear in the text."""
    parts = re.split(r"\.\.\.|\u2026|;", str(quote))
    fragments = [re.sub(r"^given:\s*", "", p.strip(), flags=re.I) for p in parts]
    fragments = [f for f in fragments if len(f) > 8]
    return bool(fragments) and all(norm(f) in norm(text) for f in fragments)


def extract_json_objects(text):
    """Finds every JSON object in a text (fenced or not)."""
    found, i = [], 0
    while True:
        i = text.find("{", i)
        if i == -1:
            return found
        try:
            obj, end = DECODER.raw_decode(text, i)
            if isinstance(obj, dict):
                found.append(obj)
            i = end
        except ValueError:
            i += 1


def criterion_key(name):
    """'Criterion 2: EOQ Result' and 'EOQ result' give the same key."""
    return norm(re.sub(r"^\s*\\?\s*criterion\s*\d+\s*:\s*", "", str(name), flags=re.I))


def parse_rubric(text):
    """Reads '# Question N: ... - X Marks' and '### Criterion N: Name - X Marks'."""
    rubric, totals, q = {}, {}, None
    for line in text.splitlines():
        line = line.strip().lstrip("\\")
        m = re.match(r"#\s*Question\s+(\d+)\s*:.*?[\u2014\-]\s*(\d+)\s*Marks", line, re.I)
        if m:
            q = f"Q{m.group(1)}"
            rubric[q], totals[q] = {}, int(m.group(2))
            continue
        m = re.match(r"#{3}\s*Criterion\s+\d+\s*:\s*(.*?)\s*[\u2014\-]\s*(\d+)\s*Marks", line, re.I)
        if m and q:
            rubric[q][criterion_key(m.group(1))] = int(m.group(2))
    return rubric, totals


# ---------- checks ----------

def check_rubric_coverage(criteria, rubric):
    issues, seen = [], set()
    for c in criteria:
        key = (str(c.get("question_id")), criterion_key(c.get("criterion", "")))
        if key in seen:
            issues.append(f"Duplicate criterion: {key[0]} {c.get('criterion')}")
        seen.add(key)
        if key[1] not in rubric.get(key[0], {}):
            issues.append(f"Not in rubric: {key[0]} {c.get('criterion')}")
    for q, crits in rubric.items():
        for name in crits:
            if (q, name) not in seen:
                issues.append(f"Rubric criterion not evaluated: {q} {name}")
    return issues


def check_score_limits(criteria, rubric):
    issues = []
    for c in criteria:
        label = f"{c.get('question_id')} {c.get('criterion')}"
        marks, mx = c.get("proposed_marks"), c.get("max_marks")
        if not isinstance(marks, (int, float)) or not isinstance(mx, (int, float)):
            issues.append(f"{label}: marks or max is not a number")
            continue
        if marks < 0 or marks > mx:
            issues.append(f"{label}: {marks} is outside 0 to {mx}")
        rub_max = rubric.get(str(c.get("question_id")), {}).get(criterion_key(c.get("criterion", "")))
        if rub_max is not None and rub_max != mx:
            issues.append(f"{label}: max_marks {mx} differs from rubric {rub_max}")
    return issues


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def check_evidence(criteria, submission_text):
    issues = []
    for c in criteria:
        label = f"{c.get('question_id')} {c.get('criterion')}"
        quotes = [q for q in _as_list(c.get("evidence")) if norm(q) != "no evidence found"]
        marks = c.get("proposed_marks")
        if isinstance(marks, (int, float)) and marks > 0 and not quotes:
            issues.append(f"{label}: {marks} marks but no quoted evidence")
        for q in quotes:
            if not quote_in_text(q, submission_text):
                issues.append(f"{label}: quote not found in submission: \"{str(q)[:90]}\"")
    return issues


def _pdf_pages(path):
    try:
        import pypdf
        return len(pypdf.PdfReader(str(path)).pages)
    except Exception:
        return None  # pypdf missing or unreadable: page range not checked


def check_citations(criteria, reference_dir):
    issues = []
    for c in criteria:
        label = f"{c.get('question_id')} {c.get('criterion')}"
        cites = _as_list(c.get("citations"))
        if not cites:
            issues.append(f"{label}: no citations and no Context Limitation note")
        for cite in cites:
            if isinstance(cite, str):
                if not cite.lower().startswith("context limitation"):
                    issues.append(f"{label}: citation is not in {{file, page}} form: {cite[:60]}")
                continue
            fname, page = cite.get("file"), cite.get("page")
            if not fname or not isinstance(page, int) or page < 1:
                issues.append(f"{label}: citation needs a file and a page number")
                continue
            if reference_dir:
                path = Path(reference_dir) / fname
                if not path.is_file():
                    issues.append(f"{label}: cited file not found: {fname}")
                elif path.suffix.lower() == ".pdf":
                    n = _pdf_pages(path)
                    if n is not None and page > n:
                        issues.append(f"{label}: {fname} has {n} pages, cited page {page}")
    return issues


def compute_totals(criteria):
    by_q = {}
    for c in criteria:
        if isinstance(c.get("proposed_marks"), (int, float)):
            q = str(c.get("question_id"))
            by_q[q] = by_q.get(q, 0) + c["proposed_marks"]
    return {"by_question": by_q, "total": sum(by_q.values())}


def check_question_totals(totals, rubric_totals):
    issues = []
    for q, got in totals["by_question"].items():
        if q in rubric_totals and got > rubric_totals[q]:
            issues.append(f"{q}: total {got} is above the question maximum {rubric_totals[q]}")
    return issues


def check_numerical(criteria, verification, numeric_question, rubric_totals, totals):
    """If the verifier found errors, the numerical question cannot have full marks."""
    issues, escalate = [], []
    if not verification or not numeric_question:
        return issues, escalate
    overall = verification.get("overall")
    if overall == "UNVERIFIED":
        escalate.append("Numerical verification is UNVERIFIED (no script for this calculation)")
    bad = [s for s in verification.get("steps", []) if s.get("status") in ("FAIL", "CARRY-FORWARD-PASS")]
    if bad and numeric_question in rubric_totals:
        got = totals["by_question"].get(numeric_question, 0)
        if got >= rubric_totals[numeric_question]:
            names = ", ".join(s.get("step", "?") for s in bad)
            issues.append(f"Verifier found errors ({names}) but {numeric_question} has full marks")
    return issues, escalate


def confidence_and_escalation(criteria, analysis, escalate):
    """LOW confidence or open issues must go to faculty. MEDIUM only needs review."""
    reasons, notes = list(escalate), []
    levels = []
    for c in criteria:
        label = f"{c.get('question_id')} {c.get('criterion')}"
        level = str(c.get("confidence", "LOW")).upper()
        level = level if level in CONFIDENCE_ORDER else "LOW"
        levels.append(level)
        if level == "LOW":
            reasons.append(f"{label}: LOW confidence")
        elif level == "MEDIUM":
            notes.append(f"{label}: MEDIUM confidence")
        issue = str(c.get("unresolved_issues", "None")).strip()
        if issue and issue.lower() not in ("none", "none."):
            reasons.append(f"{label}: unresolved issue: {issue[:100]}")
    for q in (analysis or {}).get("questions", []):
        for flag in q.get("ambiguity_flags", []):
            notes.append(f"{q.get('question_id')}: analysis flag: {flag.get('issue', flag) if isinstance(flag, dict) else flag}")
    overall = min(levels, key=lambda l: CONFIDENCE_ORDER[l]) if levels else "LOW"
    return overall, reasons, notes


# ---------- main logic ----------

def run_qc(criteria, submission_text, rubric_text, verification=None,
           numeric_question=None, analysis=None, reference_dir=None):
    rubric, rubric_totals = parse_rubric(rubric_text)
    totals = compute_totals(criteria)
    num_issues, escalate = check_numerical(criteria, verification, numeric_question, rubric_totals, totals)

    checks = [
        ("Rubric coverage", check_rubric_coverage(criteria, rubric)),
        ("Score limits and rubric maximums", check_score_limits(criteria, rubric)),
        ("Evidence found in submission", check_evidence(criteria, submission_text)),
        ("Citations", check_citations(criteria, reference_dir)),
        ("Question totals", check_question_totals(totals, rubric_totals)),
        ("Numerical verification consistency", num_issues),
    ]
    results = [{"check": n, "status": "PASS" if not i else "FAIL", "issues": i} for n, i in checks]
    failed = [r["check"] for r in results if r["status"] == "FAIL"]

    confidence, reasons, notes = confidence_and_escalation(criteria, analysis, escalate)
    if failed:
        reasons.append("QC failed: " + ", ".join(failed))
    return {
        "qc_status": "FAIL" if failed else "PASS",
        "checks": results,
        "totals": totals,
        "confidence": confidence,
        "escalation_required": bool(reasons),
        "escalation_reasons": reasons,
        "review_notes": notes,
    }


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _first(objects, key):
    return next((o for o in objects if key in o), None)


def main():
    p = argparse.ArgumentParser(description="Automatic QC checks for one student.")
    p.add_argument("--student", required=True, help="student id, for example B")
    p.add_argument("--numeric-question", help="question id with calculations, for example Q2")
    p.add_argument("--submission")
    p.add_argument("--evaluation")
    p.add_argument("--verification")
    p.add_argument("--analysis")
    p.add_argument("--rubric", default="Data/assignment_rubric.md")
    p.add_argument("--reference-dir", default="Data/reference_materials")
    a = p.parse_args()

    sid = a.student
    submission = a.submission or f"Data/submissions/student_submission_{sid}.md"
    evaluation = a.evaluation or f"evaluation_findings/rubric_evaluation_student_{sid}.md"
    verification = a.verification or f"verification_findings/numerical_verification_student_{sid}.md"
    analysis = a.analysis or f"evaluation_findings/submission_analysis_student_{sid}.md"

    criteria = [o for o in extract_json_objects(_read(evaluation)) if "proposed_marks" in o]
    if not criteria:
        raise SystemExit("No criterion JSON blocks found in the evaluation file.")
    ver = _first(extract_json_objects(_read(verification)), "steps") if Path(verification).is_file() else None
    ana = _first(extract_json_objects(_read(analysis)), "questions") if Path(analysis).is_file() else None

    result = run_qc(criteria, _read(submission), _read(a.rubric), ver,
                    a.numeric_question, ana, a.reference_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()