# R(5,5) control packet

This workspace contains a fail-closed, dual-checker control gate for `(5,5,n)`
Ramsey graphs.  It does **not** claim a new Ramsey bound and it does not treat the
known 656 order-42 graphs as a complete census.

The two checkers intentionally share no parser or forbidden-subgraph code:

- `checkers/checker_a.py` parses input into a Boolean adjacency matrix and scans
  every 5-subset directly.
- `checkers/checker_b.c` has a separate parser and enumerates 5-cliques by
  recursive bitset intersections, once in the graph and once in its complement.

`scripts/run_control_gate.py` compiles Checker B, compares exact violation
identities, performs positive semantic mutations, tests parser rejection, and
checks all deletions through the intersection of a two-conflict K43 control.

The K43 matrices in `inputs/k43_two_conflict_gist.txt` are a visible third-party
transcription, not the raw Springer supplementary file.  They are useful for
exercising the checkers but cannot close the publisher source-provenance gate.
The McKay order-42 source gate is now closed for the supplied control packet;
see `CHECKPOINT.md` for the exact scope and evidence.

`scripts/run_corpus_gate.py` freezes the mirror acquisition discriminator
for that corpus (47,888 bytes, SHA-256
`067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`).  It
refuses to run downstream checks unless all source bytes match.  On a match it
checks the 328 records and 328 derived complements with both exact checkers,
requires the complete upper-triangle adjacency bitstring to agree across both
custom parsers and an independent NetworkX graph6 parser for every record and
complement, reproduces the published edge histogram and degree range, tests
complement involution, and requires 656 distinct canonical labels from Debian
nauty's `nauty-labelg`.  Provenance schema v2 links the admitted bytes to a
second raw authoritative body, response-header capture, curl transfer metadata,
and the retrieval experiment.  The captured authoritative response omitted
`Content-Type`; the sidecar preserves that absence instead of inferring a type.

## Replay

```bash
python3 scripts/run_control_gate.py \
  checkers/checker_a.py checkers/checker_b.c \
  inputs/k43_two_conflict_gist.txt artifacts/control_report.json
```

Replay the authenticated supplied-corpus gate with:

```bash
python3 scripts/run_corpus_gate.py \
  checkers/checker_a.py checkers/checker_b.c \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json
```

For a graph6 corpus, both standalone checkers accept `--format graph6`.  The
matrix orchestrator is deliberately specialized to the provisional K43 control;
the corpus orchestrator is the fail-closed source and graph6 gate.

The graph6 plumbing itself has a smaller cold-start control that does not need
the historical corpus.  It generates all 1,044 order-7 isomorphism classes with
nauty, checks both custom parsers/evaluators, checks signatures with NetworkX,
and compares the locally derived complements byte-for-byte with `nauty-complg`.
Order 7 deliberately has three graph6 padding bits, just like order 42.
The epoch-2 report `artifacts/graph6_third_parser_report.json` also records the
hash of the imported target corpus-gate module.

The epoch-3 report `artifacts/graph6_full_fingerprint_report.json` strengthens
that test from order/edge/degree signatures to complete adjacency fingerprints
across all three parsers.  It again covers all 1,044 order-7 classes and their
complements, but it is not an order-42 corpus result.

```bash
python3 scripts/test_graph6_plumbing.py \
  checkers/checker_a.py checkers/checker_b.c \
  artifacts/graph6_plumbing_report.json
```
