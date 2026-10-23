"""
Numerical verifier: independent, deterministic checks of student calculations.
The result of this script is the source of truth, never the LLM's own arithmetic.

Usage (from project root):
  python skills/numerical-verification/scripts/numerical_verifier.py eoq \
      --D 10000 --S 500 --H 20 --eoq 500 --ordering 10000 --holding 5000 --total 15000

Leave out any --flag the student did not calculate.
Prints one JSON object. Copy it into the verification report unchanged.
"""
import argparse
import json
import math

TOLERANCE = 0.005  # 0.5% relative error counts as correct (covers rounding)


def _pct_error(student, expected):
    if expected == 0:
        return abs(student)
    return abs(student - expected) / abs(expected)


def _close(student, expected):
    return _pct_error(student, expected) <= TOLERANCE


def _severity(student, expected):
    err = _pct_error(student, expected)
    if err <= TOLERANCE:
        return "None"
    if err <= 0.05:
        return "Low"
    if err <= 0.15:
        return "Moderate"
    return "High"


def _step(name, student, true_value, carry_values=None):
    """One calculation step.

    status:
      PASS                 matches the true value
      CARRY-FORWARD-PASS   wrong vs true value, but correct for the student's own
                           earlier figure (the error was inherited, not new)
      FAIL                 wrong, and not explained by an earlier error
      NOT PROVIDED         the student did not calculate this step
    """
    if student is None:
        return {"step": name, "status": "NOT PROVIDED", "expected": round(true_value, 2)}
    if _close(student, true_value):
        status = "PASS"
    elif any(_close(student, c) for c in (carry_values or [])):
        status = "CARRY-FORWARD-PASS"
    else:
        status = "FAIL"
    out = {
        "step": name,
        "student": student,
        "expected": round(true_value, 2),
        "difference": round(student - true_value, 2),
        "pct_error": round(_pct_error(student, true_value) * 100, 2),
        "status": status,
        "severity": _severity(student, true_value),
    }
    if carry_values:
        out["expected_from_student_figures"] = [round(c, 2) for c in carry_values]
    return out


def verify_eoq_chain(D, S, H, eoq=None, ordering=None, holding=None, total=None):
    """Checks EOQ, annual ordering cost, annual holding cost and total cost."""
    q_true = math.sqrt(2 * D * S / H)
    order_true = D / q_true * S
    hold_true = q_true / 2 * H
    total_true = order_true + hold_true

    # Carry-forward values: same formulas, but using the student's own earlier figures
    order_cf, hold_cf, total_cf = [], [], []
    if eoq:
        order_cf = [D / eoq * S]
        hold_cf = [eoq / 2 * H]
        total_cf = [D / eoq * S + eoq / 2 * H]
    if ordering is not None and holding is not None:
        total_cf.append(ordering + holding)  # total adds up the student's own two costs

    steps = [
        _step("EOQ", eoq, q_true),
        _step("Annual ordering cost", ordering, order_true, order_cf),
        _step("Annual holding cost", holding, hold_true, hold_cf),
        _step("Total relevant cost", total, total_true, total_cf),
    ]
    given = [s for s in steps if s["status"] != "NOT PROVIDED"]
    if any(s["status"] == "FAIL" for s in given):
        overall = "FAIL"
    elif any(s["status"] == "CARRY-FORWARD-PASS" for s in given):
        overall = "CARRY-FORWARD-PASS"
    else:
        overall = "PASS"
    return {
        "calc": "EOQ",
        "formula": "EOQ = sqrt(2DS/H); ordering = (D/Q)*S; holding = (Q/2)*H; total = ordering + holding",
        "inputs": {"D": D, "S": S, "H": H},
        "tolerance_pct": TOLERANCE * 100,
        "steps": steps,
        "overall": overall,
    }


def verify_eoq(demand, ordering_cost, holding_cost, student_eoq):
    """Old interface, kept so workflow_orchestrator.py keeps working."""
    expected = math.sqrt(2 * demand * ordering_cost / holding_cost)
    return {
        "formula": "sqrt(2DS/H)",
        "expected_eoq": round(expected, 2),
        "student_eoq": round(student_eoq, 2),
        "difference": round(abs(student_eoq - expected), 2),
        "status": "PASS" if _close(student_eoq, expected) else "FAIL",
    }


# To support a new calculation: write verify_xxx(...) like verify_eoq_chain,
# then add it here and to references/supported_calculations.md.
SUPPORTED = {"eoq": verify_eoq_chain}


def main():
    parser = argparse.ArgumentParser(description="Verify a student calculation.")
    parser.add_argument("calc", help=f"calculation type. Supported: {', '.join(SUPPORTED)}")
    parser.add_argument("--D", type=float)
    parser.add_argument("--S", type=float)
    parser.add_argument("--H", type=float)
    parser.add_argument("--eoq", type=float)
    parser.add_argument("--ordering", type=float)
    parser.add_argument("--holding", type=float)
    parser.add_argument("--total", type=float)
    a = parser.parse_args()

    if a.calc not in SUPPORTED:
        print(json.dumps({"calc": a.calc, "overall": "UNVERIFIED",
                          "reason": "No script for this calculation. Escalate to faculty."}))
        return
    if None in (a.D, a.S, a.H):
        parser.error("eoq needs --D, --S and --H")
    result = verify_eoq_chain(a.D, a.S, a.H, a.eoq, a.ordering, a.holding, a.total)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()