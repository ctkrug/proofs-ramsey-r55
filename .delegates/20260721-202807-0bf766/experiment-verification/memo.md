## Verification memo — R(5,5) known-class census

**Best live route:** complete the supplied 656-host fixed-core embedding census. It is a control/corpus route, not a Ramsey exclusion: the 656 graphs are historically useful but non-exhaustive. Source: [McKay–Radziszowski](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf); current range remains `43 ≤ R(5,5) ≤ 46` ([Dynamic Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)).

**Computed check:** the cheapest decisive test—independent cold audit of hosts 0–48—passed. It hash-checked corpus/manifest/checkpoint/progress, replayed all 12 saved positive embeddings, regenerated VF2 streams for all six positive hosts, checked eight distinct pullback graphs with independent Python and C K5 checkers, and rejected boundary-bit, mapping, residual-order, and manifest-hash mutations. Audit report SHA-256: `e8c434e5…7511e5f5`. This validates only the 49-host prefix, not the remaining 607 hosts or a block.

**Resume experiment:** resume at `next_host=49`, one immutable host per segment. Before each continuation, verify corpus hash `067902e8…4780eccb`, manifest prefix contiguity, artifact hashes, and frozen producer hashes for the driver plus both enumerators. The latter is currently a provenance gap: segment records hash the driver but not its imported bitset/VF2 modules.

**Controls and stop conditions:**

- Require exact equality of both mapping streams and vector streams, not counts alone.
- Cold-regenerate every positive VF2 stream; after completion, cold-sample 32 empty hosts stratified across source/complement halves and edge-count layers.
- Reject immediately on any hash/parser/stream/replay/K5-checker disagreement, malformed artifact, or accepted mutation.
- Enforce the predeclared aggregate per-host gate `<30 s`, `<1 GiB`, `<100,000` tied-row vectors, throughput `≥0.001` host/s, and total artifact growth `<200 MB`. The current driver’s `--case-seconds 900` is only a timeout, not enforcement of the 30-second research gate; Sol should correct this operational mismatch before relying on it.
- Stop without emitting blocks on any gate failure; redirect then to the predeclared ≤20-clause two-orbit core discriminator.

**Search-efficiency assessment:** this is not a repetition of historic extension/annealing; its delta is a replayable complete pullback ledger for supplied controls. The safe reduction freezes 435 of 861 edges, leaving 426 boundary bits: **49.48% fewer primary variables**. Bitset domains, edge/nonedge forward checks, unused-capacity and Hall-union pruning avoid the naïve `C(42,12)=11,058,116,888` residual-set scan per host. Row-lex ordering compresses representation but expands all tied permutations, so it does not silently quotient coverage. Hosts are atomically decomposed; gzip/hash manifests compress storage; parsing is reused within a segment. No DFS memoization, unsafe symmetry quotient, or solver-learned state is claimed.

Observed prefix cost is 3.42 s bitset + 17.11 s VF2 per host on average (20.53 s aggregate); the remaining-work point estimate is about 3.5 CPU-hours, not a bound.

**Reusable artifact:** a frozen-code, hash-chained 656-row manifest; per-host full custom streams; retained or cold-regenerable VF2 streams; tied-order pullbacks; and final dual-check graph6 bundle.

**Sol should reject:** any “known-class block,” SAT result, or novelty claim before all 656 hosts and final audit pass; any claim that the 656 are exhaustive; and any partial block set. Sol should independently verify the imported-module hash lock and the distinction between labelled boundary vectors and isomorphism-class exclusions.
