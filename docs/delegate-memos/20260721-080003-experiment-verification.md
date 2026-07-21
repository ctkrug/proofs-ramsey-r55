# Experiment-verification memo — R(5,5), epoch 11 intake

**Scope.** Design and audit plan only.  This memo makes no witness,
catalogue-completeness, multiplicity, or Ramsey-bound claim.

## Best live route

Run exactly one **symmetry-normalized `q=20` order-42 SAT pilot**
(`strategy-e81525840a9b`).  The preceding unsymmetrized formula and its
encoding controls are sound as far as their declared tests show, but CaDiCaL
1.7.3 returned `UNKNOWN` after 300 seconds / 1 GiB.  Repeating that unchanged
configuration is ruled out.  Adding a proven complement-and-relabel quotient
changes the search space without changing the represented orbit set.

**Coverage lemma (proved).** For a graph on 42 vertices whose degrees are all
in `{20,21}`, either some vertex has degree 20, or all vertices have degree
21 and complementation makes every degree 20.  Choose a degree-20 vertex,
rename it 0, and rename its 20 neighbours `1,...,20`.  Complementation and
renaming preserve the two Ramsey prohibitions.  Thus every orbit under these
actions has a representative satisfying

```text
x(0,i) = 1  for 1 <= i <= 20
x(0,i) = 0  for 21 <= i <= 41.
```

This is coverage, not a claim that the representative is unique or canonical.

## Cheapest decisive experiment

Add an opt-in `--fix-root-neighborhood` generator flag.  It must append those
41 units to the existing fully unsymmetrized degree-`{20,21}` formula; do not
simplify counters, add a lex-leader, pre-process, or free another band.  The
expected DIMACS dimensions are **71,421 variables and 1,844,093 clauses**
(the old 1,844,052 plus 41).  The 1,701,336 Ramsey clauses and their C-derived
ledger hash `c3ed87c...e9d1945` must be unchanged.

Run one CaDiCaL 1.7.3 proof-logging invocation with the existing `-q -t 300`
settings, 1-GiB harness limit, and 512-MiB proof-file limit.  Record wall time,
peak RSS, exit code, stdout/stderr, full command, solver binary/version hashes,
and every output hash.  It is a cost discriminator: checked SAT, checked
UNSAT for only this quotient slice, or a bounded timeout.  It is not a global
R(5,5) experiment.

## Exact controls and independent verification

1. **Unit ledger.** A separate, tiny auditor (not importing the generator)
   must recompute the map `edge_var(0,i)=i(i-1)/2+1`, expect positives for
   `i=1..20` and negatives for `i=21..41`, and require 41 distinct primary
   variables.  The generator summary should declare flag, root, neighbor set,
   non-neighbor set, clause count, and unit-ledger SHA-256.
2. **Coverage control.** Retain the written lemma above and exhaust every
   labelled six-vertex graph of degree band `{2,3}`: each accepted graph or
   its complement must admit a relabelling with root 0 and neighbours `{1,2}`.
   This catches the complement direction and root-pattern convention; it is a
   semantic control, not a proof by finite analogy.
3. **Formula identity.** Independently count header/clauses, require the old
   Ramsey prefix byte-for-byte, and compare the old CNF to the new CNF after
   removing precisely the 41 declared unit lines.  Re-run the existing C
   five-set ledger and row-counter truth table.
4. **Mutations.** Fail closed on a missing unit, an extra unit, any reversed
   unit, a shifted root variable, a unit on an auxiliary variable, a missing
   five-set/color clause, or a weakened degree bound.
5. **Small proof path.** Run the normalized flag on the analogous `R(3,3,6)`
   control (with its appropriate self-complementary degree band) and retain a
   DRAT-to-LRAT check.  The current `R(3,3)` control does not exercise root
   units, so it is insufficient alone.
6. **SAT disposition.** Decode all 861 edge bits; Python direct enumeration
   and the independent C recursive-bitset checker must both find no forbidden
   five-set and agree on all degrees.  The root units must be checked directly.
   Canonicalize with nauty and compare only with the authenticated *supplied*
   656 labels; absence there is supplied-corpus novelty, not a census claim.
7. **UNSAT disposition.** Preserve complete DRAT, convert/check LRAT with
   freshly built tools, and cold-replay the formula/proof packet.  A timeout
   stream or a DRAT check failure is never an exclusion.

## Likely failure modes

- Omitting the all-21-regular complement case makes symmetry breaking
  incomplete; treating the root pattern as unique overstates what was proved.
- A wrong graph6/DIMACS edge order or polarity can fix a different star.
- Solver propagation may gain little because counters remain syntactically
  present; `UNKNOWN` is an expected honest result, not grounds to broaden the
  run.
- The old cold-audit script hard-locks the old report/hash and assumes no
  units, so it cannot audit this result unchanged.  Create a new normalized
  audit rather than weakening that historic audit.
- Shared `edge_var` code between generator and auditor can mask one common
  error.  The unit auditor must use its own arithmetic loop.

## Reusable artifact and stop rule

Preserve a normalization packet: source/report hashes, coverage note and
six-vertex transcript, independent unit ledger, base/new DIMACS relation,
mutation outcomes, solver transcript/resources, proof or model, dual scans,
and canonical-comparison output.  It is reusable for q=17--19 only after this
cost measurement; it does not cover them now.

Stop immediately on coverage, unit-map, formula-identity, decoded-model, or
proof mismatch.  Otherwise stop after one checked SAT result, one checked
UNSAT result, or the fixed 300-second timeout.  Reject any proposal to run
q=17--19, order 43, a third cyclic orbit, or an extra solver budget merely
because this bounded run is inconclusive.

## What Sol should independently verify

Independently rederive the coverage lemma; recalculate all 41 literals and the
`+41` clause count; confirm that the new formula is exactly base plus units;
and cold-check any model/proof.  Reject claims that unknown is exclusion, that
the supplied 656 are complete, or that a q=20 result settles the whole
almost-regular or R(5,5) problem.
