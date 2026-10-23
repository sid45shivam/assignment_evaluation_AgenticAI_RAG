# Supported Calculations

Only calculations in this table can be verified automatically.
Anything else must be marked `UNVERIFIED` and escalated to faculty.

| Calculation | Script command | Steps checked | Status |
|---|---|---|---|
| EOQ | `numerical_verifier.py eoq` | EOQ, annual ordering cost, annual holding cost, total relevant cost | Implemented |
| Safety stock | not written | | Not implemented |
| Reorder point | not written | | Not implemented |
| Break-even | not written | | Not implemented |

Tolerance: 0.5% relative error counts as correct (covers rounding).
Severity by error size: None (up to 0.5%), Low (up to 5%), Moderate (up to 15%), High (above 15%).

## Adding a new calculation
1. Write `verify_xxx(...)` in `numerical_verifier.py`, like `verify_eoq_chain`.
2. Add it to the `SUPPORTED` dict at the bottom of that file.
3. Add a row to the table above and a test in `test_numerical_verifier.py`.