Memo saved: [experiment-verification memo](/root/proof-factory/research/ramsey-r55/workspace/docs/delegate-memos/20260721-080003-experiment-verification.md).

Best live route: one symmetry-normalized order-42 \(q=20\) SAT pilot. Use the proved complement/relabel coverage lemma to fix \(N(0)=\{1,\ldots,20\}\), adding exactly 41 unit clauses.

Key verification gates:

- New CNF must be exactly the old CNF plus 41 units: 71,421 variables and 1,844,093 clauses.
- Independently audit all unit literals and the complement/relabel coverage argument.
- Require unchanged Ramsey-clause ledger, mutation tests, and a new normalized cold audit.
- SAT requires dual full scans, degree/root checks, and supplied-corpus-only canonical comparison.
- UNSAT requires completed DRAT and checked LRAT; timeout remains inconclusive.

Stop after one checked SAT/UNSAT result or the fixed 300-second timeout; reject broadening to other degree bands, order 43, or extra budget solely after an unknown.
