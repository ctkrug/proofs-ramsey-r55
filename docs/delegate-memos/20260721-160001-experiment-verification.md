# Terra experiment-verification memo — epoch 15

## Best live route

Run a **labelled-model CEGAR** pass on retained trial 1 (source record 21),
not a fresh first-model SAT run.  Keep its frozen labelled induced graph on
the 30 nondestroyed vertices, its 426 primary boundary-edge variables, all
Ramsey clauses, and the Hamming-distance-at-least-60 condition.  After every
SAT model that passes both full graph checkers and canonicalizes to a supplied
control, append the one 426-literal clause that forbids that exact primary
edge vector.  Continue to a predeclared maximum of 64 verified models.

This is a proposed finite discriminator, not an existence claim, a
classification, or a Ramsey bound.  The trial-1 base formula is already
available as logical SHA-256
`2f1c3b2ac59e28c4b6e2873d2d5ebb2d2eba4fd908a2927f2a30d1936bc3d1072`
(155,976 variables; 508,157 clauses).  Its first model was SAT in 9.86 s,
valid under Python and C scans, and isomorphic to supplied source record 18;
the cold audit additionally checked full DIMACS satisfaction, NetworkX
maximal cliques, and fixed-core equality.  Thus the experiment changes the
admissible model set in response to the observed, measured failure mode:
first models rediscover supplied classes.

## Exact discriminator and controls

For a model with primary values `b_e`, append

```text
OR_e (not x_e if b_e=1, else x_e).
```

This blocks precisely that labelled completion regardless of values of the
155,550 cardinality auxiliaries.  Before the next solve, independently
evaluate every retained block against the old primary vector (false) and the
new vector (true); after SAT, require direct DIMACS evaluation of the base
formula plus every prior block.

Required gates per accepted model:

- hash-gate the 328-record corpus at
  `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`;
  rederive record 21 and its 12-vertex destroy set from the fingerprint;
- reproduce the fixed induced 30-vertex graph and Hamming distance at least
  60; no degree statistic substitutes for either check;
- run `checker_a.py` (all five-subsets) and independently compiled
  `checker_b.c` (recursive bitset scans in graph and complement);
- canonicalize with `nauty-labelg`, then check membership in all 656 supplied
  canonical labels; have the cold auditor independently use NetworkX graph6,
  maximal-clique, isomorphism, and DIMACS paths;
- record model, canonical label, primary-vector hash, ordered block hash,
  wall time, solver seed/version, and logical CNF hash.  Retain every model,
  including known rediscoveries.

First run an exact *embedding census* for this frozen core: determine which
supplied controls admit it as an induced labelled 30-core and count compatible
labelled completions when feasible.  It is an interpretability control, not a
prerequisite for the labelled run.  If it does not yield a compact,
independently checked all-embedding block, do not call the CEGAR clauses
class blocks.

## Failure modes to attack

The chief semantic trap is terminology.  A 426-literal clause excludes one
labelled boundary vector, **not** its nauty isomorphism class.  A compatible
core embedding can still leave up to `12! = 479,001,600` assignments of the
destroyed labels before automorphism coincidences.  Therefore 64 blocks do
not exhaust even one supplied class, much less the boundary family.

Other stop-on-failure conditions are: incomplete/malformed SAT output;
checker disagreement; canonicalization disagreement; failed block or DIMACS
evaluation; corpus/source hash drift; solver `UNKNOWN`; or solver `UNSAT`
without a completed independently checked proof.  An unproved UNSAT result
is only a solver observation.  Never silently replace a failed model by a
restart or adapt the selected boundary/model budget.

## Search-efficiency pass

The fixed-core decomposition is the only already justified large reduction:
it freezes `C(30,2)=435` of `C(42,2)=861` edges, leaving 426 (49.48% fewer
primary edge variables), and skips `C(30,5)=142,506` of 850,668 five-sets
(16.75%), leaving the recorded 708,162 touched five-sets.  The 64 blocks add
at most 64 long clauses, negligible beside the base formula.  Reuse the
generated five-set clause body, fixed-core embedding census, canonical-label
table, and control hashes; batch independent boundaries only after the
single-boundary result is closed.

Use an incremental SAT API if it appends only audited primary blocks while
preserving a hashable base formula and solver-state provenance; otherwise
write physical round CNFs.  Do not reuse learned clauses across distinct
boundaries.  Bitset/delta logic may prefilter but cannot replace full scans.
No symmetry quotient is safe unless an explicit source-and-destroy-set
stabilizer proof preserves the frozen labelled formula; many supplied
controls have trivial automorphism group.

The current cardinality encoding represents at most 366 matching edges and
uses 155,550 auxiliaries.  A separately implemented direct sequential
encoding of `sum(diff)>=60` can require at most `425*60=25,500` counter
auxiliaries, reducing that component by 83.6%.  It is only a proposed
compression: exhaustively compare it with the retained match-bound encoding
on small instances and mutation-test thresholds 59/60/61 before production.

## Stop condition and independent review

Stop on (1) a dual-checked valid model whose canonical label is absent from
the supplied 656, (2) 64 verified labelled rediscoveries, or (3) any failure
above.  Outcome (1) is only “absent from the supplied corpus,” not historically
new or a 43-vertex candidate.  Outcome (2) is a negative rediscovery-rate
measurement, not an exclusion.  The Sol principal should independently verify
the block polarity/primary-variable mapping, the small-case cardinality
equivalence gate, and the labelled-versus-class distinction, and reject any
claim that the 656 supplied controls are exhaustive or that an unproved
UNSAT conclusion excludes the retained boundary.
