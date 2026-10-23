"""
Score calculator: adds up criterion scores. Use this instead of adding by hand.

Usage (from project root):
  python skills/numerical-verification/scripts/score_calculator.py --scores 6 6 7 6 8 10

Prints one JSON object with the list of scores and the total.
"""
import argparse
import json


def calculate_total_score(scores):
    """Calculate the total proposed score from criterion scores."""
    total = sum(scores)
    return {
        "criterion_scores": scores,
        "total_score": round(total, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Add up criterion scores.")
    parser.add_argument("--scores", type=float, nargs="+", required=True,
                        help="proposed marks, one per criterion")
    args = parser.parse_args()
    print(json.dumps(calculate_total_score(args.scores), indent=2))


if __name__ == "__main__":
    main()