## Literature-strategy memo

**Status:** unchanged. Dynamic Survey DS1.18 (24 Apr 2026) still records strong evidence for 656 order-42 critical graphs and the range `43 ≤ R(5,5) ≤ 46`; its table gives upper bound 46. [Dynamic Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) The current Angeltveit–McKay manuscript remains v2 (1 Sep 2025) and states the independently implemented `R(5,5) ≤ 46` computation. [arXiv](https://arxiv.org/abs/2409.15709)

**Best live route:** finish `strategy-r55twoorbitdomainwall2026` as an **exact burden-one exclusion**, not another witness search. The existing packet already proves burden zero UNSAT in all 20 fixed-background two-orbit slices, while the publisher seed supplies burden two in every slice. Thus each slice has exact minimum two iff its raw-origin burden-≤1 encoding is UNSAT.

This is the strongest immediate route because it turns a nearly completed, proof-carrying bounded family into a complete local-minimum classification. It does not duplicate pure circulant search, radius 1/2 search, the one-orbit sweep, or generic heuristic search. It also avoids unjustified escalation to three orbits.

**Exact rationale:** the current burden-zero CNFs deduplicate clauses, which is sound for satisfiability but unsound for counting monochromatic `K5`s: distinct five-set/color origins can induce the same clause and must each count separately. The existing complete origin ledgers already preserve that multiplicity. The missing premise is therefore explicit:

- add one relaxation variable to every raw origin, via `(origin clause ∨ r_i)`;
- impose `Σ r_i ≤ 1` with an independently derived cardinality encoding;
- do not introduce relaxation variables only after clause deduplication.

A satisfying assignment then decodes to a graph with at most one monochromatic `K5`; an UNSAT proof excludes precisely that possibility within the slice.

**Cheapest discriminator:** first specialize the extended two-orbit encoding back to the retained distance-6 slice and demand UNSAT for burden ≤1, matching its independently established exact minimum two. Only then sweep the 20 unsymmetrized 86-edge slices. No symmetry breaker is needed or desirable.

**Controls:**

- Hash-lock the two Springer source bodies and replay the prerequisite reports.
- Extend both Python and C derivations independently; require byte-identical raw-origin ledgers and a separately compared extended-CNF semantics, not merely matching DIMACS headers.
- Test duplicate-origin multiplicity deliberately: mutate one duplicated origin or its relaxation literal and require the comparison/audit to fail.
- For SAT, materialize the full 43-vertex graph and have both full graph/complement K5 enumerators confirm the exact count and identities.
- For UNSAT, retain DRAT and independently check it; convert/check LRAT as in the existing adversarial audit.
- Preserve the no-all-variable-origin assertion, or explicitly encode such origins if it changes.

The existing [checkpoint](</root/proof-factory/research/ramsey-r55/workspace/CHECKPOINT.md:1>) and [adversarial audit](</root/proof-factory/research/ramsey-r55/workspace/artifacts/two_orbit_slice_adversarial_audit.json:1>) are sufficient prerequisites; they already establish full-origin semantic checks and proof verification for burden zero.

**Failure modes:** counting unique clauses rather than raw origins; treating optional `r_i` variables as an exact count without full graph rescanning; an at-most-one encoding error; accidentally relaxing both color origins of a five-set incorrectly; or overstating the result as a claim about arbitrary 86-edge changes or `R(5,5)`.

**Reusable artifact:** a dual-generated, multiplicity-preserving weighted-CNF/MaxSAT schema plus DRAT/LRAT replay bundle. It can later support bounded certified local-MaxSAT neighborhoods. The raw origin/factor data may inform the trapping-atlas route, but only as held-out move-proposal evidence—not as a witness evaluator.

**Stop condition:** stop immediately on any source hash, raw-origin multiplicity, specialization, dual-CNF, proof, or full-scan mismatch. Otherwise stop after either:

1. a fully dual-checked burden-one model, or  
2. 20 proof-checked UNSAT results, which closes this two-orbit family at exact minimum two.

After outcome 2, park this family. Reject a third-orbit release unless a new structural discriminator is supplied; “more freedom” is not one.

**What Sol should independently reject or verify:** reject claims that the 656 are exhaustive, that bounded-slice UNSAT changes the Ramsey bound, or that duplicate clauses may be merged for multiplicity. Verify the official range, source hashes, raw-origin semantics, cardinality encoding, DRAT/LRAT checks, and full-graph identity scans independently.
