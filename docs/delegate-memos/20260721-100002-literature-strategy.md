## Literature-strategy memo

**Best live route:** the normalized `q=20` almost-regular order-42 branch, but only as the proposed proof-carrying cube pilot (`strategy-596a3981722b`).

**Sourced fact:** the maintained Dynamic Survey still gives \(43\le R(5,5)\le46\). I fetched its current PDF on 2026-07-21: SHA-256 `fc7df6...79f2d2`, 349,271 bytes, last modified 2026-04-26. The current primary upper-bound preprint remains Angeltveit–McKay v2, whose theorem is \(R(5,5)\le46\) and whose conclusion says further improvement needs new theory, not direct scale-up. [Dynamic Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf), [Angeltveit–McKay](https://arxiv.org/abs/2409.15709)

**Reported computation:** both monolithic q=20 CaDiCaL runs ended `UNKNOWN`; the normalized formula is independently audited as the frozen 1,844,052-clause body plus exactly 41 root units. Its partial DRAT is invalid.

### Exact rationale

This route changes architecture without widening the mathematical claim. It reuses the strongest already-audited packet and tests whether difficulty is concentrated in some assignments of a tiny prefix. It also combines two existing strategies correctly:

- fixed-root complement/relabel coverage from the normalized q=20 route;
- the proof/cube coverage obligations from the certified-pilot route.

It is not a new Ramsey method historically: the current \(R(5,5)\le46\) work already uses SAT and symmetry breaking in its gluing computations. The contribution here is strictly a replayable, bounded proof-carrying pipeline for a clearly scoped slice.

### Cheapest discriminator

First run the complete cube mechanism on normalized \(R(3,3,6)\), then use the same mechanism on q=20:

1. Declare four primary edge variables and all 16 signed cubes before solving.
2. Independently reconstruct the 16 unit suffixes, prove pairwise disjointness and exhaustive coverage, and hash the base-CNF-plus-cube packet.
3. Require checked DRAT and LRAT for every UNSAT leaf; independently rescan any SAT model.
4. Give each production leaf a short, fixed proof-logging budget.

The pilot succeeds only if at least one production leaf resolves or the measurements show a material certificate-throughput/storage gain. A 16-leaf pilot is not an exclusion unless every leaf is resolved and the cover checks.

### Important missing premise

The planned “four cross-part edges” must be selected with residual symmetry in mind. After fixing \(N(0)=\{1,\ldots,20\}\), the formula retains an \(S_{20}\times S_{21}\) label symmetry.

A naive four-edge star or matching can make the 16 cubes collapse into only five isomorphism types by Hamming weight, creating avoidable duplicated solver work. Before running production leaves, either:

- use all 16 leaves merely as a pipeline test and explicitly report their orbit classes; or
- choose a declared four-edge pattern with trivial stabilizer under the residual group, and independently verify that claim.

Do not silently quotient cube leaves by isomorphism: proof transport under the vertex permutation must itself be generated and checked.

A second scope premise is equally important: q=20 covers only degree set \(\{20,21\}\). Even a complete q=20 refutation would not exclude the other complement-reduced almost-regular bands \(q=17,18,19\), much less arbitrary order-42 graphs.

### Controls

- Frozen normalized CNF SHA-256 `87b707...865dd`; verify it remains exactly the audited base plus 41 units.
- Independent C Ramsey-clause ledger and standalone normalization auditor.
- Normalized \(R(3,3,6)\) must replay with both DRAT and LRAT checks before production.
- Cube-manifest checker must not import the cube generator.
- Keep the full raw 16-leaf manifest even if orbit equivalences are later exploited.
- Treat the authenticated 656 controls only as a novelty/degree control, never as a complete census.

### Failure modes and stop condition

Stop immediately on a cover mismatch, variable-map mismatch, proof-check failure, decoded-model failure, or changed base formula. Also stop the production pilot if no leaf resolves within the predeclared budget or projected proof storage is not materially better than the monolith.

Do not redirect immediately to q=17–19 after an inconclusive cube result; that repeats the same unknown cost model across additional bands.

### Reusable artifact

The valuable deliverable is a generic **CNF cube manifest + independent cover/proof checker**, validated on normalized \(R(3,3,6)\), with:

- fixed primary-variable map;
- cube/unit ledger;
- leaf-to-proof/model mapping;
- DRAT-to-LRAT verification records;
- optional checked vertex-permutation proof transport.

This is reusable for later q-bands and bounded K43 repair families without overstating any result.

### What Sol should reject or verify independently

Reject:

- partial DRAT streams, partial cube sets, or aggregate solver statistics as evidence of UNSAT;
- any claim that q=20 settles almost-regular order-42;
- any symmetry quotient without an explicit, independently checked transport/coverage argument;
- any “speedup” based on isomorphic duplicate leaves.

Independently verify the source hashes, root-normalization coverage lemma, cube cover, each leaf’s assumptions, and every completed proof/model. The durable state supports this pilot; it supports no bound change or candidate claim.
