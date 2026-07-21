# Verification memo — two-orbit domain-wall burden-zero sweep

**Scope:** design and verification plan only.  The proposed sweep is a finite
near-circulant family around the authenticated K43 seed; it cannot establish a
global Ramsey bound from an UNSAT result.

## Best live route and rationale

Run the 20 **unsymmetrized burden-zero** SAT instances obtained by freeing the
43 distance-6 edges and the 43 edges at exactly one other cyclic distance
`d in {1,...,21} minus {6}`.  All remaining distance orbits stay equal to the
publisher seed.  This is the cheapest live discriminator because radius two
and the whole one-orbit slice are already closed at burden two, while a
two-orbit zero would be an immediately checkable concrete object.  It tests
the specific domain-wall prediction before spending on radius three, MaxSAT,
or unstructured search.

The retained prerequisites are sound on this checkout: the publisher bodies
both hash to `c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990`;
the radius-two report hashes to
`ee32f396c898894d32ffcbe69987caded6731f32398ce3be28cfde1d1b9c107a`; and a fresh
replay of `run_distance6_slice_gate.py` passed.  Its report differs in
environment paths but its source hash, reduced constraint family, exact
result, and direct rescans match `artifacts/distance6_slice_exact_report.json`.

## Exact cheapest discriminator

For slice `d`, introduce variables `x_u = color({u,u+6})` and
`y_u = color({u,u+d})` for `u in Z_43` (the unordered-edge convention is
`{u,u+d mod 43}`).  Enumerate every `5`-subset and both target colors directly
from the frozen 43-by-43 matrix.

For a color `c`, retain a clause only if all nonvariable edges of that
5-subset have color `c`; the clause says that at least one variable edge has
color `1-c`.  A fixed edge of the other color discards that color's candidate.
Do not assume a fixed edge exists: assert and record the count of all-variable
5-subsets separately.  Emit (i) a canonical DIMACS CNF of the **unique**
clauses, and (ii) a provenance ledger retaining every originating five-set,
target color, variable-edge list, fixed-edge list, and multiplicity.

Ask only whether this CNF is satisfiable.  Do **not** add a rotation break to
this first pass: 86 variables and 20 instances are small relative to the
cost and risk of proving a lex-leader encoding.  Common rotation quotienting
is useful later for model enumeration, not for the decisive zero test.

Process slices in a pre-pass order determined by the independently derived
number of unique clauses and variable-incidence/factor-graph width; record the
order before solving.  This is a scheduling choice, not data-dependent
pruning.  All 20 must eventually be run unless a gate failure stops the pass.

## Exact controls and independent verification

1. **Two source-to-CNF derivations.** Implement a transparent Python
   combinations enumerator and a separate C nested-loop/bitset enumerator.
   They may share only the raw publisher bytes and a written variable schema,
   not a normalized matrix or edge-to-variable helper.  Compare sorted
   five-set provenance ledgers, unique signed-clause multisets, multiplicities,
   and DIMACS SHA-256 for every `d`.
2. **Specialisation control for every slice.** Set every `y_u` to the frozen
   seed color at distance `d` (constant zero or one).  The resulting weighted
   `x`-constraint ledger must equal the retained distance-6 ledger exactly:
   215 active five-sets, 86 positive pairs of multiplicity two, and 43
   negative triples of multiplicity one.  Then rerun the established
   one-orbit check: burden 0 and 1 are UNSAT and the 86 burden-2 models remain.
   This catches wrong distance orientation, off-by-one indexing, and silent
   omission of fixed clauses for *each* second orbit.
3. **Raw-matrix controls.** Decode the specialised publisher assignment and
   independently recover exactly the two retained zero-K5 identities and no
   one-K5.  For every SAT result, decode the full matrix and require both
   existing full K5 checkers (`publisher_radius1_a.py --seed-only` and a
   freshly compiled `publisher_radius1_b.c --seed-only`) to report empty
   all-zero and all-one identity lists.  Do not accept the reduced CNF model
   itself as the witness check.
4. **Semantic mutations.** Both generators must reject nonbinary,
   asymmetric, shortened, nonzero-diagonal, and changed-hash inputs.  Add one
   generator-only mapping mutation (shift the declared `y` edge index) and
   require the cross-generator ledger comparison to fail.  Add a matrix
   mutation that forces a known monochromatic K5 and require full checkers to
   detect it.  These test the gate, rather than merely exercising parsers.
5. **UNSAT evidence.** Retain CNF, provenance ledger, solver command/version,
   stdout, and proof.  CaDiCaL is locally available and supports a proof
   positional output plus `--lrat`; use an unpreprocessed/recorded mode and
   validate a toy CNF first.  A reproducible checker repair was tested in a
   temporary directory: `git clone --depth 1 https://github.com/marijnheule/drat-trim.git`,
   revision `2e3b2dc0ecf938addbd779d42877b6ed69d9a985`, builds `lrat-check`
   (the local `drat-trim` binary SHA-256 was
   `92f0aa9575ed519d66a99b8b1b3dde6ece4618ae4c202a3a4b200265dda0aa7a`).
   Pin source and build hashes in the retained packet; independently check
   every proof.  Until then, UNSAT is a useful discriminator only.

## Stop conditions and failure modes

Stop immediately, preserve the divergent files, and do not solve later slices
on: changed publisher bytes; a radius-two/one-orbit replay failure; source-CNF
ledger mismatch; failed specialisation; mutation accepted; a DIMACS header or
hash mismatch; a SAT model failing either full checker; or a proof rejected by
the independent checker.

The principal errors are correlated reduced-clause code, treating duplicate
clauses as a multiplicity-free burden calculation, mixing `d` with `43-d`,
wrong circular edge ownership, an unsound rotation lex-leader, solver
preprocessing whose proof does not match the archived CNF, and promoting 20
slice exclusions to a statement about all 903 edges.  The plan avoids the
symmetry error by using no symmetry reduction in its first decision pass.

## Reusable artifact and Sol review

Retain `two_orbit_slice_manifest.json`, 20 CNFs, both complete clause ledgers,
their hashes, SAT models or checked proof logs, parser/mutation outcomes, full
K5 rescans, and a replay driver that refuses a changed source hash.  A SAT
model is the only outcome that warrants immediate deeper verification; it is
not a result announcement by itself.  If all 20 are checked UNSAT, conclude
only that this fixed-other-orbits two-orbit family is empty and park it before
multi-orbit work.

Sol should reject any run that (a) starts from the previous one-orbit reduced
normal form rather than deriving clauses afresh for each `d`, (b) uses a
rotation break without an explicit orbit-coverage proof, (c) accepts a solver
status without a full-matrix rescan for SAT or a checked proof for an exclusion,
or (d) calls the supplied 656 controls complete or the finite sweep a Ramsey
bound.
