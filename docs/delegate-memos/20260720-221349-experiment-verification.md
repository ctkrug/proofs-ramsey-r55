# Verification memo — R(5,5) authenticated-corpus gate

**Scope:** experiment design and audit only. This memo makes no Ramsey-bound,
witness, completeness, or source-authentication claim.

## Best live route

Close `strategy-r55controls2026` before any K43 repair or unknown-order-42
search.  The locally present `sources/r55_42some.g6` now has the frozen
47,888-byte SHA-256
`067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.
That makes the supplied bytes a plausible control candidate, but **not yet an
authenticated direct-authority acquisition**.

The immediate blocker is concrete: its sidecar says
`content_type_inferred: true` and its `response_headers` omit `content-type`,
although `content_type` is recorded as `text/plain; inferred from validated
graph6 record format (header absent)`.  This violates the checkpoint's demand
for actual response metadata.  `run_corpus_gate.py` currently accepts this
because it only tests whether the asserted content type begins with
`text/plain`; that is a schema weakness, not source evidence.

## Cheapest discriminator

1. Preserve the current raw bytes and sidecar unchanged, including their
   SHA-256s; do not normalize or overwrite them.
2. Through a genuinely independent raw-file transport, acquire the authoritative
   URL with an immutable header capture and transport command/version.  The URL
   is https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6 .
3. Require the second raw body to equal the frozen digest and the response
   capture to establish final URL, TLS/HTTP status, and an actual content type
   (or preserve an authoritative response lacking it and explicitly relax the
   policy by recorded decision—not by claiming it was present).
4. Only then invoke the recorded one-hour target gate.  The currently checked
   full target gate is:

   `python3 scripts/run_corpus_gate.py checkers/checker_a.py checkers/checker_b.c sources/r55_42some.g6 artifacts/authenticated_corpus_report.json`

The gate is substantial rather than instantaneous: Checker A directly scans
all `C(42,5)` subsets for 328 source records and again for their complements.
It must be run once, without overlapping copies.  An exploratory invocation
was deliberately stopped once the provenance defect was identified; it
produced no report and must not be treated as a partial result.

## Controls and independent verification

On an admissible corpus, require all of the following:

- Frozen bytes: 47,888 bytes, 328 nonblank LF-terminated graph6 records, and
  the stated SHA-256.
- Evaluators: Checker A's direct 5-subset enumeration and freshly compiled
  Checker B's recursive bitset search agree on every source and complement
  instance; retain source, binary, compiler, and output hashes.
- Representation: two custom graph6 parsers plus NetworkX agree on each
  861-bit upper-triangle fingerprint.  The all-unlabeled-order-7 regression is
  a plumbing control only.
- Complement: local complement is an involution, bitwise inverse, has edge
  sums 861, and agrees byte-for-byte with `nauty-complg` on the *actual*
  corpus.
- Structural signatures: the base histogram is
  `{423:1,424:7,425:29,426:66,427:89,428:77,429:43,430:16}`, all 656 degrees
  lie in 19..22, and `nauty-labelg` has 656 distinct labels.
- Clean-room replay: a second operator reruns the frozen command from only
  the raw body, sidecar, checker sources, tool versions, and manifest; compare
  complete report hashes or explain every environment-dependent field.

## Failure modes and stop condition

Stop before target checking on any byte/line/record/hash mismatch or missing
actual provenance.  Stop during target checking on parser, evaluator,
forbidden-set, reference-complement, histogram, degree, or canonical-label
mismatch.  Retain divergent inputs and reports; never change expected values
to admit them.

Likely traps are provenance substitution (an asserted direct retrieval),
inferred headers represented as response metadata, line-ending conversion,
correlated local complement/parser bugs, and treating 656 distinct supplied
classes as a classification of all order-42 Ramsey graphs.

## Reusable artifact and Sol review

The deliverable is a frozen control packet: two raw retrievals plus header
captures, provenance sidecars, corpus/report hashes, per-record fingerprints
and canonical hashes, nauty complement output hash, checker/binary/tool
hashes, and a clean replay log.  It supports later novelty comparisons but
does not certify completeness.

Sol should reject a pass based solely on the present inferred-content-type
sidecar, a full gate report without target-level `nauty-complg`, any rerun that
overlaps instances, and any wording that promotes a passed packet into an
R(5,5) result.  Sol should independently inspect the raw header capture and
recompute the raw SHA-256 before accepting the first target-gate run.
