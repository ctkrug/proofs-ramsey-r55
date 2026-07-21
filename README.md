# R(5,5) control packet

## Epoch-15 labelled-model CEGAR discriminator

One frozen order-30 core was held fixed while an incremental CaDiCaL driver
enumerated and exactly blocked 64 distinct labelled 426-edge boundary vectors.
All 64 decoded graphs were valid, but they occupied only six supplied classes;
an independently checked `S_12` destroy-label normalization collapsed them to
eight normal forms.  This is a bounded negative route discriminator, not a
class block, boundary exclusion, new graph, or Ramsey bound.  See
`docs/novel42-labelled-cegar.md` for the exact scope and hashes.

Replay the independent audit with a fresh output path:

```bash
python3 checkers/novel42_labelled_cegar_audit.py \
  sources/r55_42some.g6 \
  artifacts/authenticated_corpus_report.json \
  artifacts/novel42_labelled_cegar64_report.json \
  artifacts/novel42_labelled_cegar64 \
  artifacts/novel42_labelled_cegar64_cold_audit.replay.json
```

## Epoch-14 exact boundary-repair discriminator

Eight predeclared 12-vertex exact SAT repairs of authenticated order-42
controls all produced valid Ramsey graphs, at labelled boundary Hamming
distances 178--232, but all eight were supplied-corpus rediscoveries.  The
independent cold audit evaluated every one of the 4,061,806 retained physical
clauses, used NetworkX maximal-clique scans and isomorphism independently of
the producer, and identifies eight distinct source-to-control transitions
through a common induced order-30 graph.  This is a bounded negative discovery
result and corpus-local structural dataset, not a new Ramsey graph or bound.
See `docs/novel42-boundary-repair.md` for the exact scope and replay commands.

Replay the retained compressed packet with:

```bash
python3 checkers/novel42_boundary_audit.py \
  sources/r55_42some.g6 \
  artifacts/authenticated_corpus_report.json \
  artifacts/novel42_boundary_repair_report.json \
  artifacts/novel42_boundary_repair \
  artifacts/novel42_boundary_repair_cold_audit.replay2.json
```

## Epoch-13 rowpair-v1 null certificate

The uncoloured union-support adjacency-row Delsarte pair relaxation cuts none
of the 8,052,576 handshake-parity degree histograms at orders 43--45.  The
retained exact certificate assigns one central distance according only to the
parity of the two row weights and checks every Krawtchouk inequality.  This is
a negative result about that relaxation only, not a Ramsey bound and not a
result about a coloured adjacency-aware LP or SDP.  See
`docs/rowpair-v1.md` for the precise formulation.

Rebuild the independent C ledger producer and replay the accepted gate with:

```bash
mkdir -p tools/rowpair artifacts/rowpair_v1
gcc -std=c11 -O2 -Wall -Wextra -Werror \
  -fsanitize=undefined -fno-sanitize-recover=undefined \
  checkers/rowpair_ledger_b.c -o tools/rowpair/rowpair_ledger_b
python3 scripts/run_rowpair_v1_gate.py \
  --corpus sources/r55_42some.g6 \
  --python-ledger artifacts/rowpair_v1/control_ledger_python.replay.tsv \
  --c-ledger artifacts/rowpair_v1/control_ledger_c.replay.tsv \
  --c-checker tools/rowpair/rowpair_ledger_b \
  --output artifacts/rowpair_v1/rowpair_v1_report.replay.json \
  --source sources/rowpair/provenance.json \
  --source sources/rowpair/dynamic-survey-revision18.pdf \
  --source sources/rowpair/2409.15709v2.tar.gz \
  --source sources/rowpair/subgraph-counting-r55.pdf \
  --source sources/rowpair/linear-programming-ramsey-paper29.pdf
python3 checkers/rowpair_certificate.py \
  --report artifacts/rowpair_v1/rowpair_v1_report.replay.json \
  --python-ledger artifacts/rowpair_v1/control_ledger_python.replay.tsv \
  --c-ledger artifacts/rowpair_v1/control_ledger_c.replay.tsv \
  --corpus sources/r55_42some.g6 \
  --output artifacts/rowpair_v1/rowpair_v1_cold_audit.replay.json
```

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
transcription and remain only parser/evaluator controls.  The actual Springer
Supplementary Data 4 bytes are retained under `sources/retrievals/` with two
independent raw retrieval records.  The dedicated publisher gate authenticates
those bytes and exhausts all 903 one-edge flips with two independent raw parsers
and exact evaluators. A second gate exhausts all 407,253 distinct two-edge
flips. A third gate reduces the seed's sole nonconstant cyclic-distance orbit
to a 43-variable CSP and exactly classifies all `2^43` assignments in that
slice. A fourth gate releases distance 6 with each other cyclic distance in
turn and excludes all 20 unsymmetrized burden-zero slices using dual-derived
CNFs and independently checked DRAT/LRAT proofs. See `CHECKPOINT.md` for the
exact scope and evidence.

The epoch-10 almost-regular pilot is a separate bounded research-software
artifact. It encodes the order-42 degree band `{20,21}` without symmetry
breaking, validates the sequential degree counter on every 1-to-6-bit row,
validates the union-of-bands predicate on all 33,867 labelled graphs through
order 6, checks `R(3,3,5)` SAT and `R(3,3,6)` UNSAT with DRAT/LRAT, and
independently regenerates the production Ramsey-clause ledger in C. CaDiCaL
1.7.3 returned `UNKNOWN` at 300 seconds; there is no witness or exclusion. The
retained partial DRAT stream is rejected as a certificate by the cold audit.

The epoch-11 follow-up adds the proved fixed-root representative
`N(0)={1,...,20}` to the same q=20 band. A standalone checker independently
reconstructs all 41 unit literals, proves that the normalized CNF is exactly
the retained unsymmetrized body plus those units, tests the complement/relabel
convention on all labelled order-6 graphs, and rejects five unit-ledger
mutations. CaDiCaL 1.7.3 again returned `UNKNOWN` at 300 seconds. The cold
audit rejects its partial proof stream; this remains a cost result only.

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

Replay the authenticated publisher-seed radius-1 gate with:

```bash
python3 scripts/run_publisher_radius1_gate.py \
  checkers/publisher_radius1_a.py checkers/publisher_radius1_b.c \
  sources/retrievals/springer_supplementary_data4_audit1.txt \
  sources/retrievals/springer_supplementary_data4_audit2.txt \
  artifacts/authenticated_corpus_report.json \
  artifacts/publisher_seed_radius1_report.replay.json
```

This proves only the exact radius-1 statements recorded in the report; it is
not a witness, global optimum, or Ramsey bound.

Replay the no-symmetry almost-regular `q=20` pilot to fresh output paths with:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-almost-regular-42-q20-replay \
  --hypothesis "There exists a Ramsey(5,5,42) graph with all degrees 20 or 21" \
  --expected-signal "checked SAT, checked UNSAT, or an explicit 300-second unknown" \
  --timeout 900 --memory-mb 1024 \
  --source-url https://www.cs.rit.edu/~spr/PUBL/sur14.pdf \
  -- python3 scripts/run_almost_regular_42_pilot.py \
  checkers/almost_regular_42_cnf.py \
  checkers/almost_regular_42_ledger_b.c checkers/checker_b.c \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json \
  tools/drat-trim/drat-trim.c tools/drat-trim/lrat-check.c \
  artifacts/almost_regular_42_q20.replay \
  artifacts/almost_regular_42_q20_report.replay.json
```

Cold-audit the frozen packet to a fresh report path with:

```bash
python3 scripts/audit_almost_regular_42_pilot.py \
  artifacts/almost_regular_42_q20_report.json \
  artifacts/almost_regular_42_q20 \
  checkers/almost_regular_42_ledger_b.c \
  tools/drat-trim/drat-trim.c \
  artifacts/almost_regular_42_q20_audit.replay.json
```

Replay the fixed-root q=20 pilot to fresh output paths with:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-almost-regular-42-q20-normalized-replay \
  --hypothesis "There exists a Ramsey(5,5,42) graph with every degree in {20,21}" \
  --expected-signal "checked SAT, checked UNSAT under complement/relabel coverage, or an explicit 300-second UNKNOWN" \
  --timeout 900 --memory-mb 1024 \
  --source-url https://www.cs.rit.edu/~spr/PUBL/sur14.pdf \
  -- python3 scripts/run_almost_regular_42_q20_normalized.py \
  checkers/almost_regular_42_cnf.py \
  checkers/almost_regular_42_normalization_a.py \
  checkers/almost_regular_42_ledger_b.c checkers/checker_b.c \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json \
  artifacts/almost_regular_42_q20/q20.cnf.gz \
  tools/drat-trim/drat-trim.c tools/drat-trim/lrat-check.c \
  artifacts/almost_regular_42_q20_normalized.replay \
  artifacts/almost_regular_42_q20_normalized_report.replay.json
```

Cold-audit the normalized packet to fresh report paths with:

```bash
python3 scripts/audit_almost_regular_42_q20_normalized.py \
  artifacts/almost_regular_42_q20_normalized_report.json \
  artifacts/almost_regular_42_q20_normalized \
  artifacts/almost_regular_42_q20/q20.cnf.gz \
  checkers/almost_regular_42_normalization_a.py \
  checkers/almost_regular_42_ledger_b.c \
  tools/drat-trim/drat-trim.c \
  artifacts/almost_regular_42_q20_normalized_cold_audit.replay.json \
  artifacts/almost_regular_42_q20_normalized/q20-normalized.audit-cold.replay.json
```

Replay the epoch-12 complete 16-cube pilot to fresh output paths with:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-q20-cube16-pilot-replay \
  --hypothesis "A complete four-variable q=20 cover exposes a leaf decidable in 20 seconds with a checked result" \
  --expected-signal "all toy certificates verify, then at least one checked production SAT/UNSAT leaf or 16 explicit UNKNOWN results" \
  --timeout 1500 --memory-mb 1024 \
  --source-url https://www.cs.rit.edu/~spr/ElJC/sur.pdf \
  -- python3 scripts/run_q20_cube_pilot.py \
  checkers/almost_regular_42_cnf.py \
  checkers/almost_regular_42_normalization_a.py \
  checkers/cube_manifest_a.py \
  artifacts/almost_regular_42_q20_normalized/q20-normalized.cnf.gz \
  artifacts/almost_regular_42_q20_normalized/q20-normalized.map.tsv \
  tools/drat-trim/drat-trim.c tools/drat-trim/lrat-check.c \
  checkers/checker_b.c \
  artifacts/q20_cube16_pilot.replay \
  artifacts/q20_cube16_pilot_report.replay.json 20 256
```

Cold-audit that fresh packet by substituting its report, packet, and experiment
JSON paths in the following retained-packet command. The cold auditor is
intentionally hash-locked to the retained main report; update
`MAIN_REPORT_SHA256` only after independently confirming a fresh report's exact
scope and status.

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-q20-cube16-cold-audit-replay \
  --hypothesis "the retained manifest and toy certificates replay and all production timeout streams are incomplete" \
  --expected-signal "16 toy proof replays pass and fresh drat-trim rejects 16 production streams" \
  --timeout 900 --memory-mb 1024 \
  --source-url https://www.cs.rit.edu/~spr/ElJC/sur.pdf \
  -- python3 scripts/audit_q20_cube_pilot.py \
  artifacts/q20_cube16_pilot_report.json \
  artifacts/q20_cube16_pilot \
  artifacts/almost_regular_42_q20_normalized/q20-normalized.cnf.gz \
  artifacts/almost_regular_42_q20_normalized/q20-normalized.map.tsv \
  checkers/cube_manifest_a.py \
  tools/drat-trim/drat-trim.c tools/drat-trim/lrat-check.c \
  artifacts/q20_cube16_pilot_cold_audit.replay.json \
  artifacts/q20_cube16_pilot/production/cube-manifest.audit-cold.replay.json \
  .proof-experiments/20260721-101546-136ce5/experiment.json
```

This pilot proves no production leaf status: every retained q=20 leaf returned
`UNKNOWN`, and the cold audit rejects every interrupted stream. Its positive
deliverable is the complete physical-CNF manifest/checker and the fully checked
small-instance proof path.

Replay the complete radius-2 gate with:

```bash
python3 scripts/run_publisher_radius2_gate.py \
  checkers/publisher_radius2_a.py checkers/publisher_radius2_b.c \
  sources/retrievals/springer_supplementary_data4_audit1.txt \
  sources/retrievals/springer_supplementary_data4_audit2.txt \
  artifacts/publisher_seed_radius1_report.json \
  artifacts/publisher_seed_radius2_scores.replay.u16le \
  artifacts/publisher_seed_radius2_report.replay.json
```

Replay the exact cyclic-distance-6 slice classification with:

```bash
python3 scripts/run_distance6_slice_gate.py \
  checkers/distance6_slice_a.py checkers/distance6_slice_b.c \
  checkers/publisher_radius1_a.py checkers/publisher_radius1_b.c \
  sources/retrievals/springer_supplementary_data4_audit1.txt \
  sources/retrievals/springer_supplementary_data4_audit2.txt \
  artifacts/publisher_seed_radius2_report.json \
  artifacts/distance6_slice_exact_report.replay.json
```

The radius-2 result is only a Hamming-neighborhood statement. The distance-6
result fixes the other 20 cyclic-distance orbits and therefore is only a
structured-slice classification. Neither changes the Ramsey bound.

Replay the proof-carrying two-orbit burden-zero sweep to fresh output paths:

```bash
python3 scripts/run_two_orbit_slice_gate.py \
  checkers/two_orbit_slice_a.py checkers/two_orbit_slice_b.c \
  checkers/publisher_radius1_a.py checkers/publisher_radius1_b.c \
  sources/retrievals/springer_supplementary_data4_audit1.txt \
  sources/retrievals/springer_supplementary_data4_audit2.txt \
  artifacts/publisher_seed_radius2_report.json \
  artifacts/distance6_slice_exact_report.json \
  tools/drat-trim/drat-trim.c \
  artifacts/two_orbit_slices.replay \
  artifacts/two_orbit_slice_exact_report.replay.json
```

The retained result covers exactly distance 6 plus one other cyclic distance,
with the remaining 19 orbits frozen. It finds no witness and does not yet prove
that each slice has minimum burden two; burden one is the next saved test.

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
