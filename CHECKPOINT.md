# R(5,5) research checkpoint — epoch 3

Recorded: 2026-07-20 21:15 UTC

## Outcome and exact scope

Internal research-software progress only. No new Ramsey bound, witness,
classification, target-instance exclusion, or canonical novelty claim is made.
The maintained rigorous status remains `43 <= R(5,5) <= 46`.

This epoch continued strategy `r55controls2026`. A genuinely new acquisition
path was tested against Hugging Face's Xet-backed mirror object. The bounded
`curl` run returned code 6 after two DNS failures and `--remove-on-error` left
no `sources/r55_42some.g6`. No HTTP response was received, so
`artifacts/mirror_retrieval_headers.txt` is empty. The final hardened source
preflight returned code 2 with `downstream_checks_run: false`. Zero order-42
records were evaluated. Do not begin S3 unknown-42 search, S4 K43 repair, SAT
enumeration, or canonical comparison from the provisional local packet.

The reusable positive result closes a narrower verifier gap. The two custom
parsers and the independent NetworkX parser now expose the complete
upper-triangle adjacency bitstring, rather than only order, edge count, and
ordered degrees. On a 42-vertex record this fingerprint has exactly 861 bits.
The final order-7 regression passed on all 1,044 unlabeled graph classes and
their 1,044 complements. Checker A and Checker B agreed exactly, the full
NetworkX fingerprints agreed, local complement bytes agreed with
`nauty-complg`, and the provisional K43 semantic-mutation and malformed-input
controls still passed. This remains parser/evaluator infrastructure, not
evidence about an order-42 record.

## Current source/status audit

- Dynamic Survey DS1.18 is dated 24 April 2026 and records the 43–46 range:
  https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- McKay's maintained page says the file supplies 328 representatives and the
  other 328 are complements; it does not claim catalogue completeness:
  https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- The browser path confirmed that the maintained ANU object is `text/plain`,
  but did not expose exportable raw bytes.
- Hugging Face's file page advertises 47.9 kB and SHA-256
  `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`:
  https://huggingface.co/datasets/linxy/RamseyGraph/blob/main/data/r55_42some.g6
  This is mirror metadata, not proof of authoritative-source equivalence.

## Decisive experiments

### New-host acquisition discriminator

Experiment: `.proof-experiments/20260720-210542-55792e`

- Return code 6; not timed out; duration 1.027 s; seed 0; 256 MB cap.
- Both attempts failed with `Could not resolve host: huggingface.co`.
- `sources/r55_42some.g6` is absent.
- `artifacts/mirror_retrieval_headers.txt` is empty because no HTTP response
  was received.
- Experiment JSON SHA-256:
  `4a37b050ec37f9513d138253aa380db868e169c4a2fa5e89256b1444a984d29c`.

Do not retry either the ANU or Hugging Face `curl` path in the unchanged command
environment. Reopen only with a new network/export mechanism or an unchanged
externally retrieved file with provenance.

### Final full-adjacency regression

Experiment: `.proof-experiments/20260720-210824-8f13e8`

- Return code 0; duration 1.027 s; seed 0; 1,024 MB cap.
- `nauty-geng` generated one representative of every 1,044 unlabeled simple
  graph class at order 7.
- Checker A (Python/direct combinations) and Checker B (C/recursive bitsets)
  agreed on their entire outputs for all source records and complements.
- NetworkX 3.3 agreed on every complete upper-triangle bitstring, not merely
  order/edge/degree signatures, for all 2,088 records.
- Local complementation was an involution and agreed byte-for-byte with
  `nauty-complg`.
- Order 7 has three graph6 padding bits, as order 42 does.
- Report: `artifacts/graph6_full_fingerprint_report.json`, SHA-256
  `9be4f1dc4257390f324bb7491bba5f282aa76e738c085adf6326448be3b8bd55`.
- The report records final imported corpus-gate SHA-256
  `cec728c0a1a94bea0f81d804d0a865da8c7aaefe1b919f51819d8da7b2c300ff`.
- Experiment JSON SHA-256:
  `92bd0e5ef743beb61196b9c6531972f877ba86a778cf1f557f0be3403eafbc42`.

The earlier epoch-3 run `.proof-experiments/20260720-210522-025825` is
superseded because the final target manifest added adjacency-fingerprint hashes
after that run. Cite only the final regression above.

### Semantic and parser controls

Experiment: `.proof-experiments/20260720-210716-8da301`

- Return code 0; duration 13.891 s; seed 0; 1,024 MB cap.
- Both checkers retained exact agreement on the two provisional K43 matrices.
- Forced clique and independent-set mutations were detected by both checkers.
- Asymmetric, invalid-character, and truncated inputs were rejected by both.
- The two recorded K43 conflicts and four valid 42-vertex deletions were
  unchanged; the local input remains third-party and publisher authentication
  remains false.
- Report: `artifacts/full_fingerprint_semantic_control_report.json`, SHA-256
  `de66b7c663724a66ee98b5ba91f4f21b55f2b5b9118d8016926ad4c6e9e567c7`.
- Experiment JSON SHA-256:
  `58e8fd8619c6c32881af5a21be7f77d81002527a3bf300b8948b0f3675214a2c`.

### Final fail-closed target preflight

Experiment: `.proof-experiments/20260720-210833-0111b6`

- Expected return code 2; duration 0.174 s; seed 0; 256 MB cap.
- Report status is `source_preflight_failed` with
  `downstream_checks_run: false`.
- Report: `artifacts/corpus_source_preflight_epoch3.json`, SHA-256
  `db893987f58b718712ebd39f6e8338df2c79d32f0fe2dfdc62f7c051011e7fb4`.
- Experiment JSON SHA-256:
  `5e276be3963f297e750602ffb013d2d693401e9dd103b9418ec7a24c47b7f0db`.

## Exact continuation

Objective: close the authoritative order-42 corpus control gate.

Do not retry direct `curl` against ANU or Hugging Face in the current command
environment. Acquire unchanged bytes from
`https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6` through a genuinely new
raw-file path, or receive an unchanged file with retrieval provenance, at
`sources/r55_42some.g6`. Record retrieval timestamp, final URL, response
headers/content type, byte count, and SHA-256. Do not normalize line endings.

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
  --expected-signal "Two exact checkers report zero forbidden sets on 656 instances; all three parsers agree on every full 861-bit adjacency fingerprint; published histogram and degree range, complement, and 656-class canonical gates pass" \
  --timeout 3600 --memory-mb 2048 \
  --source-url https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6 \
  -- python3 scripts/run_corpus_gate.py \
  checkers/checker_a.py checkers/checker_b.c \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json
```

Stop immediately at any provenance, source hash, LF termination, record count,
861-bit parser fingerprint, checker output, forbidden-set identity, edge
histogram, degree, complement, or canonical-label mismatch. Preserve divergent
inputs and outputs unchanged. A pass establishes properties only of the
supplied 328 records and their 328 complements, not completeness of all
`(5,5,42)` graphs.

Only after this gate passes should the next source gate attempt unchanged
Springer Supplementary Data 4,
`41467_2018_7327_MOESM6_ESM.txt`. Only after both raw-source gates pass may the
four valid K43 deletions be canonicalized against the supplied 656, followed by
the authenticated six-vertex S4 repair slice or S3 novelty search.

## Delegate provenance and tool disclosure

GPT-5.6 Sol was principal investigator. Two precomputed GPT-5.6 Terra memos
supplied advisory reconnaissance. Sol hash-verified both. Only the
experiment-verification memo supplied a relied requirement; it was promoted
byte-for-byte to
`docs/delegate-memos/20260720-210000-experiment-verification.md`, recorded in
`records/delegate-provenance-epoch3.json`, and independently implemented and
tested by Sol. No new agent was spawned.

Deterministic tools used were Python 3.12.3, C/GCC, nauty 2.8.8+ds-5,
NetworkX 3.3, curl, SHA-256, Git diagnostics, the computational-researcher
experiment harness, and web browsing. No SAT solver, proof assistant, or cloud
job was used.
