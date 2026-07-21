# R(5,5) research checkpoint — epoch 9

Recorded: 2026-07-21 04:30 UTC

## Outcome and exact scope

The fixed-background two-released-orbit domain-wall family is now classified
at exact minimum monochromatic-`K5` burden two. For every

```text
d in {1,2,3,4,5,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21},
```

the 43 edges `{u,u+6 mod 43}` and the 43 edges `{u,u+d mod 43}` are free;
the other 19 cyclic-distance orbits equal the publisher matrix with SHA-256
`c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990`.
Both independently derived raw-origin encodings prove that no assignment has
burden at most one. The frozen publisher assignment belongs to every slice and
has exactly two monochromatic `K5`s, so the minimum is exactly two in each
slice.

This is not a statement about arbitrary sets of 86 edges, a third released
orbit, the full 903-edge graph space, or the global value of `R(5,5)`. The
maintained range remains `43 <= R(5,5) <= 46`.

## Why raw-origin multiplicity is essential

For every active five-set/color origin `i` with graph clause `C_i`, the new
encoding emits

```text
C_i OR r_i
```

with a distinct relaxation variable `r_i`, then imposes `sum r_i <= 1`.
Origins are never deduplicated. At distance 1, the publisher seed's two bad
five-sets

```text
{6,12,17,36,42}
{6,12,31,36,42}
```

both reduce to graph clause `(7,37)`. Relaxing unique clauses instead of raw
origins makes the pinned burden-two seed spuriously SAT at bound one; this
unsafe mutation is retained and explicitly detected by the audit.

## Independent encodings

Graph variables are fixed as follows:

```text
1..43   : color of {u,u+6 mod 43}, indexed by u
44..86  : color of {u,u+d mod 43}, indexed by u
```

For a slice with `m` raw origins, relaxation variables are `87..86+m`.
`checkers/two_orbit_burden_a.py` uses Python token parsing, `itertools`
five-set enumeration, and a prefix sequential AMO. The separately written
`checkers/two_orbit_burden_b.c` uses `getline`, five nested loops, independent
orbit indexing, and a suffix sequential AMO. Both have `2m+85` variables and
`4m-4` clauses, but their AMO clauses have opposite direction. Their complete
raw ledgers and origin-to-relaxation maps agree byte-for-byte for all 20
slices. No symmetry break, pin, orbit quotient, or preprocessing occurs in
either production generator.

Every two-orbit ledger, specialized by fixing its second orbit to the
publisher value, reproduces the independently generated one-orbit ledger
byte-for-byte: 215 raw origins. Every new two-orbit ledger also reproduces its
retained burden-zero raw ledger byte-for-byte.

| d | raw origins | variables | clauses |
|---:|---:|---:|---:|
| 1 | 1290 | 2665 | 5156 |
| 2 | 1634 | 3353 | 6532 |
| 3 | 731 | 1547 | 2920 |
| 4 | 2494 | 5073 | 9972 |
| 5 | 1763 | 3611 | 7048 |
| 7 | 1462 | 3009 | 5844 |
| 8 | 1806 | 3697 | 7220 |
| 9 | 2795 | 5675 | 11176 |
| 10 | 1247 | 2579 | 4984 |
| 11 | 2408 | 4901 | 9628 |
| 12 | 3913 | 7911 | 15648 |
| 13 | 1075 | 2235 | 4296 |
| 14 | 1419 | 2923 | 5672 |
| 15 | 1032 | 2149 | 4124 |
| 16 | 774 | 1633 | 3092 |
| 17 | 1548 | 3181 | 6188 |
| 18 | 1032 | 2149 | 4124 |
| 19 | 1118 | 2321 | 4468 |
| 20 | 3311 | 6707 | 13240 |
| 21 | 774 | 1633 | 3092 |

Total raw origins across the 20 slices: 33,626.

## Prerequisite replays

The exact saved prerequisites were replayed before the new encoding was used:

- `.proof-experiments/20260721-040843-0eda2b`: both radius-two
  implementations again agree on all 407,253 scores; return code 0, 72.314 s;
- `.proof-experiments/20260721-040843-9177f0`: the distance-6 slice again has
  minimum burden two and exactly 86 interval optima; return code 0, 14.823 s.

Their input hashes equal the retained source and checker hashes. These replays
do not enlarge the earlier scopes.

## Pilot

Experiment: `.proof-experiments/20260721-041736-6aa1db`

- exact distance-6-only raw ledger: 215 origins;
- byte-identical Python/C ledgers and origin maps;
- both prefix and suffix burden-at-most-one CNFs are UNSAT;
- both DRAT proofs pass freshly compiled `drat-trim`;
- duration 7.259 s; peak child RSS 64,256 KiB, below the predeclared
  120-second/1,024-MiB stop;
- report: `artifacts/two_orbit_burden_one_pilot_report.json`, SHA-256
  `8e6610227477cd6fc1f2433817cc3e3ffd18982bff4c34e2440d5c4641ec237a`.

## Decisive sweep

Experiment: `.proof-experiments/20260721-041804-395e81`

- return code 0; duration 150.328 s; peak child RSS 65,024 KiB;
- experiment JSON SHA-256:
  `f56f9aa873e126f48840e296ae5ac6a92eb4493b71097d84108597c1edf42151`;
- report: `artifacts/two_orbit_burden_one_exact_report.json`, SHA-256
  `993adc7236b0c7a241b9d17457b28e144e745e7c2d890bae17ef9c81dcbf689f`;
- result: no SAT distance; all 20 distances UNSAT in both encodings;
- all 40 binary DRAT proofs pass freshly compiled `drat-trim`;
- complete packet: `artifacts/two_orbit_burden_one/`, 324 files,
  12,807,189 bytes at creation.

The precommitted scheduling order was:

```text
1,12,20,3,16,21,15,18,13,19,10,14,7,17,2,5,8,11,4,9
```

Distances 1, 12, and 20 are the duplicate-origin sentinel and two largest
stress cases; the remainder are ordered by raw-origin count and distance.

## Independent adversarial audit

Experiment: `.proof-experiments/20260721-042400-d28272`

- return code 0; duration 24.719 s; peak child RSS 65,024 KiB;
- experiment JSON SHA-256:
  `b460e787473eef4444b3797e973a00dd3326a5646e6eb3ef0f93af2d2e1be1c6`;
- report: `artifacts/two_orbit_burden_one_adversarial_audit.json`, SHA-256
  `0026e4d53f31b2fb8409bb52a0090035306cd6366e4a59c527bbc35b316167ff`;
- all 40 DRAT proofs were converted to retained textual LRAT and passed the
  separately compiled `lrat-check`;
- every CNF was reparsed and required to equal its raw-origin clauses plus the
  declared prefix or suffix AMO exactly;
- all 20 independent specializations reproduced the 215-origin one-orbit
  ledger;
- all 20 independent patterned assignments agreed with the C full-graph
  clique/complement enumerator; Python full enumeration also agreed for
  distances `1,3,10,12,20,21`;
- SAT/UNSAT AMO semantic controls passed for both encodings at distances
  `1,12,20`;
- reversed-relaxation, omitted-AMO-link, shifted-y-index, source-hash, and
  duplicate-merge mutations were all detected as intended;
- LRAT packet: `artifacts/two_orbit_burden_one_lrat/`, 40 files,
  23,986,952 bytes at creation.

The proof checker sources are pinned to `drat-trim` revision
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985` in
`tools/drat-trim/PROVENANCE.md`.

## Reproduction

The main gate and audit refuse to overwrite evidence. Use fresh output paths.

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-two-orbit-burden-one-replay \
  --hypothesis "At least one fixed-background two-orbit slice has raw burden at most one" \
  --expected-signal "A dual-checked model or 40 checked UNSAT encodings" \
  --timeout 1800 --memory-mb 1024 \
  --source-url 'https://doi.org/10.1038/s41467-018-07327-2' \
  -- python3 scripts/run_two_orbit_burden_one_gate.py \
  checkers/two_orbit_burden_a.py checkers/two_orbit_burden_b.c \
  checkers/publisher_radius1_a.py checkers/publisher_radius1_b.c \
  sources/retrievals/springer_supplementary_data4_audit1.txt \
  sources/retrievals/springer_supplementary_data4_audit2.txt \
  artifacts/two_orbit_slice_exact_report.json \
  artifacts/two_orbit_slice_adversarial_audit.json \
  artifacts/distance6_slice_exact_report.json tools/drat-trim/drat-trim.c \
  artifacts/two_orbit_burden_one.replay \
  artifacts/two_orbit_burden_one_exact_report.replay.json
```

Because solver timings enter the JSON, a replay report need not be byte
identical. Compare every mathematical field and retained file hash before
changing the audit's main-report hash lock. To cold-audit the frozen accepted
packet directly, use:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-two-orbit-burden-one-audit-replay \
  --hypothesis "The frozen exclusion packet survives independent audit" \
  --expected-signal "40 LRAT checks and all semantic/mutation controls pass" \
  --timeout 900 --memory-mb 1024 \
  --source-url 'https://github.com/marijnheule/drat-trim' \
  -- python3 scripts/audit_two_orbit_burden_one.py \
  artifacts/two_orbit_burden_one_exact_report.json \
  artifacts/two_orbit_burden_one \
  sources/retrievals/springer_supplementary_data4_audit1.txt \
  checkers/publisher_radius1_a.py checkers/publisher_radius1_b.c \
  tools/drat-trim/drat-trim.c tools/drat-trim/lrat-check.c \
  artifacts/two_orbit_burden_one_lrat.replay \
  artifacts/two_orbit_burden_one_adversarial_audit.replay.json
```

## Route disposition and exact continuation

`strategy-r55twoorbitdomainwall2026` is exhausted at its declared scope. Do
not release a third orbit merely because it is larger; reopen only upon a
concrete defect in source provenance, raw-origin multiplicity, specialization,
cardinality, graph mapping, proof verification, or distance coverage.

Recommended next strategy: `strategy-r55-novel42`. Run the cheapest exact
feasibility pilot for the recognized almost-regular order-42 slice, where any
valid graph is outside the authenticated supplied 656. First hash-lock
`artifacts/authenticated_corpus_report.json`, extract the supplied corpus's
degree-spread distribution, and validate a degree-spread-at-most-one counter
on small known Ramsey controls before a 300-second/1-GiB proof-logging SAT
pilot. Stop on any corpus, graph6, degree, encoding, proof, or full-scan
mismatch; a timeout is inconclusive.

## Tool and delegate disclosure

GPT-5.6 Sol was principal investigator. Supplied GPT-5.6 Terra
literature-strategy and experiment-verification memos were advisory; their
promoted artifacts and hashes are in `records/delegate-provenance-epoch9.json`.
Sol independently replayed prerequisites, implemented the Python prefix and C
suffix encodings, ran the decisive sweep, wrote and ran the separate audit,
and limited the conclusion to the checked family. Deterministic tools were
Python 3.12.3, GCC 13.3.0, CaDiCaL 1.7.3, pinned `drat-trim` and `lrat-check`,
SHA-256, Git diagnostics, and the computational-researcher experiment harness.
No new subagent, CAS, proof assistant, or external publishing action was used.
