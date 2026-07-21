# R(5,5) research checkpoint — epoch 15

Recorded: 2026-07-21 16:43 UTC

## Epoch-15 outcome: labelled blocks expose an eight-normal-form bottleneck

The saved `strategy-4c792f58d4a3` discriminator is complete.  It reused the
immutable trial-1 formula for source record 21: a labelled order-30 core is
frozen, 426 incident/internal boundary edges are primary variables, the base
has 155,976 variables and 508,157 clauses, and boundary Hamming distance is at
least 60.  After each verified supplied-corpus model, the incremental solver
received the 426-literal clause falsified by exactly that primary vector.

The crucial scope correction is now enforced in code and documentation: each
clause blocks one labelled assignment, not a nauty isomorphism class.  The
experiment-verification Terra memo also contained a base-hash transcription
error (`...59e28c...`); direct decompression and the retained production
artifact agree on logical SHA-256
`2f1c3b2ac59e4c4b6e2873d2d5ebb2d2eba4fd908a2927f2a30d1936bc3d1072`.

Production reached the exact budget of 64 distinct primary models.  Every
total assignment satisfied the base and all earlier blocks, and both full
graph checkers accepted every decoded graph.  None was outside the supplied
656.  The supplied-class distribution was:

```text
source 12: 13    source 18: 11    source 19: 6
source 20:  8    source 21:  5    source 25: 21
```

Distances were 136--226.  Solver time totaled 300.533 seconds; the recorded
production wall time was 609.167 seconds with 152,472 KiB peak child RSS.
The result does not exclude any isomorphism class or the retained boundary and
does not change a Ramsey bound.

### Cold audit and exact structural diagnostic

The cold checker imports no producer.  It independently reconstructed the
primary map, evaluated 508,157 base clauses per model (32,522,048 total),
checked every ordered block, validated the fixed core and distance, enumerated
maximal cliques in each graph and complement with NetworkX, and checked
NetworkX isomorphism to every nauty-identified target.  All 64 models passed.

All 12 destroyed vertices had distinct 30-bit core-neighborhood rows in every
model.  Sorting those rows therefore gives an exact normal form under the
destroy-label `S_12` action for this sample.  The 64 labelled vectors collapse
to only eight normal forms across the six supplied classes.  This is the
decisive route diagnosis: a larger arbitrary labelled-block cutoff has low
information value.

Retained records and hashes:

```text
production experiment  .proof-experiments/20260721-161659-700d02
production report      8cd3f5b16649f5fab092c5624f345cca9b305e5ac6cac789152677720b6c332e
ordered blocks         067cc2e42bee9fb40325865637621f69724bf40832408295548dff49d1a59fb1
cold experiment        .proof-experiments/20260721-162745-91d1f9
cold report            8c9af0b66c350bfff49b235093f183e037a4a57fc888709af18369bff7f7567c
embedding cost probe   .proof-experiments/20260721-164245-525153
```

The reusable incremental driver is
`tools/novel42_incremental_enumerator.cpp`; the controller and independent
auditor are `scripts/run_novel42_labelled_cegar.py` and
`checkers/novel42_labelled_cegar_audit.py`.  Installing Ubuntu package
`libcadical-dev 1.7.4-1` was the only system change and is recorded in
`docs/system-toolchain-epoch15.md`.

### Exact continuation

Do not continue the same assignment-block loop with a larger budget.  Reopen
it only after a sound class-level block or symmetry quotient is installed.
The next discriminator is a new symmetry-normalized boundary formula:

1. remove the source-specific Hamming condition, because it is not invariant
   under permutations of the 12 destroyed labels;
2. order the destroyed vertices lexicographically by their 30-bit adjacency
   rows into the frozen core;
3. exhaustively verify lex-encoding satisfiability and orbit coverage on small
   frozen-core instances, including tied rows;
4. run one predeclared production first-model gate only if that control passes.

Every boundary completion has a row-sorted representative, so the proposed
quotient is sound.  When rows are distinct it removes the full `12!` destroy
label action; the current packet predicts an observed reduction from 64
vectors to eight normal forms.  Tied rows are the explicit coverage hazard and
must be tested before production.  Stop on a control failure, one dual-checked
supplied-corpus novel graph, or a predeclared normal-form budget.

Full formulation and replay details are in
`docs/novel42-labelled-cegar.md`.

## Epoch-15 disclosure

GPT-5.6 Sol was principal investigator.  The supplied GPT-5.6 Terra
literature-strategy and experiment-verification memos were advisory and were
promoted under `docs/delegate-memos/` with provenance in
`records/delegate-provenance-epoch15.json`.  Sol corrected the labelled/class
scope, audited the base hash, rejected the impractical embedding census as a
precondition, implemented and ran the incremental experiment, and wrote the
independent cold checker.  No new subagent was spawned.  Deterministic tools
were Python 3.12.3, GCC/G++ 13.3.0, CaDiCaL library 1.7.4, nauty `labelg`,
NetworkX 3.3, gzip, SHA-256, and the computational-researcher experiment
harness.  No CAS, proof assistant, external publication, or remote account was
used.

---

# Prior checkpoint — epoch 14

Recorded: 2026-07-21 14:23 UTC

## Epoch-14 outcome: exact boundary repair rediscovered only supplied classes

The Terra archive audit was accepted only as route advice after primary-source
checking.  The 1997 paper defines general identities I2/I3 but applies its
displayed LP to `R(4,6)<=41`; the current `R(5,5)<=46` proof is a different
argument.  The authoritative ANU data page says `r45extreme` contains complete
sets only for the smallest and largest few edge counts, so subset extrema from
that archive cannot provide universal I3 bounds for missing interior layers.
The proposed “published order-45 I2/I3 baseline reconstruction” is therefore
blocked until complete catalogues or proved global feature bounds exist.

The saved live route `strategy-r55-novel42` was tested with one bounded,
predeclared discriminator.  Eight source-side control records

```text
21, 36, 41, 83, 126, 128, 192, 216
```

were selected before solver output by SHA-256 ranking under fingerprint
`r55novel42basin2026`; complement partners were excluded from trial selection.
For each record, a fingerprint-selected set of 12 vertices was destroyed.  All
426 incident/internal edges became SAT variables, the induced order-30 graph
was frozen, exact Ramsey clauses were emitted for all relevant five-sets, and
a Sinz counter forced labelled boundary distance at least 60.  The first valid
model per boundary was the declared novelty discriminator.

All eight formulas were SAT in 5.3--15.3 seconds.  Both the direct Python
five-subset checker and separate C recursive-bitset checker accepted every
decoded graph.  Actual boundary distances were 178--232.  However, nauty
canonical membership and independent NetworkX isomorphism showed that every
candidate was already one of the supplied 656:

```text
source 21  -> source 18       distance 207
source 36  -> source 56       distance 203
source 41  -> complement 101  distance 203
source 83  -> source 220      distance 230
source 126 -> source 185      distance 197
source 128 -> source 1        distance 178
source 192 -> source 194      distance 232
source 216 -> source 217      distance 227
```

This falsifies the supplied-corpus-novel first-model hypothesis over exactly
the eight declared boundaries.  It does not exclude novel solutions within
any boundary and does not make the supplied corpus exhaustive.  The exact
positive, corpus-local fact is that these eight pairs of distinct control
classes share an induced order-30 graph, witnessed by the retained 12-vertex
rewirings.

The cold auditor imports none of the producer.  It uses NetworkX graph6
parsing, maximal-clique enumeration in each graph and complement, NetworkX
isomorphism, and a direct satisfaction scan of all 4,061,806 physical clauses.
It rederived every destroy set, fixed induced graph, and distance and rejected
forced clique/independent-set mutations.  After deterministic gzip storage,
the compression-aware replay emitted a byte-identical report.

Key retained hashes:

```text
production report  3d1377f1df4e19a64933fb0c450eca5fcc1b6e3c8ffabf3ac38d94f0546650bb
cold audit/replay  8e6669dd46361d893900d12b6cec71b7c652aae540e3d216f35128e181c46e31
corpus              067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb
```

The accepted production experiment is
`.proof-experiments/20260721-141324-22844d`; the cold audit is
`.proof-experiments/20260721-141801-cf3c9d`; the compressed replay is
`.proof-experiments/20260721-142133-c076d7`.  The initial preflight
`.proof-experiments/20260721-141228-a33851` failed before SAT because temporary
graph6 records lacked separators and supports no claim.

### Exact continuation

Do not repeat the same one-model-per-boundary portfolio with arbitrary new
seeds.  The next discriminating experiment is canonical CEGAR within one
frozen boundary: solve, dual-check, canonicalize, and whenever the model is a
supplied class, add a blocking clause for that complete labelled boundary
assignment.  Predeclare a model/evaluator budget and stop on a dual-checked
novel class or the exact budget.  An exhaustive boundary exclusion would need
a checked final UNSAT certificate and a verified correspondence for every
block; this packet does not provide one.

Full formulation, replay, limits, and source links are in
`docs/novel42-boundary-repair.md`.

## Epoch-14 disclosure

GPT-5.6 Sol was principal investigator.  The supplied GPT-5.6 Terra
literature-strategy and experiment-verification memos were advisory and are
promoted under `docs/delegate-memos/` with provenance in
`records/delegate-provenance-epoch14.json`.  Sol audited the primary sources,
designed and repaired the harness, ran every experiment, and wrote the cold
auditor.  No new subagent was spawned.  Deterministic tools were Python 3.12.3,
GCC 13.3.0, CaDiCaL 1.7.3, nauty `labelg`, NetworkX, gzip, SHA-256, jq,
pdftotext, and the computational-researcher experiment harness.  No CAS,
numerical optimizer, proof assistant, external publication, or system-level
change was used.

---

# Prior checkpoint — epoch 13

Recorded: 2026-07-21 12:35 UTC

## Epoch-13 outcome: exact null certificate for the uncoloured row-pair LP

The saved `strategy-r55-row-code-sdp` first discriminator is complete and
negative.  The tested model is exactly the uncoloured union-support pair LP:
fixed degree-pair totals, off-diagonal Hamming distances allowed by the union
of the edge and nonedge `R(3,5)=14` bounds, diagonal mass retained explicitly,
and all ordinary binary Krawtchouk inequalities.  It does not retain the edge
colour of a pair, edge-degree marginals, full adjacency symmetry, or triple
moments.

The exact profile counts are:

```text
n=43, degrees 18..24: 6,992,920
n=44, degrees 19..24:   953,580
n=45, degrees 20..24:   106,076
total:                 8,052,576
```

All counts impose both total order and handshake parity.  Applying the
published exact `R(4,5,m)` edge extrema to the doubled `m=2` excess identity
gives a contribution interval that strictly straddles zero at every allowed
degree, so this scalar interval baseline removes zero profiles.

More decisively, every one of the 8,052,576 profiles has an explicit feasible
point in the uncoloured Delsarte LP.  Put every off-diagonal degree-pair mass at
distance 22 when the two degrees have even sum.  For odd sum use distance 21
at order 43 and distance 23 at orders 44 and 45.  Every selected distance lies
in the exact edge/nonedge union support.  If `s` vertices have even degree, the
complete Delsarte sum is

```text
n K_k(0)
+ [s(s-1)+(n-s)(n-s-1)] K_k(h_even)
+ 2s(n-s) K_k(h_odd).
```

The retained integer certificate checks this for every `s=0..n` and
`k=0..n`; the minima for orders 43, 44, and 45 are respectively 1, 0, and 1.
Thus zero profiles are cut, without reliance on a numerical LP solver.

## Controls, repair, and cold audit

Fresh Python and C/bitset graph6 implementations emitted byte-identical
2.8-MiB ledgers (SHA-256
`48df90ead7bfec093a33e14dad2906eb070413c1d4c2cd9d99e6e8ced3c1f9cc`)
for all 328 supplied graphs and their complements.  The controls reproduce 194
degree histograms, off-diagonal distances 12--28, and the sharp counts 12,144
ordered edge pairs with 13 common neighbours and 12,144 ordered nonedge pairs
with 13 common nonneighbours.  The supplied corpus remains SHA-256
`067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.

The first recorded gate `.proof-experiments/20260721-121817-c060be` failed
closed on the complement transformation.  This exposed an endpoint convention
bug in the new ledger only: for arbitrary pairs the number of common
nonneighbours excluding both endpoints is
`n-2-d(u)-d(v)+2*epsilon+c`.  The correction was made in both implementations;
no output from the failed run is evidence.

The accepted gate `.proof-experiments/20260721-122138-bd5745` completed in
29.588 seconds with 42,136 KiB peak child RSS.  Main report
`artifacts/rowpair_v1/rowpair_v1_report.json` has SHA-256
`ef8171abecd9e53ff4915c1e17b594f167829669a02e6fb42e7d0c77ddf14ce3`.
The cold audit `.proof-experiments/20260721-122217-a1e4eb` completed in 5.800
seconds with 54,484 KiB peak child RSS.  It used an integer three-term
Krawtchouk recurrence and dynamic-programming profile counter, exhausted all
33,867 labelled graphs through order 6, and rejected seven mutations.  Cold
report `artifacts/rowpair_v1/rowpair_v1_cold_audit.json` has SHA-256
`35c1135b3b26f68a2281e496cd060029177c3ede53271705988b2858b1aa952d`.

## Route disposition and exact continuation

The hypothesis that the uncoloured pair relaxation cuts a scalar-admissible
profile is falsified over its entire declared domain.  Per the predeclared stop
rule, park `strategy-r55-row-code-sdp` and do not build a custom Terwilliger SDP
from this result.  Reopen the same stage only for an artifact defect.  A
coloured adjacency-aware model is a materially stronger new mechanism, not an
inference from this packet; before receiving compute it must preserve
edge-degree marginals and aggregate common-neighbour identities and identify a
frozen published baseline stronger than the vacuous extremal interval.

The recommended next family is `strategy-r55-inequality`: authenticate the
public edge-extremal `(4,5,n)` archives and determine whether the published
`I2/I3` feature bounds needed for a genuinely stronger order-45 scalar
baseline can be reconstructed.  First fetch and hash the archive index and
`r45extreme.tar.gz`, inspect its exact scope, and stop if the data do not expose
the triangle/pointed features required by `I3` or merely reproduce the already
published extrema.  Do not enumerate 8 million profiles under the vacuous
baseline.

Replay commands and the exact mathematical scope are in `README.md` and
`docs/rowpair-v1.md`.

## Epoch-13 disclosure

GPT-5.6 Sol was principal investigator.  The supplied GPT-5.6 Terra
literature-strategy and experiment-verification memos were advisory; Sol
audited the primary sources, rejected the suggestion that the uncoloured LP
retains edge colour, found and repaired the endpoint off-by-two ledger bug,
derived the central-distance certificate, implemented the producer, and ran
the independent cold checker.  No new subagent was spawned.  Deterministic
tools were Python 3.12.3, GCC 13.3.0 with UndefinedBehaviorSanitizer, exact
Python integers, SHA-256, jq, curl, pdftotext, and the computational-researcher
experiment harness.  No CAS, SAT solver, numerical LP solver, proof assistant,
external publishing action, or system-level change was used.

---

# Prior checkpoint — epoch 12

Recorded: 2026-07-21 10:27 UTC

## Epoch-12 outcome: cube pipeline certified, production discriminator negative

The saved `strategy-596a3981722b` discriminator is complete.  The frozen
fixed-root q=20 parent remained exactly the 71,421-variable,
1,844,093-clause CNF with uncompressed SHA-256
`87b70753dd07b3fc04ddb62799701a8a379efb2cd5c9ea9ddbd026f6679865dd`.
The four declared cross-part edges and independently rederived DIMACS variables
were

```text
(1,21) -> 212, (2,21) -> 213, (2,22) -> 234, (3,22) -> 235.
```

All 16 signed assignments were retained as physical-CNF leaves.  The P5 edge
pattern has 10 classes under path reversal, but this was reported only as a
cost diagnostic: no leaf was quotiented, no isomorphism proof was transported,
and no symmetry inference was used.  The production manifest has SHA-256
`d1d18434b21fbb66d40d936a60084fd5dfaaad5dcf5140f5a17d73871be12180`.
The primary and cold independent manifest audits are byte-identical, SHA-256
`3c72ddc8e307fea078243ba72df74cd321ee930acd6d77020a81d03c4e136eff`.
They reconstruct the full edge map, all suffix signs and hashes, all 120
pairwise disjointness checks, exhaustive coverage, and nine adversarial
mutations without importing the producer.

### Proof-path control and production result

Before production, every one of the 16 analogous normalized `R(3,3,6)` leaves
was physically materialized, solved UNSAT, converted from DRAT to LRAT, and
checked by freshly compiled `lrat-check`.  The cold audit repeated all 16 DRAT
conversions and checked both regenerated and retained LRAT files.

Production then ran all 16 q=20 leaves sequentially with CaDiCaL 1.7.3,
20 seconds per leaf, a 64-MiB proof-file ceiling per leaf, and the experiment
wrapper's enforced 1-GiB memory ceiling.  Every leaf returned `UNKNOWN`:

- 322.789 aggregate solver-seconds; individual wall times 20.115--20.453 s;
- zero decoded SAT models and zero verified UNSAT leaves;
- partial DRAT sizes 7,378,403--8,840,928 bytes, 128,241,561 bytes total;
- deterministic compressed retention 54,025,245 bytes, below the 256-MiB gate.

The main report is `artifacts/q20_cube16_pilot_report.json`, SHA-256
`864f2c67df3e963ba358e1c430880b1f2f39e89508830aca9fdfb06faa427251`.
Experiment `.proof-experiments/20260721-101546-136ce5` completed in 377.962
seconds with 484,396 KiB peak child RSS; its experiment JSON has SHA-256
`0d13b0caa5500d441c145039a95220b97acbba492dbdbadbdd12b2e6dc791444`.

### Cold rejection of every timeout stream

The cold audit rebuilt each 80-MB production leaf from the hashed compressed
parent and its manifest suffix, checked the exact leaf hash, decompressed and
hash-checked the associated stream, and ran freshly compiled `drat-trim`.
All 16 streams were rejected.  Therefore no cube is excluded.  Cold report
`artifacts/q20_cube16_pilot_cold_audit.json` has SHA-256
`7e09c6ef485d05e5de2ff4a858c484289252b83f96969693d7d488ca73ffd812`.
Experiment `.proof-experiments/20260721-102428-af542e` completed in 155.831
seconds with 411,008 KiB peak child RSS; its experiment JSON has SHA-256
`5e1828729ef838804f3b46b018302b0a4fab6b6e9f355f14d4611f1cf2aa88e4`.

This falsifies only the tractable-leaf hypothesis under the exact declared
solver and 20-second budgets.  It does not prove q=20 SAT or UNSAT, does not
cover the q=17--19 bands, and changes no Ramsey bound.  The maintained status
remains `43 <= R(5,5) <= 46`.

## Route disposition and exact continuation

Do not repeat the same four-variable/20-second CaDiCaL configuration, treat
partial proof size as logical progress, increase the cutoff without a
principled cost model, or launch q=17--19 from this negative result.  Reopen
q=20 only with a materially different proof-logging solver or encoding,
justified branching/budget evidence, or a demonstrated parent/cover/audit
defect.

The next recommended family is the saved adjacency-row pair-distance route
`strategy-r55-row-code-sdp`.  First extract exact row-weight,
pair-intersection, and edge/nonedge distance distributions from all 656
authenticated controls, then encode only the rational pair-moment relaxation
for currently admissible n=43--45 profiles.  Stop before a custom SDP if the
pair relaxation cuts no profile beyond the published degree/subgraph
constraints, cuts any known control, or yields a numerical dual that cannot be
rationalized and checked exactly.

## Epoch-12 reproduction and disclosure

Exact replay commands are in `README.md`. GPT-5.6 Sol was principal
investigator. The supplied GPT-5.6 Terra literature-strategy and
experiment-verification memos were advisory and are promoted under
`docs/delegate-memos/` with provenance in
`records/delegate-provenance-epoch12.json`. Sol independently audited the
source status, variables, cover, orbit scope, proof targets, and cold replay.
No new subagent was spawned. Deterministic tools were Python 3.12.3, GCC
13.3.0, CaDiCaL 1.7.3, `drat-trim`, `lrat-check`, the independent C graph
checker, SHA-256, jq, and the computational-researcher experiment harness. Web
access checked DS1.18 and the current Angeltveit--McKay preprint. No CAS, proof
assistant, external publishing action, or system-level change was used.

---

# Prior checkpoint — epoch 11

Recorded: 2026-07-21 08:25 UTC

## Epoch-11 outcome: fixed-root normalization audited, pilot still UNKNOWN

The saved q=20 branch was rerun with the exact proved representative

```text
N(0) = {1,...,20}.
```

This normalization is sound for every order-42 graph whose degrees lie in
`{20,21}`: choose a degree-20 vertex; if none exists, the graph is 21-regular
and its complement is 20-regular; then relabel the chosen root and its
neighbors.  The generator added exactly 41 units and made no other formula
change.  A standalone checker that does not import the generator reconstructed
the edge map and proved byte-for-byte that the new CNF is the retained
unsymmetrized CNF body followed by those units.

CaDiCaL 1.7.3 nevertheless returned `UNKNOWN` after 300.226 seconds.  There is
no model, completed proof, exclusion, or new Ramsey bound.  The maintained
status remains `43 <= R(5,5) <= 46`.

The exact production packet is:

- experiment `.proof-experiments/20260721-081112-052e15`, experiment JSON
  SHA-256 `b5b729e8b9bc3d9fa0d6a24e8ffdfd912dd4240c365120f1b49d338b586969f1`;
- 336.833 seconds total, 524,756 KiB peak child RSS under an enforced 1,024-MiB
  limit;
- 71,421 variables and 1,844,093 clauses: the prior 1,844,052 clauses plus 41
  units;
- uncompressed CNF SHA-256
  `87b70753dd07b3fc04ddb62799701a8a379efb2cd5c9ea9ddbd026f6679865dd`,
  retained gzip SHA-256
  `edc51d7e497a9d6da452800fb5ac09742d1b4db7db516d2ba4c673dda55dbfea`;
- root-unit ledger SHA-256
  `b3b4dfe90f2a1315386893d3ff9197258e046a8fe2372943f93c47253cefe7a6`;
- main report `artifacts/almost_regular_42_q20_normalized_report.json`, SHA-256
  `c0ee1711e81b6db391bf68a517662e55bd7a92dab3cdd2fab6f6e090a46c5a01`.

## Controls and adversarial audit

The independent normalization checker examined all 32,768 labelled
six-vertex graphs.  Exactly 1,760 lie in the `{2,3}` degree band; all admit the
declared representative, including 70 all-3-regular graphs that exercise the
complement case.  It rejected missing, extra, reversed, shifted, and
auxiliary-variable unit mutations.  The normalized `R(3,3,6)` control was
UNSAT with checked DRAT and LRAT.  A separate C nested-loop generator retained
the production Ramsey-clause ledger hash
`c3ed87c4609c629948e6b51715f65fea99efed79af5baacbc96805041e9d1945`.

Cold experiment `.proof-experiments/20260721-081843-52c306` completed in
22.472 seconds (experiment JSON SHA-256
`4db4704037f2bc97c35709e149c0446a0e83ac5c9e370a8a6e57e2d274bfecba`).
It independently replayed the complete formula/unit/mutation audit from the
compressed packet and rebuilt the C ledger.  Freshly compiled `drat-trim`
returned 1 on the 60,558,002-byte interrupted proof stream, SHA-256
`9f62127fecf1f9ebd1b616e4768b7ea20d940da368d59f41c4a2ceca69f22a66`.
The stream is not a certificate.  Cold report
`artifacts/almost_regular_42_q20_normalized_cold_audit.json` has SHA-256
`53b9f0da836d46e869d3c644afce5aff4ca64a8c9e6a3c53e8a5680e0412e626`.

Compared with the unsymmetrized pilot, the normalized run used less peak child
memory (524,756 versus 582,876 KiB) but still exhausted the same solver time.
The larger partial proof stream (60,558,002 versus 35,732,187 bytes) is only a
cost observation, not evidence of greater logical progress.

## Route disposition and exact continuation

Repeating this same fixed-root formula with CaDiCaL 1.7.3 and the same options
and budget is blocked.  Reopen the monolithic configuration only with a
materially different proof-logging solver or encoding, justified additional
resources, or a demonstrated packet defect.  Do not infer anything from the
partial DRAT, and do not launch q=17--19 merely because q=20 remained unknown.

The next cheapest discriminator is a tiny proof-carrying cube pilot.  First
implement a deterministic 16-leaf cover on four declared cross-part edge
variables.  Independently check that the 16 cubes are pairwise disjoint and
exhaust all assignments, and validate the cover plus DRAT/LRAT path on the
normalized `R(3,3,6)` control.  Only then give each production leaf the same
short predeclared limit.  Stop if any cover/proof mapping fails, if no leaf
resolves, or if projected certificate storage is not materially better than
the monolithic packet.  A partial cube set is not an exclusion.

## Epoch-11 reproduction and disclosure

Replay commands are in `README.md`. GPT-5.6 Sol was principal investigator.
The supplied GPT-5.6 Terra literature-strategy and experiment-verification
memos were advisory and are preserved with provenance in
`records/delegate-provenance-epoch11.json`. Sol independently audited their
claims, implemented the generator and independent checker, ran both recorded
experiments, and rejected any inference from `UNKNOWN`. No new subagent was
spawned. Deterministic tools were Python 3.12.3, GCC 13.3.0, NetworkX 3.3,
CaDiCaL 1.7.3, Debian nauty, `drat-trim`, `lrat-check`, SHA-256, and the
computational-researcher experiment harness. No CAS, proof assistant, external
publishing action, or system-level change was used.

---

# Prior checkpoint — epoch 10

Recorded: 2026-07-21 06:30 UTC

## Epoch-10 outcome: exact encoding, inconclusive q=20 pilot

The saved almost-regular lead was operationalized at its cheapest
complement-representative branch. The production formula asks for an order-42
graph with no clique or independent set of order 5 and

```text
d(v) in {20,21} for every vertex v.
```

No symmetry breaking was used. CaDiCaL 1.7.3 returned `UNKNOWN` at its
predeclared 300-second wall-clock limit. Consequently this epoch found no
witness, proved no exclusion, and changed no Ramsey bound. The maintained
status remains `43 <= R(5,5) <= 46`.

The exact cost result is replayable:

- experiment `.proof-experiments/20260721-062032-96649a` returned 0 from the
  orchestrator in 335.330 seconds and used peak child RSS 582,876 KiB;
- the formula has 71,421 variables, comprising 861 edge variables and 70,560
  sequential-counter auxiliaries;
- it has 1,844,052 clauses: both colors for all
  `C(42,5)=850,668` five-sets (1,701,336 clauses) plus 142,716 exact row-bound
  clauses;
- the uncompressed CNF has SHA-256
  `08e7665e8a2da1d03b3e2c52adc182b2eb949081a29646baf622936683ae70be`
  and 80,195,686 bytes; retained `q20.cnf.gz` has SHA-256
  `91cadd86837aa2627c2480ab18d7a9df9e1f1a4688b774e6dea5247c35593d9d`;
- the solver's 35,732,187-byte partial DRAT stream is retained compressed, but
  it is not a certificate and is never evidence of UNSAT;
- main report `artifacts/almost_regular_42_q20_report.json` has SHA-256
  `1c93796ebf27f29d428194d5910ecb2e59e72598d506dc365021ddbdf7ad53fe`.

## Preconditions and controls

The attempted full corpus replay
`.proof-experiments/20260721-060815-084561` timed out at 180 seconds before
output. This is a resource failure only; the previous successful full gate
took 997.687 seconds. The exact preflight needed by this pilot was repaired
with two independent degree parsers while retaining the frozen full-gate
report:

- source `sources/r55_42some.g6` remains SHA-256
  `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`;
- retained full corpus report remains SHA-256
  `0d9b1801434edcc12f34e73cea6c98d911f0e0c6f0884f8f03d96a46eca1344c`;
- a custom byte-level graph6 parser and NetworkX 3.3 agree on every ordered
  degree vector for the 328 records; deriving complements gives 656 controls;
- all 656 have `(minimum degree, maximum degree)=(19,22)`, hence spread 3;
  none is almost regular. This is supplied-corpus control, not completeness.

The degree encoding passed 642 CaDiCaL truth-table cases covering every
1-to-6-bit row and local band. The union-of-bands identity was also checked on
all 33,867 labelled graphs through order 6. Complementation maps the seven
possible order-42 bands as

```text
17 <-> 23, 18 <-> 22, 19 <-> 21, 20 <-> 20,
```

where each number is the lower endpoint `q`. Thus `q=17,18,19,20` represent
the full almost-regular slice, but only `q=20` was attempted.

The same stack generated both colors of every triple for small controls:
`R(3,3,5)` decoded SAT and passed a direct scan, while `R(3,3,6)` was UNSAT
with checked DRAT and LRAT. A separately written C nested-loop generator
reproduced the production Ramsey-clause ledger SHA-256
`c3ed87c4609c629948e6b51715f65fea99efed79af5baacbc96805041e9d1945`.

## Cold adversarial audit

Experiment `.proof-experiments/20260721-062806-06f812` completed in 16.186
seconds. `scripts/audit_almost_regular_42_pilot.py` independently decompressed
and reconstructed formula counts and hashes, reran the C ledger, and sent the
timeout stream to freshly compiled `drat-trim`. `drat-trim` returned 1 and did
not verify it. Audit report `artifacts/almost_regular_42_q20_audit.json` has
SHA-256 `cda1950a6c673a1335ed90ea1f529905ce6d9ae8715bc6adfac75ec9141f33cc`.

## Route disposition and exact continuation

The almost-regular route remains active, but repeating the same unsymmetrized
q=20 formula under the same 300-second CaDiCaL budget is blocked: it would add
no information. Reopen that exact configuration only with a solver or encoding
change, a justified larger budget, or a defect in the retained packet.

The next cheapest discriminator is a sound symmetry-normalized q=20 replay.
For any graph with all degrees in `{20,21}`, either it has a degree-20 vertex,
or its complement has all degrees 20. Relabel a degree-20 vertex to 0 and its
20 neighbors to vertices 1 through 20. Hence every orbit under vertex
relabeling and complementation has a representative satisfying

```text
x_{0,i}=1 for i=1..20; x_{0,i}=0 for i=21..41.
```

Next epoch first action: add exactly these 41 unit clauses as a separately
declared normalization, prove its coverage in the report, rerun the small
controls and formula audit, then give only this normalized q=20 branch one
300-second/1-GiB proof-logging pilot. Stop on any mapping, coverage, model, or
proof mismatch; otherwise stop at checked SAT, checked UNSAT, or timeout. Do
not run q=17..19 or extend to order 43 merely because normalized q=20 is
inconclusive.

## Epoch-10 reproduction and disclosure

The exact production and cold-audit commands are in `README.md`; both require
fresh output paths. GPT-5.6 Sol was principal investigator. Supplied GPT-5.6
Terra literature-strategy and experiment-verification memos were advisory;
their promoted files and hashes are in
`records/delegate-provenance-epoch10.json`. Sol independently checked sources,
selected the corrected one-branch scope, implemented the Python encoding and C
ledger, ran the experiments, and performed the cold audit. No new subagent was
spawned. Deterministic tools were Python 3.12.3, GCC 13.3.0, NetworkX 3.3,
CaDiCaL 1.7.3, Debian nauty, pinned `drat-trim` and `lrat-check`, SHA-256, and
the computational-researcher experiment harness. No CAS, proof assistant, or
external publishing action was used.

---

# Prior checkpoint — epoch 9

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

---

# R(5,5) research checkpoint — epoch 8

Recorded: 2026-07-21 02:22:03 UTC

## Epoch 8 outcome: certified negative, not field progress

An adversarial implementation independently reproduced the authenticated seed, all 903 radius-one
scores, the full 407,253-pair radius-two ledger, both minimizer identities, the strict 403,809-pair
family, the explicit `-27`/`+27` rotations, and the complete distance-six constraint derivation. The
recomputed radius-two ledger is byte-identical to the retained 814,506-byte ledger. Malformed-input,
forced-clique, forced-coclique, ordering-boundary, and 12 deterministic random-pair controls passed.

The one-orbit optimum classification is now certificate-backed rather than only implementation-backed:

- deterministic direct-cardinality CNFs prove burdens 0 and 1 UNSAT;
- independent CaDiCaL enumeration found exactly the retained 86 burden-two words;
- exhaustive Python and C++ full-graph checkers validated every word;
- a 25 MB CNF plus checked DRAT proof excludes every 87th burden-at-most-two word.

The planned 20-family two-orbit sweep is complete. For every `d in {1,...,21} \ {6}`, the family
`F_{6,d}` varies exactly distances 6 and `d`, freezing the other 19 cyclic-distance orbits. Every
family has exact minimum burden 2. Equality always freezes distance `d` to its Springer color, so the
complete minima are exactly the same 86 distance-six interval words: two common-rotation and two
graph-isomorphism classes. No second orbit creates a new minimum class.

The retained packet contains 60 two-orbit DRAT proofs (burden 0, burden 1, and burden 2 with the second
orbit changed for each family), all checked by drat-trim, plus 60 independent unsymmetrized Z3
pseudo-Boolean decisions. Raw active-five-set counts range from 731 to 3,913; unique raw clauses from
258 to 1,763; deterministic primal min-fill width upper bounds from 37 to 58.

This fails the explicit field-progress gate: no K43 witness, no lower conflict count, no concise human
structural proof, no material accepted global search-space reduction, and no held-out search-algorithm
improvement. Classify it as a **verified negative experiment plus certificate-carrying infrastructure
result**. The Ramsey bound remains `43 <= R(5,5) <= 46`, and global order-43 multiplicity is unproved.

Close the one- and two-orbit witness route. Do not launch all 190 three-orbit families by default. The
next discriminator is proof-core compression: seek deletion-minimal unsymmetrized raw-clause cores of
at most 20 clauses that collapse to at most five parameterized obstruction types. Stop if either
threshold fails, then redirect to the leakage-safe held-out algorithm benchmark.

Decisive experiments:

- `.proof-experiments/20260721-022123-71d7c4` — final source/radius-one/radius-two/constraint audit;
- `.proof-experiments/20260721-020646-b4834f` — independent one-orbit CNF/DRAT classification;
- `.proof-experiments/20260721-020930-8c427b` — certified 20-family two-orbit sweep.

Primary adjudication: `docs/FIELD_PROGRESS_AUDIT.md` and
`artifacts/field_progress_gate_report.json`.

## Retained epoch 7 outcome and exact scope

Springer Supplementary Data 4 is now authenticated as the published
two-conflict K43 seed, and its complete Hamming-radius-1 edge neighborhood is
exhausted through radius 2.  The seed's only two radius-2 minimizers are
isomorphic translations of the seed, and the complete 43-bit cyclic-distance-6
slice containing it is exactly classified. These are reproducible local and
structured-slice results, not a Ramsey witness, bound, global multiplicity
optimum, or order-42 census. The maintained published status remains
`43 <= R(5,5) <= 46`.

For exactly the frozen 43-vertex matrix with SHA-256
`c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990`:

- it has 454 one-edges;
- its only monochromatic K5s are the all-zero sets
  `[6,12,17,36,42]` and `[6,12,31,36,42]`;
- all 903 one-edge flips have total monochromatic-K5 burden at least 2;
- the two global radius-1 minimizers are flips `(6,12)` and `(36,42)`,
  both with burden 2;
- among the 861 flips not incident to vertex 6, the unique minimum is
  `(36,42)` with burden 2;
- among all 741 flips avoiding every shared conflict vertex
  `{6,12,36,42}`, the exact minimum is 3, attained by
  `(0,37)`, `(5,11)`, `(10,16)`, `(16,22)`, `(21,27)`, `(26,32)`, and
  `(32,38)`.
- all `C(903,2)=407253` distinct two-edge flips have burden at least 2;
- exactly two radius-2 pairs attain 2:
  `{(6,12),(9,15)}` and `{(33,39),(36,42)}`;
- the 403,809-pair deletion-remainder-change slice also has minimum 2 at
  exactly those two pairs.

The last predicate is a strict non-star firewall: its changed edge remains in
the graph after deleting any of the four shared conflict vertices. It therefore
changes every relevant order-42 deletion remainder, though it says nothing
about larger edit sets or unknown order-42 components.

## Source and provenance gate

Primary article: https://doi.org/10.1038/s41467-018-07327-2

Publisher object:
https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt

Two direct retrievals are retained as
`sources/retrievals/springer_supplementary_data4_audit{1,2}.{txt,headers}`.
Both bodies are 3,812 bytes and byte-identical. Each retrieval record reports
HTTP/2 200, verified TLS, no redirect, the publisher-controlled effective URL,
`Content-Type: application/octet-stream`, and the correct byte count:

- `.proof-experiments/20260720-235158-0cfef1`;
- `.proof-experiments/20260720-235208-a7e84e`.

The gate hash-links both bodies, both raw header captures, both curl transfer
records, and both experiment JSON files. It refuses a changed body even if the
changed matrix remains structurally valid.

## Decisive experiment

Experiment: `.proof-experiments/20260721-000810-1f70a4`

- Return code 0; duration 45.243 s; 1,024 MB cap; peak child RSS 34,560 KiB.
- Experiment JSON SHA-256:
  `3ce459a1a214f1c86dcc9351e4cabbae961a210785cab8e576c78c2f0dc8f98f`.
- Report: `artifacts/publisher_seed_radius1_report.json`, 1,544,868 bytes,
  SHA-256
  `0db3cca75888b70850b60e1b891d8e08349ab0bec6196cd8f4c528603fa04fe9`.
- The report retains the ordered 903-entry flip ledger, full violation
  identities, family histograms, minimizer identities, provenance, mutations,
  parser rejections, deletion membership, checker/compiler hashes, and 41
  direct rescans.

Checker A (`checkers/publisher_radius1_a.py`, SHA-256
`f34ea148c36ab74b0c11784f9b4d333dc915ef0a6bd3d70c7ef9c2aa03f5a535`)
independently parses the raw whitespace in Python, scans all `C(43,5)` subsets,
and derives exact one-edge deltas. Checker B
(`checkers/publisher_radius1_b.c`, SHA-256
`b1bfd2a51511ae0f3e6caccbaa29235cf65df2f8a3cae7ccdfce934af1f5914a`)
parses fixed raw byte positions in C and recursively enumerates K5s in the graph
and complement afresh after every flip. Their complete identity ledgers agree.

The report additionally rescans every family minimizer and one representative
of every global burden class with both full evaluators. Forced clique and
coclique mutations are detected. Both parsers reject nonbinary, shortened,
nonzero-diagonal, asymmetric, and substituted-Gist inputs. A UBSan build of
Checker B also reproduced the retained 903-entry ledger with no diagnostic:
`.proof-experiments/20260721-001630-5af604`, experiment JSON SHA-256
`2d22200322a85d0874f75253e86be41eda5500c1bfc7a57f1f4ea8f648a07032`.

An attempted combined ASan+UBSan replay under the harness's 1,024 MB
`RLIMIT_AS` aborted before evaluation because ASan requires a much larger
virtual shadow reservation. The captured failure is
`.proof-experiments/20260721-001555-dfd5af`, experiment JSON SHA-256
`969331a4fdfc9d8083fb545888d5093b42f6fdb9451c0ca465a13491dd16c6a8`.
The durable repair is the UBSan-only audit above; the ASan failure is not a
checker failure and is not counted as validation.

An initial development version of Checker A failed the cross-check because its
delta ledger omitted seed conflicts unaffected by the changed edge. That result
was discarded, the recurrence was corrected, and the official experiment was
run only after complete identity agreement. This failure is preserved here to
prevent reintroducing the defect.

## Complete radius 2

Experiment: `.proof-experiments/20260721-005729-caca87`

- Return code 0; duration 39.595 s; peak child RSS 124,698,624 bytes.
- Report: `artifacts/publisher_seed_radius2_report.json`, SHA-256
  `ee32f396c898894d32ffcbe69987caded6731f32398ce3be28cfde1d1b9c107a`.
- Compact complete score ledger:
  `artifacts/publisher_seed_radius2_scores.u16le`, 814,506 bytes, SHA-256
  `60ba5158f8d7579785e026a9f00f0722a61fb8d47ed4d279ae128c419c524edb`.

Checker A scans all `C(43,5)` five-sets once and applies exact two-edit
contribution cases. Checker B toggles each pair in C and recursively enumerates
K5s in the graph and complement afresh. They agree entry-for-entry on all
407,253 burdens and on every minimizer identity. Eight independently selected
pairs were also rescanned for full identities.

The only radius-2 minimizers merely relocate the two conflicts:

- `{(6,12),(9,15)}` leaves zero K5s `[4,9,15,22,28]` and
  `[9,15,22,28,33]`;
- `{(33,39),(36,42)}` leaves zero K5s `[1,20,26,33,39]` and
  `[15,20,26,33,39]`.

Nauty canonical labels and explicit NetworkX mappings show that these are the
seed relabeled by vertex rotations `u -> u-27` and `u -> u+27` modulo 43,
respectively. Thus radius 2 exposes no new burden-2 isomorphism class.

## Exact distance-6 slice classification

Experiment: `.proof-experiments/20260721-010952-d08716`

- Return code 0; duration 10.882 s; peak child RSS 66,306,048 bytes.
- Report: `artifacts/distance6_slice_exact_report.json`, SHA-256
  `8c8c64a82c84913222578fad537cc9beb73e74de5260a84090b9406f798a9fb1`.

Twenty of the seed's 21 cyclic-distance edge orbits are constant. The sole
exception is distance 6. If `x_u` colors edge `{u,u+6 mod 43}` and coordinates
are changed to `u=27t mod 43`, every potentially monochromatic K5 in this
43-variable slice reduces to translations of only three constraint shapes:

```text
x_t or x_(t+18)                 (multiplicity 2)
x_t or x_(t+20)                 (multiplicity 2)
not x_t or not x_(t+5) or not x_(t+24)  (multiplicity 1)
```

There are 215 active five-sets and 129 unique constraints. An independent
Python/Z3 pseudo-Boolean enumeration and a custom C relaxation-case DPLL agree
that burdens 0 and 1 are UNSAT, burden 2 is attainable, and there are exactly
86 optima. They are precisely:

- 43 rotations of one step-27 cyclic interval of 24 ones;
- 43 rotations of one step-27 cyclic interval of 25 ones.

The publisher seed is one length-24 interval. Its distance-6 word is
`0111000111001110011100011100111001110001110` in vertex order and
`0000001111111111111111111111110000000000000` in step-27 order. Six full
graph/complement K5 rescans agree with the reduced burdens. This exhausts all
`2^43` assignments in this one-orbit ansatz, not the whole graph space.

## Deletion and novelty firewall

The two conflicts intersect in `{6,12,36,42}`. Deleting any member yields a
valid order-42 graph because the seed's complete violation list contains only
those two sets. `nauty-labelg` places all four deletions in the authenticated
supplied-656 packet:

- delete 6 or 42: canonical SHA-256
  `ee2269437c3ba4cd8cde512768489089a5865ab701b38e8716acaddcdd07c3a7`,
  complement of supplied record 42;
- delete 12 or 36: canonical SHA-256
  `3f16d9a422f89c250bebd7d50fa6cb4006de0655513bac24f34232d2620c623f`,
  complement of supplied record 256.

This is membership in the supplied 656 only. It does not prove completeness.
Ordinary star-only extension from these deletions remains historically
saturated and should not be reopened.

## Cold replay

From the repository root:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-publisher-seed-radius1-replay \
  --hypothesis "The retained authenticated publisher seed has no radius-1 witness and its strict avoid-intersection slice has minimum burden 3" \
  --expected-signal "Byte/provenance/mutation gates pass and both exact implementations reproduce all 903 identities, global minimum 2, and strict 741-flip minimum 3" \
  --timeout 240 --memory-mb 1024 \
  --source-url 'https://doi.org/10.1038/s41467-018-07327-2' \
  --source-url 'https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt' \
  -- python3 scripts/run_publisher_radius1_gate.py \
  checkers/publisher_radius1_a.py checkers/publisher_radius1_b.c \
  sources/retrievals/springer_supplementary_data4_audit1.txt \
  sources/retrievals/springer_supplementary_data4_audit2.txt \
  artifacts/authenticated_corpus_report.json \
  artifacts/publisher_seed_radius1_report.replay.json
```

Require the replay report's mathematical fields to equal the retained report;
the report hash itself may differ because absolute temporary compiler paths or
tool metadata can change only if the script is later revised. Stop immediately
on any source, parser, mutation, canonical, or ledger mismatch.

## Exact continuation

Continue the conflict-core route as a cyclic-domain-wall CSP rather than an
unstructured Hamming-ball search. The first discriminator is the 20-slice
sweep obtained by releasing distance 6 together with exactly one of the other
20 cyclic-distance orbits, leaving the remaining 19 orbits frozen.

For each 86-variable slice:

1. derive every active K5 clause directly from the frozen matrix;
2. symmetry-break the common vertex-rotation action without excluding an
   orbit of assignments;
3. ask first for burden 0, then minimum burden only when the SAT question is
   resolved;
4. decode every SAT model to a 43-vertex matrix and require both complete K5
   checkers before retaining it;
5. treat an UNSAT response as a search discriminator unless a deterministic
   CNF and independently checked proof log are retained.

Rank second orbits by achieved exact burden and by factor-graph width. The
prediction is concrete: if the one-dimensional defect must escape by coupling
to another orbit, at least one two-orbit slice should beat burden 2 or expose a
small recurrent obstruction suitable for a transfer-matrix or trapping-set
lemma. If all 20 slices have certified minimum 2 and only symmetry copies,
close this near-circulant family and redirect compute to multi-orbit/nonlocal
surgery. Do not launch all `C(903,3)` flips first; radius 2 already shows that
the apparent local moves only translate the domain wall.

## Tool and delegate disclosure

GPT-5.6 Sol performed the epoch-7 local work without spawning a subagent. It
implemented both radius-2 evaluators, the exact slice encodings, the custom C
DPLL, the fail-closed gates, direct rescans, and the cyclic/isomorphism
analysis. Earlier epoch-6 delegate memos remain advisory provenance only.

Deterministic tools added in this epoch: Python 3.14.6, C/Apple Clang 17,
Z3 4.15.4, remote Debian nauty `labelg`, NetworkX explicit isomorphism maps,
SHA-256, Git diagnostics, and the computational-researcher experiment harness.
Z3 and the custom DPLL independently enumerated the complete optimum model set;
no global Ramsey SAT/UNSAT claim, CAS result, or proof-assistant theorem was
made.
