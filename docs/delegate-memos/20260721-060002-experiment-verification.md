# Experiment-verification memo — R(5,5), epoch 10 intake

**Scope.** Reconnaissance and experiment design only.  Nothing here is a
witness, an exclusion beyond a named encoded branch, a classification, or a
Ramsey-bound claim.

## Best live route and rationale

Use the **almost-regular order-42 feasibility pilot** in
`strategy-33eb5acd3b31` / `strategy-r55-novel42`.  The fixed-background
two-orbit family is already exhausted; releasing a third orbit has no recorded
reopen condition or cost discriminator.  The authenticated 42-vertex corpus
is adequate as a *novelty control*, but not as a claimed census.

The direct premise is checkable: `sources/r55_42some.g6` has SHA-256
`067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`, and
`artifacts/authenticated_corpus_report.json` has SHA-256
`0d9b1801434edcc12f34e73cea6c98d911f0e0c6f0884f8f03d96a46eca1344c`.
That gate covers 328 supplied graphs and their 328 complements only.

**Reported computation, independently rerunnable:** NetworkX 3.3 graph6
decoding of those 656 supplied/derived graphs found degree spread exactly 3 in
every case (`min,max = 19,22` for all 328 sources and their complements).
Thus an independently verified `(5,5,42)` graph with `Delta-delta <= 1`
would be new relative to the supplied corpus.  This does not show that it is
new relative to all order-42 graphs, and it supplies no reason to assume a
43-vertex extension.

The source concept is Radziszowski's reported almost-regular conjecture below
the Ramsey threshold; the prediction is a missing order-42 component in this
sharp slice; the test is exact SAT plus independent model checking.  The
source is the maintained survey: https://www.cs.rit.edu/~spr/ElJC/sur.pdf.

## Exact slice and cheapest discriminator

For a hypothetical `(5,5,42)` graph, the standard `R(4,5)=25` neighborhood
bound gives `17 <= d(v) <= 24`.  With degree spread at most one, all degrees
are in `{q,q+1}` for some `q` in `17..23`.  Complementation maps those seven
bands to four representatives:

```text
{17,18} <-> {23,24};  {18,19} <-> {22,23};
{19,20} <-> {21,22};  {20,21} <-> {20,21}.
```

Therefore the complete almost-regular slice is the union of four named
branches `q = 17,18,19,20`, *provided complement closure is retained and
verified*.  Do not encode a loose global edge-count interval in place of the
42 row constraints.  For a fixed `q`, use the 861 edge bits, both forbidden
color clauses for each of `C(42,5)=850,668` five-sets (1,701,336 clauses),
and for every vertex `q <= sum incident edges <= q+1`.

The cheapest informative production run is **only branch `q=20`** (degrees
20/21), for 300 seconds and 1 GiB including proof generation.  It is the
central, self-complementary band and overlaps the edge-density scale of the
controls.  A checked SAT model is decisive for the live novelty discriminator.
A checked UNSAT proof excludes only `q=20`; timeout/OOM is only a cost result.
Run the other three representatives only after this pilot meets the artifact
and proof-size budget.  This ordering is a proposal, not a structural claim
that `20/21` is likelier than the other bands.

## Controls and independent verification plan

1. **Hash/source gate.** Re-run `scripts/run_corpus_gate.py` before generation
   and reject any change to the two hashes above, 328 records, 656 labels, or
   spread histogram `{3:656}`.  Retain the source URL
   `https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6` and its provenance.
2. **Counter unit gate.** Exhaust all graphs on at most six vertices.  For
   every local `q` in `0..n-1`, compare the independent direct predicate
   `max(degrees)-min(degrees)<=1 and degrees subset {q,q+1}` with the CNF
   evaluator.  Include accepted regular, accepted mixed `q/q+1`, rejected
   spread-two, and shifted-incidence boundary vectors.  On `n=42`, a decoded
   model is checked by a direct degree scan, not by reusing CNF auxiliaries.
3. **Ramsey-clause gate.** On the `R(3,3)` control, generate both colors of
   every triple: `C5` at the applicable degree band must decode as SAT and
   `n=6` must give DRAT-checked UNSAT.  Separately enumerate every 5-set in a
   sampled 861-edge assignment and compare clause satisfaction to the existing
   Python combinations checker and C recursive-bitset checker.
4. **Independent formula audit.** Generator A (Python, lexicographic
   five-sets/edge map, row counter A) and generator B (C, separate nested-loop
   enumeration and a different cardinality construction) must agree on the
   ordered edge map and Ramsey-clause ledger.  They need not emit byte-equal
   auxiliary clauses.  Each emits a mapping, counts, and SHA-256 manifest.
5. **Solver/proof gate.** Run `cadical -q -t 300 CNF proof.drat` under a
   1-GiB enforced limit; retain solver version/options and wall/RSS data.  On
   `UNSAT`, freshly compile the pinned `drat-trim`, check DRAT, convert to
   textual LRAT, then check with separately compiled `lrat-check`.  Do not
   call CaDiCaL's internal checking independent evidence.  A killed or
   incomplete proof is forensic output only.
6. **Model/novelty gate.** On `SAT`, decode the 861 primary variables,
   independently run both full `K5` checkers and the direct degree scan,
   canonicalize with `nauty-labelg`, and compare against all 656 retained
   canonical labels.  Preserve the graph6/model and every comparison result.

Required mutation sentinels: omit one five-set/color clause, negate one edge
literal, shift one incidence index, weaken either row bound, and corrupt one
DIMACS variable-map entry.  Each must fail at least one relevant gate.  Also
check complement closure by transforming a hand-built model in every one of
the seven original bands and verifying its mapped representative band.

## Failure modes and stop conditions

The likely errors are an average-degree constraint mistaken for spread one;
missing color clauses; an off-by-one upper triangle map; sharing generator and
auditor logic; accepting DRAT without the original CNF; treating the 656 as
complete; and calling a timeout an exclusion.  Proof logging may also inflate
memory or disk so sharply that a solver result without a completed proof is
not reusable.

Stop immediately on a source/graph6/degree/CNF-map/dual-scan/proof mismatch.
Otherwise stop the first pilot at 300 seconds or 1 GiB, a fully dual-checked
new model, or a complete DRAT+LRAT-checked `q=20` exclusion.  Do **not**
escalate to 43, add symmetry breaking, or infer the full almost-regular result
from that single band.  The full named slice is resolved only after the four
representative branches have corresponding checked outcomes.

## Reusable artifact and Sol review

Create an `almost_regular_42/` packet containing the two source hashes,
counter truth-table report, both five-set ledgers, DIMACS/map/manifest per
branch, command/environment/RSS record, proofs where complete, model decoder
output, dual full scans, and nauty label comparison.  It is reusable as a
bounded SAT-verification template and as a novelty-control packet; it is not
an end-to-end upper-bound proof.

Sol should independently verify the complement reduction from seven bands to
four, regenerate at least one branch's clause ledger and row bounds, rerun the
small exhaustive counter test, and rescan any SAT model without the generator.
Reject any report that conflates the supplied 656 with a classification, a
single branch with the full almost-regular slice, solver `UNSAT` with a
checked certificate, or a novel 42 graph with an `R(5,5)` improvement.
