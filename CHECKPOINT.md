# R(5,5) research checkpoint — epoch 2

Recorded: 2026-07-20 20:11 UTC

## Outcome and exact scope

Internal research-artifact progress only. No new Ramsey bound, witness,
classification, target-instance exclusion, or canonical novelty claim is made.
The maintained rigorous status remains `43 <= R(5,5) <= 46`.

This epoch continued strategy `r55controls2026`. The required authoritative
McKay corpus acquisition was attempted once under the deterministic experiment
harness. `curl` returned code 6 after two DNS failures and `--remove-on-error`
left no `sources/r55_42some.g6`. The strengthened corpus preflight therefore
returned code 2 and recorded `downstream_checks_run: false`. Zero order-42
corpus records were checked. Do not begin S3 unknown-42 search, S4 K43 repair,
SAT enumeration, or canonical comparison from the provisional local packet.

The reusable positive result is narrower: `scripts/run_corpus_gate.py` now
requires a third, external NetworkX graph6 signature (order, edge count, and
ordered degrees) for every admitted source record and complement, in addition
to the Python and C exact forbidden-set evaluators. The new path passed the
exhaustive order-7 plumbing suite on all 1,044 unlabeled graph classes and their
1,044 complements. Local complement bytes agreed with `nauty-complg`. This is
not evidence about any order-42 record.

## Current source/status audit

- Dynamic Survey DS1.18 is dated 24 April 2026 and records the 43–46 range:
  https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- The 2026 journal paper proves only `R(5,5) <= 46` and says Exoo's lower bound
  43 remains best:
  https://onlinelibrary.wiley.com/doi/full/10.1002/jgt.70029
- McKay's data page says the file supplies 328 representatives and the other
  328 are complements; it does not claim catalogue completeness:
  https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- The March 2026 version of arXiv:2508.16699 describes `R(5,5)=45` as a
  numerical/prime-sequence heuristic estimate. It contains neither a 44-vertex
  witness nor checked exhaustive exclusions and does not change the rigorous
  range: https://arxiv.org/abs/2508.16699

## Decisive experiments

### Authoritative acquisition attempt

Experiment: `.proof-experiments/20260720-200524-16f6f3`

- Return code 6; not timed out; duration 1.107 s; seed 0; 256 MB cap.
- Both attempts failed with `Could not resolve host: users.cecs.anu.edu.au`.
- `sources/r55_42some.g6` is absent.
- `artifacts/corpus_retrieval_headers.txt` is intentionally empty because no
  HTTP response was received.
- Experiment JSON SHA-256:
  `31eaf435d38e25b167d4f33065d49aa0f407703927f9e692e633a05c23a860a6`.

Do not repeat this command-environment acquisition without a new network path
or user-provided raw bytes; the blocker has now reproduced in two epochs.

### Corrected third-parser regression

Experiment: `.proof-experiments/20260720-200957-c4fca8`

- Return code 0; duration 1.488 s; seed 0; 1,024 MB cap.
- `nauty-geng` generated one representative of every 1,044 unlabeled simple
  graph class at order 7.
- Checker A (Python/direct combinations) and Checker B (C/recursive bitsets)
  agreed on exact forbidden-set lists for all source records and complements.
- The NetworkX 3.3 signature path now imported by the target corpus gate agreed
  on order, edge count, and ordered degrees for all 2,088 records.
- Local complement transformation was an involution and agreed byte-for-byte
  with `nauty-complg`.
- Order 7 has three graph6 padding bits, as order 42 does.
- Report: `artifacts/graph6_third_parser_report.json`, SHA-256
  `91469c68ae5abb0353e4a4a1bc13c3e471e1e341bcd402b2f2bf504c6cd6e430`.
- The report records imported corpus-gate SHA-256
  `60a1e201f08103057593dad6ee5f81468702493e6acdf247d804a776fe91797f`.
- Experiment JSON SHA-256:
  `75b343850f042321f6ddfe53c7eee95fed0a9c41683a9d5418bc94951dfa2db0`.

The earlier passing run `.proof-experiments/20260720-200920-965ada` is retained
as a superseded control: its result was correct, but its report did not hash the
imported corpus-gate module. Do not cite it as the decisive replay.

### Strengthened fail-closed control

Experiment: `.proof-experiments/20260720-201015-92e71b`

- Expected return code 2; duration 0.284 s; seed 0; 256 MB cap.
- Report status `source_preflight_failed` and
  `downstream_checks_run: false`.
- Report: `artifacts/corpus_source_preflight_epoch2.json`, SHA-256
  `db893987f58b718712ebd39f6e8338df2c79d32f0fe2dfdc62f7c051011e7fb4`.
- Experiment JSON SHA-256:
  `6c763c6f8ab87bf5a430a3df18bbdcd55064a590ff3b70a57ef77a262a7f4734`.

## Exact continuation

Objective: close the authoritative order-42 corpus control gate.

Reopen evidence required: acquire unchanged bytes from
`https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6`, or receive an unchanged
file with provenance, at `sources/r55_42some.g6`. Record retrieval timestamp,
final URL, response headers/content type, byte count, and SHA-256. Do not
normalize line endings.

The byte preflight must see all three:

- exactly 47,888 bytes;
- exactly 328 nonblank LF-terminated records;
- SHA-256
  `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.

The digest is a frozen mirror acquisition discriminator. It is not by itself
proof that the mirror equals the maintained authoritative source. If newly
retrieved authoritative bytes differ, preserve them unchanged and seek a
second authoritative retrieval or maintainer confirmation; do not edit the
constant to force a pass.

If and only if the byte preflight matches, run:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-authenticated-corpus-gate \
  --hypothesis "The acquired McKay bytes encode the reported 328 controls and 328 complements" \
  --expected-signal "Two exact checkers report zero forbidden sets on 656 instances; NetworkX signatures, published histogram and degree range, complement, and 656-class canonical gates pass" \
  --timeout 3600 --memory-mb 2048 \
  --source-url https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6 \
  -- python3 scripts/run_corpus_gate.py \
  checkers/checker_a.py checkers/checker_b.c \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json
```

Stop immediately at any source hash, line termination, record count, checker
output, NetworkX signature, forbidden-set identity, edge histogram, degree,
complement, or canonical-label mismatch. Preserve divergent inputs and outputs
unchanged. A pass establishes properties only of the supplied 328 records and
their 328 complements, not completeness of all `(5,5,42)` graphs.

Only after this gate passes should the next source gate attempt unchanged
Springer Supplementary Data 4,
`41467_2018_7327_MOESM6_ESM.txt`. Only after both raw-source gates pass may the
four valid K43 deletions be canonicalized against the supplied 656, followed by
the authenticated six-vertex S4 repair slice or S3 novelty search.

## Tool and role disclosure

GPT-5.6 Sol was principal investigator. Two already-completed GPT-5.6 Terra
memos supplied advisory literature and verification reconnaissance; Sol
verified their hashes and independently audited every relied-on source and
artifact. No new agent was spawned. Deterministic tools used were Python
3.12.3, C/GCC, nauty 2.8.8+ds-5, NetworkX 3.3, curl, SHA-256, Git diagnostics,
the computational-researcher experiment harness, and web search. No SAT solver,
proof assistant, or cloud job was used.
