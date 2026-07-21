# Literature-strategy memo — R(5,5), epoch 11 intake

**Scope.** Compact route audit only. This memo makes no witness, catalogue-
completeness, multiplicity-optimum, or Ramsey-bound claim.

## Status and duplication audit

**Sourced fact.** Radziszowski's *Small Ramsey Numbers*, DS1.18 (revision 18,
24 April 2026), still gives `43 <= R(5,5) <= 46`.  It says that the 1997 work
gave *strong evidence* for both `R(5,5)=43` and 656 critical order-42 graphs;
it does not call them complete.  The maintained McKay data page says the same
thing explicitly: its 328 supplied graphs plus complements are 656 examples,
while more order-42 and order-43--47 graphs could exist.  Angeltveit--McKay
arXiv:2409.15709v2 (1 September 2025) remains the current located upper-bound
source and states an independently implemented LP-plus-case-checking proof of
`R(5,5) <= 46`.

- Survey: https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- Data page: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- Upper bound: https://arxiv.org/abs/2409.15709

**Reported computation.** The authenticated supplied corpus contains 656
distinct controls (328 records and complements), each of degree spread three;
it is therefore a valid novelty comparator but not an exhaustive filter.
`artifacts/almost_regular_42_q20_report.json` records the dual-parser degree
gate.  The epoch-10, unsymmetrized degree-{20,21} CNF passed its encoding and
checker controls but CaDiCaL returned `UNKNOWN` at 300 seconds / 1 GiB.  This
is a resource measurement, not an exclusion.

The two-orbit family, radius-one/radius-two seed repairs, the one-orbit slice,
and pure-circulant route are already closed at their declared scopes.  Do not
release a third orbit without a new structural discriminator.  Nor is generic
42/43 local search live until it demonstrates leakage-safe advantage on held-
out damaged controls; historical work already rediscovered the known basin at
great scale.

## Best live route

Run the **symmetry-normalized q=20 almost-regular order-42 SAT pilot**
(`strategy-e81525840a9b`), then stop.  This is a bounded novel-42-basin
discriminator, not an assertion that every Ramsey graph is almost regular.

**Exact rationale (proved coverage lemma).** If an order-42 graph has all
degrees in `{20,21}`, either it has a degree-20 vertex, or it is 21-regular;
in the latter case its complement is 20-regular.  Complement if needed,
choose a degree-20 vertex, label it 0, and label its neighbors `1,...,20`.
Every orbit under complementation and relabelling therefore has a representative
with

```text
x(0,i)=1  for 1 <= i <= 20,
x(0,i)=0  for 21 <= i <= 41.
```

The 41 units meet the recorded reopen condition for the prior q=20 timeout:
they change the exact configuration by a sound, explicit quotient rather than
merely repeating it.  Unlike a broad heuristic branch, a checked model would
also be outside the supplied 656 because those controls all have spread three.
It would still only establish a new supplied-corpus class, not an R(5,5)
advance or a census defect.

## Cheapest discriminator and controls

Extend `checkers/almost_regular_42_cnf.py` with an opt-in, declared
`--fix-root-neighborhood` flag that adds exactly the 41 units above, leaving
all Ramsey and degree clauses unsymmetrized.  Before solving:

1. Regenerate the normalized CNF and a variable-map/unit ledger; independently
   assert the 861 edge-variable indexing and the polarity of every unit.
2. Prove coverage separately from the generator using the argument above; use
   small labelled graph/property tests to ensure relabelling and complementation
   produce the stated root pattern.
3. Re-run the existing degree-counter tests and independent C five-set ledger;
   mutation tests must reject a shifted root edge, a reversed unit, a missing
   root unit, a missing five-set/color clause, and a weakened row bound.
4. If SAT, decode and rescan all `C(42,5)` subsets with both exact checkers,
   verify every degree, canonicalize independently, and compare only against
   the authenticated supplied labels.
5. If UNSAT, retain a completed proof and independently check DRAT plus an
   LRAT conversion/replay.  Solver output alone is not admissible.

Use the same one 300-second / 1-GiB proof-logging pilot, recording solver
version/options and peak RSS.  The measure of success is checked SAT, checked
UNSAT for this normalized q=20 slice, or an informative cost comparison with
the prior unsymmetrized run—not a lower heuristic score.

## Failure modes, artifact, and stop rule

Primary failure modes are silently fixing a vertex without the complementation
case; confusing an orbit representative with a canonical unique representative;
off-by-one or polarity errors in the 41 units; sharing generator/checker logic;
calling timeout or partial DRAT an exclusion; and treating absence from the
656 supplied labels as an exhaustive novelty theorem.

Preserve a reusable normalization packet: source/report hashes, coverage note,
unit/variable map, DIMACS hash, independent clause ledger, mutation outcomes,
solver transcript, any completed proof, decoded model, dual scans, and canonical
comparison.  It can support later q=17--19 bands only after this q=20 cost
measurement; it does not cover the whole almost-regular slice or all order-42
graphs.

Stop immediately on a coverage, mapping, clause, degree, model, or proof
mismatch.  Otherwise stop after one checked SAT/UNSAT result or the fixed
timeout.  Do not run q=17--19, enlarge the degree band, launch K43 extension,
or revive three-orbit search merely because this pilot is inconclusive.

## What Sol should independently verify or reject

Verify DS1.18's table/wording, the q=20 coverage lemma, exact count and
polarity of the 41 units, and semantic equivalence of decoded SAT models.
Independently regenerate at least one Ramsey-clause ledger and the root-unit
ledger, and check any proof with a fresh checker.  Reject claims that the 656
are complete, that this bounded slice determines `R(5,5)`, that UNKNOWN is an
exclusion, or that almost-regularity is a universal premise.
