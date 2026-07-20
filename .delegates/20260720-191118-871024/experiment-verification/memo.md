## Verification memo — control gate before frontier work

**Best live route (proposal):** authenticate the known order-42 control corpus before any construction or exclusion experiment. The checkout has no corpus, seed, checker, SAT, or proof-log artifact; it is clean except for metadata. The verified toolchain is also absent.

**Rationale:** any claimed new 42- or 43-vertex result depends on correctly parsing and checking graphs. The 328 public representatives plus complements are the cheapest substantial oracle: they should produce 656 valid `(5,5,42)` controls, yet must not be treated as a complete classification. Source: [McKay data](https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6); historical properties: [McKay–Radziszowski](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf).

**Cheapest discriminator:** a strict two-checker replay of `r55_42some.g6`.

1. Fetch the raw bytes once; retain URL, retrieval time, byte count, and SHA-256.
2. Implement Checker A: an isolated graph6 parser plus transparent enumeration of all `C(42,5)=850,668` 5-subsets per graph.
3. Implement Checker B independently: separate parser and bitset/intersection clique checker, also applied to the complement. No shared parser, adjacency serializer, or forbidden-subgraph routine.
4. Require:
   - exactly 328 source records and 656 records after complementing;
   - every graph has zero `K5` and zero independent 5-set;
   - complement is an involution and remains valid;
   - source-side edge-count histogram `423..430` is `1,7,29,66,89,77,43,16`;
   - all observed degrees are in `19..22`;
   - no duplicates under an independently recorded canonical-labelling procedure.

This is decisive for the control gate: either the inputs and evaluators agree, or no subsequent search output is admissible.

**Controls:**

- Positive controls: force vertices `{0,1,2,3,4}` to a clique, then separately to an independent set; both checkers must identify the injected forbidden 5-set.
- Negative controls: every original and complemented corpus graph must yield an empty violation list.
- Parser controls: reject truncation, invalid graph6 characters, inconsistent vertex order, loops, and asymmetric adjacency.
- Provenance control: retain raw source unchanged; all derived adjacency files must point to its SHA-256.
- Only after this gate passes, reconstruct the public 13- and 9-conflict K43 cyclic controls and require exact agreement on the *identities* of bad 5-sets, not merely their counts. The published two-conflict K43 remains **reported**, not a usable seed, until its exact supplementary graph is recovered and dual-checked.

**Likely failure modes to attack:**

- Shared bug disguised as independence through a shared graph6 decoder or adjacency export.
- Checking only cliques but not cocliques/complements.
- Silent record loss, whitespace handling, or duplicate/complement collapse.
- Canonicalization treated as proof of corpus completeness.
- A K43 near-miss accepted by count alone without its exact violation sets.
- Extending any of the 656 directly: this route is already exhausted for the maintained corpus and must be rejected unless a corpus/provenance error is demonstrated.

**Reusable artifact:** a versioned “R55 control packet”: raw graph6 file; manifest with hashes and record counts; two checker sources and pinned environments; machine-readable per-graph verdicts; canonical IDs; mutation-test results; and a cold-start replay command. This becomes the immutable evaluator for novel-42 and K43 repair work.

**Stop condition:** stop at the first mismatch in source hash, record count, parser acceptance, complement behavior, violation identity, histogram, degree range, or canonical uniqueness. Preserve the raw input and both outputs; do not normalize or patch the source silently. Do not begin novel-42, K43 repair, or any UNSAT slice before the gate passes.

**What Sol should reject or independently verify:**

- Reject heuristic scores, low violation counts, or solver “UNSAT” as evidence of a Ramsey result.
- Reject a claim that the 656 controls are exhaustive.
- Verify independently the two implementations’ non-shared code paths, raw-data hash, complement logic, and mutation tests.
- Verify any later bounded exclusion separately: deterministic encoding, symmetry coverage, cube cover, checked proof logs, and replay from the archived packet.
