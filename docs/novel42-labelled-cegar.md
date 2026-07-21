# Labelled-model CEGAR on one frozen order-42 boundary

Recorded: 2026-07-21 UTC

## Exact question and terminology

The maintained bound remains `43 <= R(5,5) <= 46`.  This experiment did not
search order 43.  It reused the epoch-14 trial-1 boundary at order 42: source
record 21, destroy vertices

```text
2, 3, 10, 12, 14, 25, 27, 30, 36, 37, 38, 41
```

(zero based), and the other 30 labelled vertices frozen.  The 426 edges
meeting the destroy set are primary SAT variables.  The immutable base CNF
has 155,976 variables and 508,157 clauses, including the retained constraint
that the boundary differs from source record 21 in at least 60 positions.

After a verified supplied-corpus model with primary vector `b`, the solver
received exactly

```text
OR_e (not x_e if b_e = 1, else x_e).
```

This 426-literal clause blocks one labelled vector.  It does **not** block an
isomorphism class.  Nauty canonicalization was an acceptance test after SAT,
not a source of clauses.

## Search-efficiency pass

The naive full labelled graph has 861 edge bits.  Freezing the induced
30-vertex core fixes 435 of them (50.52%) and leaves 426.  It also skips the
142,506 five-sets wholly inside the core.  The remaining logical boundary
space is still at most `2^426`; no claim of exhausting it is made.

The production run linked against the CaDiCaL 1.7.4 library.  It parsed the
508,157-clause base once, retained learned clauses between solves, and added
only one audited primary block per verified known model.  The retained base
is 12,866,534 logical bytes and 2,623,295 gzip bytes.  One base plus all 64
blocks and compact total-model bitsets occupies about 4.0 MB of file content;
64 separate compressed base copies alone would occupy about 168 MB.

An all-control induced-core census was considered but not made a prerequisite.
Naively it requires `C(42,12) = 11,058,116,888` deleted subsets per control,
and a recorded NetworkX exact probe took 10.631 seconds on one negative control,
already more than a typical SAT model.  It yielded no compact representation
that could turn labelled blocks into class blocks.  The experiment therefore
retained the honest labelled scope.  The probe is
`.proof-experiments/20260721-164245-525153` and its exact two-host report has
SHA-256 `1c303c9ecbd282442b6285f0a7136b17424f8c7f0b8552d1b741dfedec44b219`.

## Result

The exact budget of 64 models was reached.  All primary vectors were distinct;
all total assignments satisfied the immutable base and all earlier blocks;
and every decoded graph passed both full forbidden-five-set checkers.  None
was absent from the supplied 656 canonical classes.

| supplied target | models |
|:--|--:|
| source record 12 | 13 |
| source record 18 | 11 |
| source record 19 | 6 |
| source record 20 | 8 |
| source record 21 | 5 |
| source record 25 | 21 |

Boundary Hamming distances were 136--226.  Solver time totaled 300.533 seconds
(0.0106--55.0435 seconds per model); the recorded production wall time was
609.167 seconds and peak child RSS was 152,472 KiB.  The outcome is a negative
rediscovery-rate measurement, not a boundary exclusion and not a changed
Ramsey bound.

The retained witnesses do establish the small corpus-local fact that the
frozen labelled order-30 core from source record 21 has compatible completions
in at least the six supplied classes listed above.  This is not a complete
embedding census.

## Independent audit and symmetry diagnostic

The cold auditor imports no producer.  It independently reconstructed the
primary edge order, evaluated all 508,157 base clauses for each model
(32,522,048 clause evaluations), checked every earlier block, reconstructed
the graph, verified the fixed core and distance, computed clique numbers in
the graph and complement with NetworkX, and checked NetworkX isomorphism to
each nauty-identified supplied target.  It also verified that model 1
falsifies its own block and model 2 satisfies block 1.

All 64 candidates had distinct 30-bit core-neighborhood rows on the 12
destroyed vertices.  Therefore sorting those rows gives a canonical
representative under the destroy-label `S_12` action for every retained model.
The 64 labelled vectors collapsed to only eight such normal forms.  This is a
measured 8-fold redundancy in this sample and motivates the next discriminator;
it is not an extrapolation to the full boundary.

Key artifacts:

```text
production experiment: .proof-experiments/20260721-161659-700d02
production report:     8cd3f5b16649f5fab092c5624f345cca9b305e5ac6cac789152677720b6c332e
ordered blocks:        067cc2e42bee9fb40325865637621f69724bf40832408295548dff49d1a59fb1
cold experiment:       .proof-experiments/20260721-162745-91d1f9
cold report:           8c9af0b66c350bfff49b235093f183e037a4a57fc888709af18369bff7f7567c
base logical CNF:       2f1c3b2ac59e4c4b6e2873d2d5ebb2d2eba4fd908a2927f2a30d1936bc3d1072
authenticated corpus:  067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb
```

The supplied experiment-verification memo transcribed the base hash with
`...59e28c...`; direct decompression, the epoch-14 report, and this run agree
on `...59e4c...`.  No claim relies on the memo transcription.

## Route disposition and continuation

Do not extend the same labelled-block loop with a larger arbitrary budget.
In this exact sample, 64 assignment blocks bought only eight destroy-permutation
normal forms and six supplied classes.  Reopen it only with a proved class-level
block or a sound symmetry quotient.

The cheapest next discriminator is a new symmetry-normalized boundary formula:
remove the source-specific Hamming constraint and impose lexicographically
nondecreasing 30-bit core-neighborhood rows on the 12 destroyed vertices.
Every completion has such a representative by sorting the destroyed labels;
when rows are distinct this quotients the full `12!` action.  Before production,
exhaustively test the lex encoding and orbit coverage on small frozen-core
instances, including tied-row cases.  Then run one predeclared first-model
gate and compare its supplied-class and normal-form redundancy with this
packet.  The source Hamming condition must not silently remain, because it is
not invariant under destroy-label permutations.

Sources:

- https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- https://doi.org/10.1002/jgt.70029
