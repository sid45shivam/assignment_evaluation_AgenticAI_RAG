"""Run: python skills/numerical-verification/scripts/test_numerical_verifier.py"""
from numerical_verifier import verify_eoq_chain, verify_eoq


def statuses(r):
    return [s["status"] for s in r["steps"]]


def test_correct_rounded_answer_passes():
    r = verify_eoq_chain(10000, 500, 20, 707, 7071, 7071, 14142)
    assert r["overall"] == "PASS"


def test_wrong_eoq_with_correct_method_is_carry_forward():
    r = verify_eoq_chain(10000, 500, 20, 500, 10000, 5000, 15000)
    assert statuses(r) == ["FAIL", "CARRY-FORWARD-PASS", "CARRY-FORWARD-PASS", "CARRY-FORWARD-PASS"]
    assert r["overall"] == "FAIL"


def test_new_error_is_counted_once():
    r = verify_eoq_chain(10000, 500, 20, 707, 7071, 3535, 10606)
    assert statuses(r) == ["PASS", "PASS", "FAIL", "CARRY-FORWARD-PASS"]


def test_wrong_total_fails():
    r = verify_eoq_chain(10000, 500, 20, 707, 7071, 7071, 15000)
    assert statuses(r)[-1] == "FAIL"


def test_missing_steps_are_not_provided():
    r = verify_eoq_chain(10000, 500, 20, eoq=707)
    assert statuses(r) == ["PASS", "NOT PROVIDED", "NOT PROVIDED", "NOT PROVIDED"]


def test_old_interface_still_works():
    assert verify_eoq(10000, 500, 20, 500)["status"] == "FAIL"
    assert verify_eoq(10000, 500, 20, 707)["status"] == "PASS"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)