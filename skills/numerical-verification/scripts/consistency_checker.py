"""
Score consistency checker: every criterion score must be between 0 and its maximum.

Usage (from project root):
  python skills/numerical-verification/scripts/consistency_checker.py \
      --scores 6 6 7 6 --max 6 6 7 6

Prints one JSON object: {"status": "PASS" or "FAIL", "issues": [...]}
"""
import argparse
import json


def check_score_consistency(criterion_scores, maximum_scores):
    """Check whether every criterion score is within its allowed range."""
    issues = []

    if len(criterion_scores) != len(maximum_scores):
        return {
            "status": "FAIL",
            "issues": ["Number of scores does not match number of criteria."],
        }

    for i, (score, maximum) in enumerate(zip(criterion_scores, maximum_scores), start=1):
        if score < 0:
            issues.append(f"Criterion {i}: score cannot be negative.")
        if score > maximum:
            issues.append(f"Criterion {i}: score {score} exceeds maximum {maximum}.")

    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def main():
    parser = argparse.ArgumentParser(description="Check criterion scores against their maximums.")
    parser.add_argument("--scores", type=float, nargs="+", required=True,
                        help="proposed marks, one per criterion, in rubric order")
    parser.add_argument("--max", type=float, nargs="+", required=True,
                        help="maximum marks, one per criterion, in the same order")
    args = parser.parse_args()
    print(json.dumps(check_score_consistency(args.scores, args.max), indent=2))


if __name__ == "__main__":
    main()