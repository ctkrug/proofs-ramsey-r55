## Verification memo — R(5,5) control gate

**Best live route:** close the authenticated order-42 corpus gate (`strategy-r55controls2026`). No search or repair experiment is presently admissible: the corpus file is absent and the existing preflight correctly ran zero target checks.

**Rationale:** a hypothetical 43-vertex witness has 43 valid 42-vertex deletions, none of which may be one of the known 656 controls. Therefore novelty, K43 deletion comparison, and repair search all require a trusted, canonically indexed 42-graph control set first. This is a prerequisite, not evidence for a new bound.

### Cheapest decisive discriminator

Obtain unchanged raw bytes of McKay’s `r55_42some.g6` through a genuinely new path—not another `curl` attempt in this DNS-blocked environment—and place them at:

`sources/r55_42some.g6`

Preserve a provenance sidecar recording retrieval time, final URL, response headers/content type, byte count, and SHA-256. The claimed authoritative URL is:

https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6

Run the existing fail-closed corpus gate only if byte preflight passes:

- 47,888 bytes;
- exactly 328 nonblank LF-terminated graph6 records;
- SHA-256 `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.

This frozen digest is a **mirror acquisition discriminator**, not proof that the raw bytes came from the maintained ANU source. If authoritative bytes differ, preserve them unchanged, stop, and seek a second authoritative retrieval or maintainer confirmation; do not alter the expected constant.

### Required controls

The target run must establish, for the supplied 328 records and 328 derived complements only:

- Checker A’s direct `C(42,5)` enumeration and Checker B’s recursive bitset search agree exactly, including forbidden-set identities.
- Both report zero monochromatic 5-sets on all 656 instances.
- Both custom graph6 parsers and NetworkX agree on every full 861-bit upper-triangle adjacency fingerprint.
- Complement is an involution, has inverse adjacency bits, edges summing to 861, and complementary degrees.
- Base edge histogram is `{423:1,424:7,425:29,426:66,427:89,428:77,429:43,430:16}`; all 656 degrees lie in `19..22`.
- `nauty-labelg` yields 656 distinct canonical labels.

One missing target-level control should be added before treating a pass as complete: compare the locally generated complements **byte-for-byte** with `nauty-complg` on the acquired 42-vertex corpus. The current corpus script uses `labelg`, but its `complg` agreement was demonstrated only in the order-7 regression. That regression is valuable parser evidence, not a substitute for target-instance reference complementation.

Retain the order-7 suite as a regression control: it covers all 1,044 unlabeled classes and their complements, with the same three graph6 padding bits as order 42. Keep the provisional-K43 mutation/rejection suite separate; it checks evaluator behavior but does not authenticate its seed.

### Likely failure modes

- **Provenance substitution:** a matching Hugging Face hash is presented as ANU-source authentication.
- **Line-ending normalization:** CRLF conversion, trailing whitespace, or missing final LF changes the byte artifact.
- **Correlated complement bug:** locally derived complements can be self-consistent across all three parsers; target-level `nauty-complg` comparison catches this.
- **False independence claim:** Checker A and B agree but share a specification/output convention. Preserve their source hashes, compiler command, versions, and full outputs.
- **Overclaiming canonicalization:** 656 distinct labels verifies distinctness of supplied graphs and complements, not completeness of all `(5,5,42)` graphs.
- **Premature target work:** canonicalizing the third-party K43 deletions before both McKay and Springer raw-source gates pass.

### Reusable artifact

Produce an immutable control packet containing:

- raw corpus and provenance sidecar;
- experiment harness record and environment/tool versions;
- `authenticated_corpus_report.json`;
- per-record source, complement, canonical-label, and 861-bit-fingerprint hashes;
- the `nauty-complg` target comparison result;
- checker source hashes and compiled-binary hash.

This packet supports later novelty checks without reinterpreting the 656 set as a classification.

### Stop condition

Stop immediately—before K43 repair, novelty search, SAT, or canonical comparison—on any provenance, hash, byte count, LF termination, record count, parser fingerprint, checker, forbidden-set, histogram, degree, complement, or canonical-label mismatch. Preserve divergent inputs and reports unchanged.

### What Sol should reject or independently verify

Reject any claimed control-gate pass lacking the target-level `nauty-complg` comparison or raw-source provenance. Independently verify the raw SHA-256, rerun both checkers from a clean environment, and confirm the report’s scope says “supplied 656 controls,” not “all order-42 Ramsey graphs.” Also reject restarting the blocked ANU/Hugging Face `curl` route, treating the provisional two-conflict K43 transcription as Springer-authenticated, or construing any successful control gate as a Ramsey bound.
