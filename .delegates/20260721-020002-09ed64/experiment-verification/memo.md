Best live route: unsymmetrized burden-zero sweep of the 20 two-orbit cyclic slices. It avoids a risky symmetry break and directly tests whether freeing distance 6 plus one other orbit yields a valid K43 coloring.

I replayed the retained distance-6 gate successfully: minimum burden 2, 86 optima, and matching reduced constraints/full rescans.

The full verification memo, including controls, proof-log plan, stop conditions, and failure modes, is here:

[20260721-020002-experiment-verification.md](/root/proof-factory/research/ramsey-r55/workspace/docs/delegate-memos/20260721-020002-experiment-verification.md)

Key rejection rule for Sol: do not accept a SAT solver status or a rotation symmetry break alone. SAT requires both full K5 checkers; UNSAT requires archived CNF plus independently checked proof.
