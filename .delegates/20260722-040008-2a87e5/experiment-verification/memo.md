## Verification memo — R(5,5)

**Best live route (proposal):** run the predeclared record-21 frozen-core residual-SAT discriminator, not another census. The complete supplied-corpus census now validates: 656 canonical hosts, exact mixed 30/60-second gates, 6 positive hosts, 12 vector occurrences, and 8 distinct 426-bit vectors. The standalone validator passed; its manifest hash is `e8a237…36a6`. This remains only a supplied-656-class boundary experiment, not a Ramsey result.

**Rationale:** [sourced fact] the maintained range remains \(43\le R(5,5)\le46\) ([Dynamic Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)). [reported computation] the corpus is now complete and validated; the residual formula preflight reconstructs 198,912 base clauses plus 8 exact block clauses, and confirms record-21’s control vector is blocked. This is the smallest active route that can either produce a fully checked order-42 candidate relative to the corpus or certify a useful fixed-core exclusion.

**Cheapest decisive experiment:** one seed-1 CaDiCaL run, capped at 3,600 seconds, 2 GiB, and 6 GiB proof file, followed by proof/model checks. Use `/usr/bin/cadical` (1.7.3) and freshly compile the pinned drat-trim source (`tools/drat-trim`, upstream revision `2e3b2dc…`). A temporary compile succeeded; source hash `d834…c2ee`, temporary binary hash `cc4e…4459`. Free disk was 17.09 GB, sufficient for the stated 8 GiB reserve, 512 MiB headroom, and 6 GiB proof cap.

**Controls and independent verification:**

- Before solve: bind hashes of residual producer, both graph checkers, corpus report, manifest, validation receipt, CaDiCaL binary, and fresh drat-trim binary; reject any changed input.
- SAT: evaluate the physical DIMACS model; run the independent Python and compiled-C five-subset checkers; canonicalize with `nauty-labelg`; then run [the cold auditor](/root/proof-factory/research/ramsey-r55/workspace/checkers/known_class_residual_sat_audit.py), which imports no producer code and re-enumerates all 656 hosts with NetworkX VF2 plus exact tied-row permutations.
- UNSAT: retain CNF, proof, and solver logs; require drat-trim success in production and a separately rebuilt cold-audit invocation. Any timeout, checker failure, or proof-size hit is `UNKNOWN`.
- Control mutation: flip one vector bit, alter a manifest hash, and replace one block clause; each must fail before solving.

**Failure modes to attack:**

- The completed validator checks stored dual-enumerator agreement and integrity, not a fresh semantic census replay. Cold audit is therefore mandatory.
- Historical runtime NetworkX bytes were not hash-locked by the earlier producer wrapper; do not reinterpret the census as stronger provenance than its receipts state.
- A SAT model can be only `sat_known_control` or a corpus-relative candidate; it is neither global novelty nor an R(5,5) lower bound.
- Verified UNSAT excludes only the frozen order-30 core with the \(S_{12}\) row-lex quotient and supplied-class blocks—not all order-42 graphs.
- Reject any run that silently changes seed, expands time/proof limits, omits vectors, or reuses an interrupted output directory.

**Search-efficiency pass:** symmetry is reduced by row-lex canonicalization; compression uses gzip artifacts and the deduplicated vector ledger; batching puts all 8 blocks in one CNF; incremental work reuses the validated census rather than re-enumerating it; decomposition freezes 30 core vertices; pruning rejects malformed vectors and unions above 10,000; solver state is deliberately one seed-1 solve with one retained proof. The best quantified safe reduction is 12 retained vector occurrences to 8 unique block clauses (33% fewer block instances), while avoiding an estimated 4–6 core-hours of census replay.

**Reusable artifact:** the immutable CNF, vector ledger, solver/proof logs, model if any, and cold-audit receipt. Existing validator: [validation.json](/root/proof-factory/research/ramsey-r55/workspace/artifacts/known-class-embedding-census-v3/validation.json).

**Stop condition:** stop immediately on any preflight/hash/control failure; otherwise stop after the single bounded solve and its independent audit—no parameter retuning.

**Sol should reject unless independently verified:** claims that this exhausts order-42 graphs, claims of novelty from corpus nonmembership, an UNSAT result without two proof checks, or any result lacking the cold all-host replay.
