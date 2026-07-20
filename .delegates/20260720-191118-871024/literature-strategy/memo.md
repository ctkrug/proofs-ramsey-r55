## Literature-strategy memo

**Best live route:** keep `strategy-r55-controls` as the hard gate, then immediately run the validated two-conflict K43 route (`strategy-r55-conflict-core`). This is not pure-circulant duplication: Molnár et al. use a circulant state only to initialize an unrestricted K43 search. [Source](https://doi.org/10.1038/s41467-018-07327-2)

**Rationale:** Direct extension of any known 42-vertex graph is closed: the 1997 study explicitly checked all 656 known graphs as non-extendible. Thus every deletion of any real K43 witness must be an unknown 42-vertex graph. [McKay–Radziszowski](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf) The Nature paper reports a K43 coloring with exactly two monochromatic K5s on six vertices and, importantly, identifies a public “Supplementary Data 4” text artifact, rather than merely an anecdotal seed. [Article](https://www.nature.com/articles/s41467-018-07327-2) The exact payload still needs acquisition and checking; do not treat the reported count as independently reproduced.

**Cheapest discriminator:**

1. Acquire the raw Supplementary Data 4 file, preserve URL and SHA-256, decode its color convention, and run two independent 5-subset checkers.
2. Require exactly two bad K5 identities, union size six, and valid 42-vertex deletions for each vertex in their intersection.
3. Canonicalize those deletions against the hashed 656 controls.

A parser/count/provenance mismatch stops the route. If it passes, exhaust whole-graph Hamming radii 1 then 2 around the seed with proof logs. An UNSAT result is only a bounded-ball fact. The supplementary filename exposed by the publisher is `41467_2018_7327_MOESM6_ESM.txt`; its public static link is [here](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt).

**Controls:**

- Hash and dual-check all 328 graph6 representatives plus complements; reproduce the 656 validity, edge/degree distributions, and complement pairing. The maintained index itself calls this a conjectural, not exhaustive, collection. [Corpus index](https://users.cecs.anu.edu.au/~bdm/data/ramsey.html)
- Reconstruct the public 13- and 9-conflict K43 variants before trusting the two-conflict parser/evaluator. [Exoo study](https://arxiv.org/abs/2212.12630)
- Use semantic mutation tests and an independent representation/language for the second checker.
- Treat “two monochromatic K5s” as a sourced reported computation, not a global multiplicity optimum.

**Failure modes:**

- Confusing MaxSAT clause energy with graph violations. Here each monochromatic K5 violates one of the two color clauses, but this must be checked from the decoded graph.
- Freezing edges outside the six-vertex core proves only that local neighborhood; it says nothing global.
- Using absence from the 656 as a proof of novelty classification. It is useful evidence only until a complete census exists.
- Turning the reported induced-distance-six result into a hard prune without its missing exhaustive artifact.
- Claiming a local UNSAT, solver timeout, or heuristic minimum of two establishes \(R(5,5)=43\).

**Reusable artifact:** a versioned control packet: raw corpus and Supplementary Data 4 bytes; hashes; parser specification; two checker outputs listing every bad 5-set; canonical IDs; and CNF/proof-log schema for radius-bounded runs. This supports both later unknown-42 search and exact repair without repeating historical ambiguity.

**Stop condition:** stop at the first byte/hash/parser/checker/canonicalization mismatch. Do not launch novel-42 or K43 optimization before the controls pass. Stop bounded repair at the stated radius unless the next radius is explicitly authorized and archived as a distinct scope.

**What Sol should reject or independently verify:**

- Reject any “new 42” claim without canonical comparison to the authenticated controls and dual exact checking.
- Independently verify the raw two-conflict seed, color convention, six-vertex union, and deletion claims.
- Reject assertions that the 656 are exhaustive, that two is globally minimal, or that bounded-neighborhood UNSAT is a global exclusion.
