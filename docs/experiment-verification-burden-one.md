# Verification memo: two-orbit burden-one closure

**Role and scope.** This is a proposed bounded experiment, not a Ramsey proof or a
global multiplicity claim.  Its only possible conclusion is the exact minimum
monochromatic-`K5` burden in the already-fixed union of the 20 two-orbit
families around the authenticated 43-vertex Springer seed.

## Best live route and cheapest discriminator

Run the 20 existing slices with the predicate *raw monochromatic-`K5` burden
at most one*.  This is the smallest live discriminator because burden zero is
already proof-checked UNSAT in every slice, while the seed supplies burden two
in every slice.  Thus either a checked model is a concrete one-burden result
for a specified slice, or 20 checked UNSAT results establish the exact scoped
minimum two and retire this family.

The relaxation must be per **raw origin**, never per deduplicated DIMACS
clause.  For every origin `i` with signed released-edge clause `C_i`, emit
`C_i OR r_i`; impose `sum r_i <= 1`.  For a fixed edge assignment, exactly
the origins corresponding to monochromatic five-sets have false `C_i`, so the
extension exists exactly when the raw burden is at most one.

This distinction is decisive, not cosmetic.  In retained distance-1 ledger
data the authenticated seed's two bad five-sets
`{6,12,17,36,42}` and `{6,12,31,36,42}` both yield the identical released
clause `(x_6 OR x_36)` (DIMACS literals `(7,37)`).  Deduplicating before
relaxation falsely changes its burden from two to one.

Use a deterministic sequential at-most-one counter, not pairwise clauses.  If
`m` is the raw-origin count, it has `2m+85` variables and `4m-4` clauses
including the `m` relaxed origin clauses (with 86 graph variables).  Across
the retained slices this is 33,626 origins and 134,424 clauses total; the
largest case, distance 12, is 7,911 variables and 15,648 clauses.  Pairwise
AMO alone would add 7,653,828 clauses at distance 12.

## Exact controls before the sweep

1. Hash-lock the two original publisher bodies to
   `c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990`, and
   hash-lock the two retained reports:
   `0456c5764898ab28d248d20912f26fd6708cac5d283151e1673110ce73690627` and
   `38f2b91ca963760dc1fed0107be7fef0c40d41d3fd7da2a7104103447c6b36c8`.
2. Independently regenerate canonical raw-origin ledgers in Python and C:
   `(five-set, target color, signed x/y literals, fixed-edge data)`.  Require
   byte identity before either emits a relaxation CNF.  Record origin index
   to relaxation-variable mapping explicitly.
3. For every second distance, specialize the `y` orbit to its frozen seed
   value *before* the cardinality encoding.  Require exact equality of its
   215 projected raw origins (not merely its 129 unique clauses) with a newly
   generated one-orbit raw ledger.  Then independently rerun the known
   one-orbit `burden <= 1` UNSAT control.
4. Positive semantic control: with `<=2`, the publisher assignment must
   extend with precisely its two raw relaxation variables true, and two full
   graph/complement K5 enumerators must report exactly those two identities.
   With `<=1` and the same graph-edge variables pinned, the instance must be
   UNSAT.  Repeat the test using the distance-1 duplicate-origin example.
5. Mutation controls must fail: merge duplicate origins; reverse one
   relaxation literal; shift a y index; omit an AMO link; and alter the
   source hash.  The duplicate merge is especially important: it should make
   the pinned distance-1 seed spuriously satisfiable, demonstrating that the
   gate detects the intended error.

## Production and independent verification

Retain one unsymmetrized CNF, raw ledger, mapping, solver stdout/stderr,
DRAT, and SHA-256 manifest per distance.  Generate the primary sequential
counter in one implementation and an independently derived cardinality
encoding in the other (the CNFs need not be byte-identical); compare their
raw ledgers and projected one-orbit controls.  Check each UNSAT proof with a
freshly compiled `drat-trim`, convert it to LRAT, and check with independently
compiled `lrat-check`.  For any SAT result, discard all auxiliary variables,
materialize the 43-by-43 matrix, and require exact identity agreement from
the independent Python combinations checker and C clique/complement checker.

## Failure modes and stop rules

Stop the whole pass on the first source hash, raw-origin count, duplicate
multiplicity, specialization, variable-map, AMO, proof, or full-scan
mismatch.  Do not replace a failing implementation silently.  Also stop and
report resource infeasibility if the one-orbit proof pilot exceeds **120 s or
1,024 MiB**; do not launch all 20 with an unmeasured encoding.  Give each
production slice the predeclared hard limit of **600 s and 1,024 MiB**.  A
timeout is an inconclusive bounded result, not an UNSAT result; retain its
partial evidence and park the sweep.

After the pilot, run distance 1 first (the duplicate-origin sentinel), then
12 and 20 (the 3,913- and 3,311-origin stress cases), then the remaining
distances in ascending raw-origin count, breaking ties by distance.  Terminal
states:

- SAT: retain the model and independent full scans; report only a scoped
  burden-one coloring pending principal review.
- 20 LRAT-checked UNSAT instances: record exact minimum two for this fixed
  two-orbit union and park it.  Releasing a third orbit requires a new
  discriminator, not automatic escalation.

## What the Sol principal should reject or verify independently

Reject any result that relaxes unique clauses, quotes only a solver status,
uses symmetry reduction without proof, or reports a total burden without the
raw five-set identity list.  Independently rerun the one-orbit specialization
and the distance-1 duplicate-origin mutation, compile the proof checkers from
the pinned sources, and select at least one UNSAT slice plus every claimed SAT
model for cold replay.  The reusable artifact should be a fail-closed
`run_two_orbit_burden_one_gate` plus a separate semantic/LRAT audit and a
machine-readable per-origin mapping manifest.
