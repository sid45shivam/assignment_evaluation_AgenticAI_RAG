"""Run: python skills/quality-control/scripts/test_qc_checks.py  (all data is fictional)"""
import copy
import tempfile
from pathlib import Path

from qc_checks import run_qc

RUBRIC = """# Question 1: Theory — 10 Marks
### Criterion 1: Definition — 5 Marks
### Criterion 2: Example — 5 Marks
# Question 2: Calculation — 10 Marks
### Criterion 1: Result — 10 Marks
"""

SUBMISSION = """A network is responsive when it delivers products quickly.
For example, a retailer opens a second warehouse near a big city.
EOQ = 1200 units
"""


def crit(q, name, marks, mx, evidence, conf="HIGH", cites=None, issues="None"):
    return {"question_id": q, "criterion": name, "max_marks": mx, "proposed_marks": marks,
            "evidence": evidence, "citations": cites or ["Context Limitation: none"],
            "confidence": conf, "unresolved_issues": issues}


GOOD = [
    crit("Q1", "Definition", 5, 5, ["responsive when it delivers products quickly"]),
    crit("Q1", "Example", 4, 5, ["a retailer opens a second warehouse near a big city"]),
    crit("Q2", "Result", 3, 10, ["EOQ = 1200 units"]),
]
VERIFIER_ERRORS = {"overall": "FAIL", "steps": [{"step": "EOQ", "status": "FAIL"}]}


def failed(r):
    return [c["check"] for c in r["checks"] if c["status"] == "FAIL"]


def test_good_evaluation_passes():
    r = run_qc(GOOD, SUBMISSION, RUBRIC, VERIFIER_ERRORS, "Q2")
    assert r["qc_status"] == "PASS" and not r["escalation_required"]
    assert r["totals"]["total"] == 12


def test_invented_quote_fails():
    c = copy.deepcopy(GOOD)
    c[0]["evidence"] = ["Responsiveness means fast delivery to every customer worldwide"]
    assert "Evidence found in submission" in failed(run_qc(c, SUBMISSION, RUBRIC))


def test_marks_without_evidence_fail():
    c = copy.deepcopy(GOOD)
    c[1]["evidence"] = ["No evidence found"]
    assert "Evidence found in submission" in failed(run_qc(c, SUBMISSION, RUBRIC))


def test_marks_above_max_fail():
    c = copy.deepcopy(GOOD)
    c[0]["proposed_marks"] = 6
    assert "Score limits and rubric maximums" in failed(run_qc(c, SUBMISSION, RUBRIC))


def test_changed_max_marks_fail():
    c = copy.deepcopy(GOOD)
    c[0]["max_marks"] = 6
    assert "Score limits and rubric maximums" in failed(run_qc(c, SUBMISSION, RUBRIC))


def test_missing_criterion_fails():
    assert "Rubric coverage" in failed(run_qc(GOOD[:2], SUBMISSION, RUBRIC))


def test_full_marks_despite_verifier_errors_fail():
    c = copy.deepcopy(GOOD)
    c[2]["proposed_marks"] = 10
    assert "Numerical verification consistency" in failed(run_qc(c, SUBMISSION, RUBRIC, VERIFIER_ERRORS, "Q2"))


def test_low_confidence_escalates():
    c = copy.deepcopy(GOOD)
    c[1]["confidence"] = "LOW"
    r = run_qc(c, SUBMISSION, RUBRIC)
    assert r["escalation_required"] and r["confidence"] == "LOW"


def test_medium_confidence_is_review_note_only():
    c = copy.deepcopy(GOOD)
    c[1]["confidence"] = "MEDIUM"
    r = run_qc(c, SUBMISSION, RUBRIC)
    assert not r["escalation_required"] and r["review_notes"]


def test_unresolved_issue_escalates():
    c = copy.deepcopy(GOOD)
    c[1]["unresolved_issues"] = "Valid alternative approach, needs faculty view"
    assert run_qc(c, SUBMISSION, RUBRIC)["escalation_required"]


def test_citation_to_missing_file_fails():
    c = copy.deepcopy(GOOD)
    c[0]["citations"] = [{"file": "ghost.pdf", "page": 1}]
    with tempfile.TemporaryDirectory() as d:
        Path(d, "real.txt").write_text("x")
        assert "Citations" in failed(run_qc(c, SUBMISSION, RUBRIC, reference_dir=d))


def test_citation_to_existing_file_passes():
    c = copy.deepcopy(GOOD)
    c[0]["citations"] = [{"file": "real.txt", "page": 1}]
    with tempfile.TemporaryDirectory() as d:
        Path(d, "real.txt").write_text("x")
        assert "Citations" not in failed(run_qc(c, SUBMISSION, RUBRIC, reference_dir=d))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)