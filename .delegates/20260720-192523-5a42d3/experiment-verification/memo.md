## Experiment-verification memo

**Best live route — proposal:** complete the fail-closed source-authentication control gate before any novel-42 or K43 repair search.

The workspace already contains two independent exact checkers and a provisional K43 control. Replay passed: both checkers found graph2’s two `K5`s, with intersection `{0,15,28,39}` and union `{0,15,22,24,28,39}`; deleting any intersection vertex yielded a valid order-42 graph. This is only a parser/evaluator control: its input is a third-party transcription, not the publisher artifact.

**Rationale:**

- Sourced: the 328 McKay representatives plus complements are known valid order-42 controls, but not an exhaustive classification. [Corpus](https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6)
- Sourced: the maintained known 656 do not extend to 43. [McKay–Radziszowski](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf)
- Inference: any actual K43 witness has 43 vertex-deleted, previously unknown order-42 graphs.
- Therefore, optimizing around known 42 graphs or an unauthenticated K43 transcription risks repeating closed work or debugging an incorrect input.

**Cheapest decisive discriminator:**

Acquire unchanged raw bytes for both:

1. `r55_42some.g6` from McKay.
2. Springer Supplementary Data 4, `41467_2018_7327_MOESM6_ESM.txt`, from the two-conflict experiment. [Article](https://doi.org/10.1038/s41467-018-07327-2)

Archive URL, retrieval time, byte count, SHA-256, and content type. Then run the existing checker pair without shared parsing or forbidden-subgraph code.

Pass criteria:

- corpus: exactly 328 graph6 records; 656 including complements; zero clique and coclique violations; source-side edge histogram `1,7,29,66,89,77,43,16` for 423–430 edges; degrees 19–22;
- seed: decoded graph has exactly two forbidden 5-sets, six-vertex union, four-vertex intersection, and each intersection deletion is valid at order 42;
- canonicalize each valid deletion against the authenticated controls, retaining the canonical tool/version and permutation witness. Absence from the 656 is evidence of novelty, never a completeness proof.

**Controls:**

- Existing positive semantic mutations: force vertices `0..4` into a clique and into an independent set; both checkers must report that exact set.
- Existing malformed-input tests: truncation, nonbinary character, and asymmetry must be rejected by both parsers.
- Add corpus complement-involution and per-record SHA-256 manifests.
- Use `dreadnaut` as a third, separate canonical-labelling control; do not share an adjacency export silently.
- Reconstruct the public 13- and 9-conflict K43 variants before trusting the supplementary-file decoding convention.

**Likely failure modes:**

- Treating agreement between two checkers as authentication of the third-party transcription.
- Wrong color convention or accidental complement when decoding the Springer data.
- Shared graph6-spec misunderstanding in both custom parsers.
- Checking only counts rather than exact violating 5-set identities.
- Canonicalization errors, duplicate collapse, or claiming the 656 are exhaustive.
- Converting local K43 repair UNSAT into a global Ramsey exclusion.

**Reusable artifact:**

An immutable control packet: raw inputs; provenance manifest; checker sources and hashes; compiler/runtime versions; per-graph verdicts; complement map; canonical IDs/permutations; mutation and rejection results; and a cold-start replay command. The present provisional replay report hash is `f854b8e8…356df69e5`; it must remain labelled provisional until raw-source comparison succeeds.

**Stop condition:**

Stop immediately on any source-byte, record-count, parser, violation-identity, complement, histogram, degree, or canonicalization mismatch. Preserve raw input and divergent outputs unchanged. Do not launch K43 repair, novel-42 search, or any UNSAT slice while either raw corpus or publisher-seed provenance remains open.

**Sol should reject or independently verify:**

Reject low conflict counts, solver success, or “not among 656” as a result. Independently replay the raw-source hashes, checker independence, seed color convention, exact two-conflict identities, deletion checks, and canonical comparisons. Any later bounded exclusion additionally needs deterministic encoding, explicit symmetry and cube coverage, checked proof logs, and cold-start replay.
