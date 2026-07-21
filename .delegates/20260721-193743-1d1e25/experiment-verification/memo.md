Memo — experiment verification

Best live route: finish the 656-host supplied-class embedding census. It is a bounded control corpus, not a completeness claim or Ramsey bound. Its exact delta from McKay–Radziszowski’s extension searches is a replayable, complete set of fixed-core boundary pullbacks for every supplied representative and complement.

Rationale: the first 33/656 hosts have exact bitset/VF2 agreement; six contain embeddings. The observed rate is 0.0435 hosts/s—43× above the 0.001 stop floor—with 817 B latest artifact growth, far below 200 MB/segment. The checkpoint projects 13,585 s remaining. I independently checked that all 33 current gzip artifacts hash to their manifest entries, their summaries agree, and all retained vectors are 426-bit binary strings.

Cheapest discriminator: continue host-by-host to 656, then require a cold audit before any residual SAT. A mismatch, a failed pullback, or an unexplained pathological host redirects the route immediately; exact completion yields the reusable class-boundary corpus.

Controls:

- Freeze corpus SHA-256 `067902…0ecc`, source-record-21 core/deletion labels, enumerator versions, and host order `0..655`.
- Require exact equality of embedding counts, mapping hashes, occurrence counts, unique-vector hashes, and full sorted vector streams between the bitset DFS and NetworkX VF2 paths.
- Re-run positive controls: record 21 identity embedding and record 12 retained candidate; complement(record 21) must remain empty.
- Cold-replay every embedding-bearing host: reparse graph6 independently; verify each induced map, every tied-row permutation, every pullback, and both exact K5/complement-K5 checkers.
- Sample at least 32 empty hosts across source/complement halves by cold re-enumeration.
- Mutation gates: flip one boundary edge, transpose one map pair, delete one tied-row order, and alter one manifest hash; each must fail.

Critical failure mode: the current per-host archive stores full bitset data but only a NetworkX summary. That proves live agreement at execution time, but does not preserve the NetworkX stream for offline comparison. Before accepting the completed corpus as independently reconstructible, Sol should either retain compressed full NetworkX sidecars or cold-rerun VF2 for every embedding-bearing host plus the stratified empty sample. Do not infer coverage from matching hashes alone.

Search-efficiency pass: retain the fixed labelled core; use bitset DFS, mapped edge/nonedge filtering, degree and Hall-union pruning, most-constrained branching, host-level checkpointing, and gzip artifacts. Expand every tied-row permutation—no quotienting. This safely replaces infeasible raw `42P30` injection enumeration (and `C(42,12)=11,058,116,888` deleted sets/host) with a measured ≈5.6 aggregate-core-hour census; memoization is correctly excluded until labelled-map multiplicity preservation is proved. Batch only independent hosts; defer solver-state reuse to residual SAT.

Stop conditions: halt on any implementation/replay/checker/mutation mismatch; throughput <0.001 host/s; >200 MB artifact growth/segment; a host exceeding its 900 s cap; or loss of decision value. A timeout is inconclusive, never an exclusion.

Reusable artifact: hash-chained host ledgers with both complete streams, normalized vectors, pullbacks, cold-audit report, and dual K5 certificates.

Sol should reject any “known-class block” lacking durable second-path data, full tied-row coverage, or explicit scope. Independently verify all embedding-bearing hosts, the negative complement control, and the final 656-host coverage/order before considering residual SAT.
