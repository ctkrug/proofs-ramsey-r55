# Exact 12-vertex boundary repair benchmark at order 42

Recorded: 2026-07-21 UTC

## Question and exact scope

The maintained status remains `43 <= R(5,5) <= 46`.  The authoritative data
page says that `r55_42some.g6` supplies 328 order-42 graphs and their 328
complements, while explicitly allowing that more order-42 graphs may exist.
This experiment asks a deliberately smaller question:

> For any of eight predeclared source-side controls, does the first exact SAT
> repair of a fingerprint-selected 12-vertex boundary, constrained to labelled
> Hamming distance at least 60, produce a valid order-42 graph outside all 656
> supplied isomorphism classes?

For a destroy set `S` of size 12, all 426 edges meeting `S` are variables and
the induced graph on the other 30 vertices is frozen.  The CNF contains the
two Ramsey clauses for every relevant five-set, simplified by frozen edges,
plus a Sinz sequential counter forcing at most 366 of the 426 boundary edges
to retain their source values.  This is a one-model-per-boundary discovery
benchmark.  It is not an exhaustive classification of a boundary and does not
assert historical novelty beyond the supplied packet.

The eight source records, selected before solver output by SHA-256 ranking
under fingerprint `r55novel42basin2026`, are

```text
21, 36, 41, 83, 126, 128, 192, 216.
```

Complement partners were excluded from trial selection and used only in the
656-class novelty gate.

## Result

All eight CNFs were SAT within 5.3--15.3 seconds and all eight decoded graphs
passed both full forbidden-five-set checkers.  The labelled boundary distances
were 178--232, far above the required 60.  Nevertheless, every candidate was
one of the supplied classes:

| source record | reached supplied class | boundary distance |
|---:|:---|---:|
| 21 | source 18 | 207 |
| 36 | source 56 | 203 |
| 41 | complement 101 | 203 |
| 83 | source 220 | 230 |
| 126 | source 185 | 197 |
| 128 | source 1 | 178 |
| 192 | source 194 | 232 |
| 216 | source 217 | 227 |

Thus the discovery hypothesis failed over the eight declared first models.
The positive structural observation is exact but corpus-local: there are eight
explicit pairs of distinct supplied classes in which one contains an induced
order-30 graph isomorphic to the fingerprint-selected induced order-30 graph
of the other.  The retained candidate graph6 files witness the corresponding
12-vertex rewirings.

## Independent audit

The producer used Python, CaDiCaL 1.7.3, nauty `labelg`, the direct Python
five-subset checker, and the separate C recursive-bitset checker.  A cold
auditor imports none of the producer and instead uses NetworkX's graph6 parser,
maximal-clique enumeration in the graph and complement, NetworkX isomorphism
to the manifest target, and direct evaluation of every physical DIMACS clause
under the retained total model.

The cold audit checked 4,061,806 clauses across the eight CNFs, found clique
number four in every graph and complement, rederived all destroy sets and
distances, confirmed all frozen order-30 induced graphs, and rejected forced
clique and forced-independent-set mutations.  After deterministic compression
of the CNFs and model logs, the compression-aware replay emitted a byte-exact
copy of the original audit report.

Key hashes:

```text
authenticated corpus:
  067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb
production report:
  3d1377f1df4e19a64933fb0c450eca5fcc1b6e3c8ffabf3ac38d94f0546650bb
cold audit and compressed replay:
  8e6669dd46361d893900d12b6cec71b7c652aae540e3d216f35128e181c46e31
compressed storage manifest:
  b34a85d95a8b1537b7579d3708269180080c76df24444f8ade4212636528dfbb
```

The initial experiment `.proof-experiments/20260721-141228-a33851` failed
closed before SAT because a temporary control file omitted record separators.
It supports no claim.  The accepted production record is
`.proof-experiments/20260721-141324-22844d`; the independent audit is
`.proof-experiments/20260721-141801-cf3c9d`; and the compressed cold replay is
`.proof-experiments/20260721-142133-c076d7`.

## Replay

Fresh production requires fresh output paths because the producer refuses to
overwrite a packet:

```bash
python3 scripts/run_novel42_boundary_repair.py \
  sources/r55_42some.g6 \
  artifacts/authenticated_corpus_report.json \
  checkers/checker_a.py checkers/checker_b.c \
  artifacts/novel42_boundary_repair.replay \
  artifacts/novel42_boundary_repair_report.replay.json 30
```

Replay the retained compressed packet independently with:

```bash
python3 checkers/novel42_boundary_audit.py \
  sources/r55_42some.g6 \
  artifacts/authenticated_corpus_report.json \
  artifacts/novel42_boundary_repair_report.json \
  artifacts/novel42_boundary_repair \
  artifacts/novel42_boundary_repair_cold_audit.replay2.json
```

## Route disposition

Do not repeat this one-model-per-boundary portfolio with more arbitrary seeds.
The next informative test is boundary-local canonical CEGAR: after each valid
model canonicalizes to a supplied class, add a blocking constraint for that
labelled boundary assignment and continue within the same frozen boundary.
Predeclare a model budget and require either a dual-checked novel class or an
honest count of distinct known-class rediscoveries.  An exhaustive boundary
claim would additionally require checked UNSAT after all relevant assignments
are blocked; this packet supplies no such exclusion.

Sources:

- https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- https://doi.org/10.1002/jgt.70029
