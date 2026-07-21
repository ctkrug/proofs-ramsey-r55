## Experiment-verification memo

**Best live route:** `strategy-a230b66ef386`, as a *symmetry-quotient validation control*, not a novelty search. It is a material modification of the existing frozen-core boundary search, closest to historical common-subgraph neighborhood search and known-class-avoidance work—not a new Ramsey mechanism. Its falsifiable delta is only: static \(S_{12}\) destroy-label canonicalization eliminates the measured label redundancy without losing any boundary completion.

The current 64-model run had 64 distinct labelled vectors but only eight destroy-permutation normal forms; all 64 had distinct 30-bit destroyed-to-core rows. [Its cold audit](/root/proof-factory/research/ramsey-r55/workspace/artifacts/novel42_labelled_cegar64_cold_audit.json) supports a potentially exact \(12!\) quotient for those observed models.

**Cheapest discriminator**

Regenerate the record-21 frozen-core formula with:

- the same 426 boundary primary variables;
- all 196,998 raw Ramsey clauses;
- no source-relative Hamming counter;
- lexicographically nondecreasing destroyed-to-core rows for the fixed destroy set  
  \(\{2,3,10,12,14,25,27,30,36,37,38,41\}\).

For each adjacent destroyed pair, encode 30-bit lex order with 29 exact prefix-equality auxiliaries and 175 clauses. Total addition: 319 auxiliaries and 1,925 clauses.

Expected physical formula: **745 variables, 198,923 clauses**, versus the prior 155,976-variable/508,157-clause formula. This removes 155,550 cardinality auxiliaries and 311,159 cardinality clauses: a 99.52% variable and 60.85% clause reduction. It is not an apples-to-apples speed comparison because it also removes the non-invariant distance restriction.

Before any order-42 solve, exhaust the following small coverage gate:

- Fix four core vertices and three destroyed vertices.
- Enumerate all \(2^{21}=2,097,152\) labelled graphs.
- Directly sort the three 4-bit core rows; permute all destroyed–core and destroyed–destroyed edges accordingly.
- Verify the frozen core is unchanged and the resulting rows are ordered.
- Independently check the lex gadget’s truth table on every pair of 4-bit rows and all three prefix auxiliaries.

The exhaustive graph gate must include and report all row-multiplicity cases:

- all distinct: 1,720,320 assignments;
- one tied pair: 368,640;
- all tied: 8,192.

This directly attacks the only subtle coverage issue: tied core rows do not produce a unique representative, but must still retain at least one representative per \(S_3\) orbit.

Then run exactly one predeclared order-42 SAT solve: seed 1, 30 seconds, 1 GiB. A SAT model must pass both full five-set checkers, DIMACS re-evaluation, direct row-order verification, and nauty membership against the supplied 656 controls.

**Why it is sound**

With the 30-core labels fixed, \(S_{12}\) acts only on destroyed vertices. It preserves the frozen core and every Ramsey clause. Every completion can be relabelled by sorting its 30-bit rows. If those rows are distinct, precisely one of its \(12!\) destroy-label permutations is row-sorted; if tied, the quotient is incomplete but still covering. The prior source-distance counter is not invariant under that action and must not remain.

**Controls and stop conditions**

Stop immediately and reject the route if:

- any small graph lacks a sorted representative;
- gadget satisfiability differs from direct lex comparison;
- a tied-row case is lost;
- regenerated raw Ramsey clauses differ from an independent reconstruction;
- the production model fails either graph checker, DIMACS evaluation, or row-order check.

If the one production model is a supplied class, record it as the expected quotient control and stop—do not resume 64-model labelled CEGAR. If it times out, record only the timeout; do not infer that the quotient is unsound or ineffective. A supplied-corpus-novel model warrants independent rechecking, but is not a claimed new Ramsey result.

**Search-efficiency pass**

- **Symmetry:** static \(S_{12}\) lex quotient; observed distinct-row models admit the full \(12!=479{,}001{,}600\) model-space reduction.
- **Compression:** remove the sequential counter rather than retain dead auxiliary structure.
- **Batching/vectorization:** evaluate the \(2^{21}\) small control assignments as packed 21-bit words; no solver calls are needed for the coverage test.
- **Incrementality:** if later authorized, parse the quotient CNF once and retain learned clauses—but only after a sound class-level block exists.
- **Decomposition:** retain the 30-vertex core / 12-vertex boundary split.
- **Pruning:** lex ordering is safe; do not add source-distance pruning or claim core-automorphism reduction.
- **Reusable artifact:** deterministic quotient generator, primary-edge map, gadget specification, exhaustive small-orbit report, and independent cold checker.

**What Sol should reject or verify independently**

Reject any claim that eight observed normal forms mean eight complete-boundary classes, that lex order blocks supplied isomorphism classes, or that the new formula’s speed can be compared to the old distance-constrained one. Verify independently that the Hamming counter is entirely absent, the action permutes internal destroyed edges as well as rows, and the small tied-row control passes.

Context for the historical boundary-search limitation is [McKay–Radziszowski’s R(5,5) analysis](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf); this quotient is only a local canonicalization control within that already-explored neighborhood family.
