# R(5,5) research checkpoint — epoch 8

Recorded: 2026-07-21 02:25:45 UTC

## Outcome and exact scope

The complete burden-zero union of the authenticated Springer seed's 20
two-released-cyclic-orbit slices is excluded with archived, independently
checked proofs. For each

```text
d in {1,2,3,4,5,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21},
```

the 43 edges `{u,u+6 mod 43}` and the 43 edges `{u,u+d mod 43}` are free; the
other 19 cyclic-distance orbits equal the publisher matrix with SHA-256
`c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990`.
Every resulting unsymmetrized 86-variable burden-zero CNF is UNSAT.

This is not a 43-vertex witness, a statement about arbitrary 86 edges, a
minimum-burden classification, an upper bound, or a change to the maintained
published range `43 <= R(5,5) <= 46`.

## Prerequisite replays

Both saved epoch-7 gates were replayed before deriving the new family:

- `.proof-experiments/20260721-020906-1ea617`: all 407,253 radius-two scores
  again agree between the independent implementations; return code 0;
- `.proof-experiments/20260721-020906-332091`: the distance-6 slice again has
  minimum burden 2 and exactly 86 interval optima; return code 0.

The replay source hashes equal the retained hashes. These replays do not enlarge
their previously recorded scopes.

## Exact encoding and derivation

For each five-set and target color `c`, a clause is retained exactly when every
fixed edge of the five-set has color `c`. Its literals require at least one free
edge to have color `1-c`. All-variable five-sets are handled explicitly (there
were none in these 20 slices). The DIMACS contains sorted unique clauses because
multiplicity is irrelevant to burden zero; a complete origin ledger retains
every five-set, target color, fixed edge, literal list, and duplicate.

Variable IDs are fixed as follows:

```text
1..43   : color of {u,u+6 mod 43}, indexed by u
44..86  : color of {u,u+d mod 43}, indexed by u
```

No symmetry break, bit pinning, orbit quotient, or preprocessing step was used
in the generator.

`checkers/two_orbit_slice_a.py` independently tokenizes the raw source and uses
Python combinations. `checkers/two_orbit_slice_b.c` reparses with `getline`,
uses five nested loops, separately implements undirected orbit indexing, and
deduplicates with `qsort`. For every distance their complete origin ledgers and
CNFs agree byte-for-byte.

Specializing the second orbit to its constant publisher value reproduces the
retained distance-6 constraint Counter exactly for every distance: 215 raw
origins, 129 unique clauses, including multiplicities 2 on the 86 positive
pairs and 1 on the 43 negative triples.

## Decisive sweep

Experiment: `.proof-experiments/20260721-021702-129660`

- return code 0; duration 125.005 s; 1,024 MB cap; peak child RSS 64,256 KiB;
- experiment JSON SHA-256:
  `58ea5e5ed83621756e8bfa9a10438a19d2cb39c4dfe5478a79bf059979f08b46`;
- report: `artifacts/two_orbit_slice_exact_report.json`, SHA-256
  `0456c5764898ab28d248d20912f26fd6708cac5d283151e1673110ce73690627`;
- complete packet: `artifacts/two_orbit_slices/`, 220 files, 5,952,393 bytes;
- result: no SAT distance; all 20 distances UNSAT;
- all 20 archived binary DRAT proofs pass independently compiled `drat-trim`.

The precommitted scheduling order, determined only by unique-clause and raw
origin counts before solving, was:

```text
3,13,21,19,18,8,7,2,14,16,9,15,1,10,17,5,11,12,4,20
```

Per-slice sizes and proof bytes:

| d | unique clauses | raw origins | DRAT bytes |
|---:|---:|---:|---:|
| 1 | 688 | 1290 | 357 |
| 2 | 473 | 1634 | 793 |
| 3 | 258 | 731 | 362 |
| 4 | 1591 | 2494 | 9913 |
| 5 | 946 | 1763 | 5424 |
| 7 | 473 | 1462 | 2244 |
| 8 | 430 | 1806 | 1143 |
| 9 | 602 | 2795 | 1143 |
| 10 | 731 | 1247 | 1929 |
| 11 | 1161 | 2408 | 6844 |
| 12 | 1505 | 3913 | 1161 |
| 13 | 344 | 1075 | 2221 |
| 14 | 516 | 1419 | 575 |
| 15 | 645 | 1032 | 2955 |
| 16 | 602 | 774 | 2499 |
| 17 | 903 | 1548 | 139 |
| 18 | 430 | 1032 | 2476 |
| 19 | 387 | 1118 | 2829 |
| 20 | 1763 | 3311 | 10828 |
| 21 | 387 | 774 | 139 |

## Adversarial audit

Experiment: `.proof-experiments/20260721-022215-e19ede`

- return code 0; duration 11.68 s; peak child RSS 64,256 KiB;
- experiment JSON SHA-256:
  `437ed626de65c0386eb46f58f8faff5134ab6247c001dec337463fdd03a3cbe2`;
- report: `artifacts/two_orbit_slice_adversarial_audit.json`, SHA-256
  `38f2b91ca963760dc1fed0107be7fef0c40d41d3fd7da2a7104103447c6b36c8`;
- all 20 DRAT proofs were converted to retained textual LRAT and separately
  checked by `lrat-check`; all passed;
- every ledger was evaluated on the publisher assignment and a fixed arithmetic
  86-bit pattern, materialized as a full 43-by-43 graph, and compared with the C
  graph/complement K5 enumerator; exact identity lists agree for all 20;
- the independent Python full K5 enumerator also agrees for distances
  `1,3,10,20,21`;
- parser rejection, source hash, a shifted-y-index mutation, and complete
  20-distance coverage checks passed.

The LRAT checker sources are from
<https://github.com/marijnheule/drat-trim>, pinned at revision
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`. Source provenance is retained in
`tools/drat-trim/PROVENANCE.md`.

## Cold replay

Use fresh output paths because both gates refuse to overwrite evidence:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-two-orbit-domain-wall-replay \
  --hypothesis "At least one exact two-orbit slice contains a burden-zero coloring" \
  --expected-signal "Dual derivations agree and every SAT model or UNSAT proof passes its independent checker" \
  --timeout 900 --memory-mb 1024 \
  --source-url 'https://doi.org/10.1038/s41467-018-07327-2' \
  -- python3 scripts/run_two_orbit_slice_gate.py \
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

Then change the main-report hash constant in the audit only if the replay report
differs solely in recorded environment paths/timings, or audit the retained
packet directly with the existing command in
`.proof-experiments/20260721-022215-e19ede/experiment.json`. Never bypass the
hash check merely to make a replay pass.

## Exact continuation

The witness question is closed for this 20-slice family. The remaining
information-rich discriminator is whether any slice has monochromatic-K5 burden
one. The publisher assignment proves every slice has burden at most two, so a
proof-checked `burden <= 1` exclusion for all 20 would establish exact minimum
two throughout the family and close the domain-wall route completely.

First action:

1. add one relaxation variable per raw five-set origin, not per deduplicated
   clause;
2. add an independently derived at-most-one constraint;
3. validate the encoding on the retained one-orbit slice, where burden 0 and 1
   are already independently UNSAT;
4. run the 20 slices without symmetry reduction;
5. decode any SAT result to the full matrix and require both full K5 checkers;
   for UNSAT retain and check DRAT and LRAT.

Stop immediately on a source, multiplicity, specialisation, dual-CNF, proof, or
full-scan mismatch. If all 20 burden-one instances are checked UNSAT, record
minimum burden exactly two and park this family; do not release a third orbit
without a new structural or core-based discriminator.

## Tool and delegate disclosure

GPT-5.6 Sol was principal investigator. The supplied GPT-5.6 Terra
literature-strategy and experiment-verification memos were advisory only and
are hash-linked in `records/delegate-provenance-epoch8.json`. Sol independently
replayed the prerequisites, implemented both generators and both audits, and
ran every decisive command. Deterministic tools were Python 3.12.3, GCC 13.3.0,
CaDiCaL 1.7.3, pinned `drat-trim` and `lrat-check`, SHA-256, Git diagnostics,
and the computational-researcher experiment harness. No new subagent, CAS, or
proof assistant was used.
