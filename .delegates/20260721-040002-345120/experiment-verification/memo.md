Memo saved: [experiment-verification-burden-one.md](/root/proof-factory/research/ramsey-r55/workspace/docs/experiment-verification-burden-one.md).

Best live route: proof-carrying `raw burden ≤ 1` sweep of the 20 already-defined two-orbit slices. Burden zero is already checked UNSAT; the seed gives burden two, so this exactly distinguishes minimum one from two within this bounded family.

Critical failure mode found: the distance-1 ledger has two distinct bad K5 origins that both reduce to DIMACS clause `(7,37)` ([lines 713 and 719](/root/proof-factory/research/ramsey-r55/workspace/artifacts/two_orbit_slices/distance_01/origins_a.tsv:713)). Relaxing deduplicated clauses would falsely report burden one. Relax one variable per raw origin only.

Recommended encoding is sequential AMO: largest slice is 7,911 variables / 15,648 clauses; pairwise AMO would add 7,653,828 clauses. Controls include raw-ledger byte identity, one-orbit specialization, a pinned seed `≤2` SAT / `≤1` UNSAT test, duplicate-merge mutation, DRAT→LRAT verification, and independent full graph scans.

Hard stops: any provenance, multiplicity, mapping, CNF, proof, or semantic mismatch; pilot over 120 s or 1 GiB; production slice over 600 s or 1 GiB. A timeout is inconclusive, never UNSAT.
