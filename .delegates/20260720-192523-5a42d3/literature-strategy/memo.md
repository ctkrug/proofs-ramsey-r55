Memo — literature strategy audit

**Best live route:** retain the hard gate `S1 controls`, paired only with reconstructible `S2` near-miss controls; then advance to `S3` (unknown-42 basin), not direct K43 search.

**Rationale (sourced → inference):**

- The current Dynamic Survey revision #18 (24 April 2026) still gives lower bound 43 and upper bound 46; no new exact value appears. [Dynamic Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf)
- The 328 public representatives plus complements are explicitly only “some” known 42-vertex graphs, not an exhaustive classification. [McKay data page](https://users.cecs.anu.edu.au/~bdm/data/ramsey.html)
- McKay–Radziszowski checked that none of their 656 known 42-vertex graphs extends to 43; their historical annealing, tabu, and 65-million-output neighborhood searches found no other class. [Primary paper](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf)
- Therefore, by vertex deletion, any 43-vertex witness would yield 43 valid 42-vertex graphs outside the known 656. This is a direct inference, not a classification theorem.

So a new search that begins with one-vertex extension, known-basin local moves, or “avoid known graphs” without an independently measured novelty condition mostly repeats historically saturated work.

**Cheapest discriminator**

Mirror `r55_42some.g6`, SHA-256 it, parse all 328 records with two independent exact 5-subset checkers, derive complements, and reproduce:

- 656 valid labeled/control instances;
- edge histogram `1,7,29,66,89,77,43,16` for 423–430 edges;
- degree range 19–22;
- zero monochromatic K5 identities, not merely zero counts.

A single mismatch in source hash, graph6 decoding, complement handling, count, or forbidden-set identity stops the route. No novel-42 or K43 repair budget should be spent before this passes.

**Controls**

1. Corpus manifest: URL, retrieval time, raw hash, parser version, per-record hashes.
2. Checker A: literal combination enumeration; Checker B: separate bitset/clique implementation.
3. Reconstruct the public 13- and 9-conflict K43 variants from the Exoo analysis and compare exact violation sets. [Ge et al.](https://arxiv.org/abs/2212.12630)
4. Keep the reported two-conflict K43 only as an untrusted lead until its actual supplementary graph is recovered and dual-checked.

**Historical duplication / missing premise**

- Do not treat the 656 as complete. The primary source calls this a conjecture, while the maintained survey still describes it as strong evidence.  
- Do not repeat direct extension of known 42 controls, generic annealing/tabu, or local common-subgraph searches. Those routes have already been run extensively.
- The McKay data-page phrase “43–47 vertices” is stale wording: it predates the published `R(5,5) ≤ 46` result and must not be cited as current status.
- The conditional one-vertex-extension preprint only establishes emptiness relative to the supplied current sets; it cannot turn the conjectural 656 list into an unconditional upper bound. [Lehavi preprint](https://arxiv.org/abs/2411.04267)
- Upper-bound scaling is not the best live route: the current `≤46` work required independent massive computations, and the formalization proposal’s own extrapolation is about 42 trillion CPU-hours for a direct `≤43` completion. [Angeltveit–McKay](https://arxiv.org/abs/2409.15709), [Gauthier proposal](https://aitp-conference.org/2025/abstract/AITP_2025_paper_3.pdf)

**Reusable artifact**

Produce a small immutable “R55 control packet”: raw corpus, hashes, decoder, two checker outputs, complement mapping, canonical IDs, exact violations for the 13/9 K43 controls, and mutation tests. It is useful to every constructive, MaxSAT, and certification branch and makes future negative claims falsifiable.

**Stop condition**

Stop immediately at any control mismatch. After controls pass, stop an `S3` epoch unless it yields either a dual-verified 42-vertex graph outside all 656 or a precisely scoped, proof-carrying exclusion. Rediscovery is failure, not progress.

**What Sol should independently verify**

Verify the two logical gates: a K43 witness proves `R(5,5) ≥ 44`, and every deletion from it must be a *new* 42 class. Reject any claim based solely on solver success, corpus similarity, the stale data-page wording, the unverified two-conflict seed, or conditional extension relative to the 656.
