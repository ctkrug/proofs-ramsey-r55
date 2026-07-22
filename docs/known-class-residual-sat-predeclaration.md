# Post-census known-class residual SAT predeclaration

Date: 2026-07-21

Status: implementation ready; execution forbidden until the resumed census has all
656 canonical host rows and its standalone validation receipt passes.

## Falsifiable discriminator

Freeze the induced order-30 core obtained from source record 21 by removing
vertices `{2,3,10,12,14,25,27,30,36,37,38,41}`. Rebuild every raw `K_5` and
independent-`K_5` clause whose truth can depend on one of the 426 remaining
boundary edges. Quotient the `S_12` action on the removed labels by requiring
their 30-bit core-neighborhood rows to be lexicographically nondecreasing,
using exact prefix-equality comparators.

The complete independently validated census supplies exact 426-bit vectors.
Take the sorted set union over all 656 host artifacts and append one long
primary-variable clause per unique vector. Each clause blocks exactly one
labelled row-lex boundary assignment. Then run one CaDiCaL solve with seed 1,
a predeclared wall limit no greater than 3,600 seconds, a 2 GiB address-space
limit, proof logging, and a dynamic proof-file limit no larger than 6 GiB. The
dynamic limit preserves the engine's 8 GiB root-disk reserve plus 512 MiB for
the CNF, logs, and receipts; hitting the limit is `UNKNOWN`, not `UNSAT`.
Production and cold DRAT checks each have a 7,200-second wall limit, 2 GiB
address-space limit, and 64 MiB log limit. A checker timeout is incomplete and
cannot validate an UNSAT verdict.

The initial pilot admits at most 10,000 globally unique blocks. Crossing that
gate stops before CNF construction for a streaming or cube-design review; it
does not silently omit vectors or solve a partial block set. The rejected v1
49-host calibration prefix contained eight unique vectors, so this is a
generous resource guard rather than a final-census projection.

## Preconditions and fail-closed gates

- The census receipt says `status=valid`, `hosts=656`, the exact manifest hash,
  the frozen 254-row v2 prefix hash, and the explicit mixed gate schedule: hosts
  0–253 at 30 seconds and hosts 254–655 at 60 seconds.
- Manifest rows are exactly hosts `0..655`, in source-then-complement order.
- Every gzip host artifact matches its manifest hash. Its custom-bitset and
  NetworkX summaries agree, and its sorted unique-vector stream matches the
  declared count and SHA-256.
- Every admitted vector is exactly 426 binary digits. No partial census, stale
  receipt, summary-only row, malformed vector, or mismatched artifact reaches
  the SAT formula.
- A global union above 10,000 vectors pauses for redesign and is inconclusive.
- The cold auditor imports no producer or census-enumerator code. It reruns a
  fresh NetworkX induced-subgraph enumeration on every host, regenerates every
  tied-row permutation exactly and duplicate-free, and then independently
  repeats the census union, raw Ramsey encoding, lex encoding, block
  construction, and physical DIMACS comparison. Its per-host coverage pass has
  an input/code-bound durable checkpoint and resumes after interruption.

## Decision rule and certificate

- `SAT`: preserve the total model and graph6 candidate; directly evaluate all
  physical clauses and row order; require agreement from the Python exhaustive
  checker and separate compiled C checker; canonicalize with nauty against the
  supplied 656. The cold auditor repeats a direct five-subset scan and nauty
  classification. A member is `sat_known_control`, a failed discriminator; only
  a nonmember is `sat_corpus_novel_candidate`. Corpus nonmembership is still
  only a candidate, not a novelty claim, until literature/expert review.
- `UNSAT`: preserve the CNF and DRAT proof; require production and cold
  drat-trim verification. This classifies only the record-21 frozen-core
  `S_12` row-lex quotient after blocking the complete census vectors.
- `UNKNOWN`: timeout, resource exhaustion, failed/incomplete proof checking, or
  unexpected solver termination is inconclusive. Preserve logs and any partial
  proof, but make no mathematical claim and do not repeat with arbitrary seeds.

The experiment does not classify all order-42 Ramsey graphs, does not prove a
new Ramsey bound, and does not establish global novelty from a finite supplied
corpus comparison.

## Exact command template

```text
python3 scripts/run_known_class_residual_sat.py \
  artifacts/known-class-embedding-census-v3/output/manifest.jsonl \
  artifacts/known-class-embedding-census-v3/validation.json \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json \
  checkers/checker_a.py checkers/checker_b.c \
  .venv/sat-audit-tools/cadical/build/cadical \
  .venv/sat-audit-tools/drat-trim/drat-trim \
  artifacts/known-class-residual-sat/output \
  artifacts/known-class-residual-sat/report.json 900 1
```

The cold-audit command is recorded alongside the completed packet. Exact code,
input, tool, CNF, proof/model, output, and report hashes must be added to the
experiment lifecycle receipt before validation or promotion.

The requested output path is the first immutable attempt. If it or its report
already exists after an interruption, the same command allocates a new sibling
such as `output.attempt-0001` and `report.attempt-0001.json`; it never overwrites
the partial attempt. Each attempt writes a durable `attempt-state.json` running
event and atomically replaces it with a completed event after the report is
durable. The printed JSON identifies the actual retry paths. The cold audit's
coverage checkpoint is similarly bound to the manifest, validation receipt,
corpus, and exact auditor hash.

```text
python3 checkers/known_class_residual_sat_audit.py \
  artifacts/known-class-embedding-census-v3/output/manifest.jsonl \
  artifacts/known-class-embedding-census-v3/validation.json \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json \
  artifacts/known-class-residual-sat/output \
  artifacts/known-class-residual-sat/report.json \
  .venv/sat-audit-tools/drat-trim/drat-trim \
  artifacts/known-class-residual-sat/cold-audit.json
```
