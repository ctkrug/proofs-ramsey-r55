Best live route: `strategy-a230b66ef386`, but only as a symmetry-quotient validation gate—not as a novelty search.

The official April 2026 survey still records `43 ≤ R(5,5) ≤ 46` and calls the 656 order-42 graphs strong evidence rather than a complete classification. [Dynamic Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) The historic paper already found those same 656 through deletion/extension, annealing, tabu, novelty-biased, and large subgraph-neighborhood searches; this route must not be presented as a new construction mechanism. [McKay–Radziszowski](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf)

The exact delta is standard but worthwhile: remove duplicate destroy-label representations inside the frozen-core SAT boundary. The prior 64 labelled models collapsed to eight normal forms.

Critical premise checked: record 21’s 12 destroyed vertices have 12 distinct 30-bit frozen-core rows. Once the non-invariant Hamming-distance constraint is removed, its row-sorted destroy-label permutation is therefore a guaranteed known valid solution. So an unblocked “first production model” is only a positive control, never a novelty discriminator.

Cheapest discriminator:

1. Independently test lex-CNF versus direct sorting on all 32,768 toy boundaries with three fixed and three destroyed vertices, including tied rows and exhaustive `S₃` orbit coverage.
2. Verify the row-sorted record-21 source directly satisfies the regenerated no-Hamming CNF and both graph checkers.
3. Block that one canonical primary vector, then allow exactly one post-block SAT model. Record its class/normal form; do not infer more.

Safe efficiency claims:

- Existing frozen core fixes 435/861 edges (50.52%), leaving 426 primaries.
- Lex quotient is up to `12! = 479,001,600` only in the distinct-row stratum; the only measured reduction is 64→8 (8×).
- Retain one incremental solver/base CNF, primary-only blocks, compact vectors, and full independent graph checks after each SAT model.
- Do not attempt the all-core embedding census: its naive scale is `656 × C(42,12)` and the retained negative probe already cost 10.63 seconds for one host.

Stop on any toy-orbit/encoding mismatch, residual Hamming condition, source-control failure, checker disagreement, a dual-checked corpus-novel graph, or the single post-block model. Reject claims that a labelled block excludes a class, that the eight-normal-form observation generalizes, or that an unblocked first model tests novelty.

I saved the full memo at [20260721-170623-literature-strategy.md](/root/proof-factory/research/ramsey-r55/workspace/docs/delegate-memos/20260721-170623-literature-strategy.md).
