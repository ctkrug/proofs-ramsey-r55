## Verification memo — known-class embedding blocks

**Best live route:** bounded pilot for complete supplied-class blocking in the fixed record-21 order-30 boundary. This is a control extension of historic common-subgraph/extension work, not a new Ramsey method. Its exact delta is blocking every compatible representation of the supplied 656 controls, rather than individual labelled SAT models. The 656 remain a non-exhaustive corpus ([McKay–Radziszowski](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf)).

**Observed computation:** the authenticated 328-record corpus hash is `067902…780eccb`; the fixed boundary has 426 variables. The existing row quotient is sound but only reduces destroy-label redundancy: exactly \(2^{360}/\binom{2^{30}+11}{12}=479{,}001{,}570.56\ldots\), approaching \(12!\) on distinct rows. It is not a class block. A NetworkX negative containment probe already cost 10.63 s, so feasibility is genuinely unresolved.

**Cheapest discriminator:** enumerate *all induced embeddings* of the fixed labelled 30-core into supplied records 21 and 12, then emit and deduplicate every row-lex-accepted 426-bit boundary vector. Run two implementations:

1. Independent graph6 parser + bitset induced-embedding DFS, branching on the most constrained core vertex and enforcing both edges and nonedges.
2. NetworkX graph6 parser + exhaustive VF2 `subgraph_isomorphisms_iter`.

For an embedding \(f:C\to H\), enumerate residual-vertex orders compatible with nondecreasing 30-bit rows, reconstruct the 426-bit vector, and sort/deduplicate exact bitstrings. Do **not** silently choose one order within tied rows: the present CNF accepts every tied-row order, so each must be blocked or a newly proved tie-breaker must replace the quotient.

**Controls:**

- Record 21 must contain the identity embedding and reproduce the existing row-sorted source vector/hash `8672d9…cdad5e`.
- Record 12 must emit the stored post-block candidate’s primary vector; it is known to be isomorphic to record 12 and to retain this fixed core.
- Complement of record 21 must produce zero embeddings in both implementations (existing one-sided result: false in 10.63 s).
- For every emitted vector, a separate streaming verifier reconstructs the labelled graph, checks frozen-core equality, direct row order, exact equality to the named host under the recorded relabelling, and both five-set checkers.
- Compare exact vector sets, counts by tie multiplicity, and SHA-256 of a deterministic sorted stream—not merely aggregate hashes. Mutate one edge and one mapping record; both must fail replay.
- Independently canonicalize host/candidate graphs with nauty/Traces before any novelty conclusion.

**Stop conditions:** stop before corpus-wide enumeration or residual SAT if either implementation exceeds 30 s or 1 GiB on either positive record; if their exact outputs differ; if the negative control emits anything; or if tied-row expansion exceeds \(10^5\) vectors for either host. Also stop if projected two-implementation corpus work exceeds the predeclared 12 core-hours or 20 GiB of block storage. No partial block set is sound for a “known-class excluded” claim.

**Failure modes to attack:** incomplete VF2 iteration mistaken for enumeration; swapped mapping orientation; omitted complements; deduplication by hash alone; treating one tie order as the entire quotient; core automorphisms producing missed boundary vectors; and claiming an UNSAT residual excludes unknown classes or order-43 graphs.

**Search-efficiency pass:** use 30-bit/42-bit integer masks, incremental candidate intersections, deterministic core order, streaming compressed vectors, external exact sort/dedup, and reuse the fixed core’s invariants across hosts. Batch the two implementations only for I/O; do not share parser or DFS logic. The only currently safe quantified reduction is the verified destroy-label quotient above; no additional class-level compression should be credited until the pilot reconciles.

**Reusable artifact:** a versioned embedding manifest containing corpus hash, host/complement id, every embedding, tie multiplicities, normalized 426-bit vectors, exact sorted-stream hash, and a standalone replay checker.

**Sol should reject:** any run that blocks only one vector per tied row class, extrapolates from the 656 to completeness, resumes labelled CEGAR, or calls residual UNSAT a Ramsey upper bound. Sol should independently verify the two code paths’ mapping direction and that record-12 replay is present before authorizing the full corpus pass.
