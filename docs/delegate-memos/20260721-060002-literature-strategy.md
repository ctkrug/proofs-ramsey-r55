# Literature-strategy memo — R(5,5), epoch 10 intake

**Scope.** Compact reconnaissance only.  This memo makes no witness,
classification, multiplicity-optimum, or Ramsey-bound claim.

## Status and duplication audit

The maintained status has not changed.  Radziszowski's *Small Ramsey Numbers*,
DS1.18 (revision 18, 24 April 2026), records the range
`43 <= R(5,5) <= 46`; it describes the 656 order-42 graphs as **strong
evidence** for a conjecture, not an exhaustive classification.  The current
Angeltveit--McKay manuscript is arXiv:2409.15709v2 (1 September 2025), whose
abstract states the independently implemented LP-plus-case-checking proof of
`R(5,5) <= 46`.

- Survey: https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- Upper bound: https://arxiv.org/abs/2409.15709
- McKay data page: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html

The two-orbit domain-wall route is now exhausted at its declared scope: the
retained dual encodings and DRAT/LRAT audits establish exact burden two in all
twenty fixed-background slices.  A third-orbit release would repeat an
explicitly blocked escalation without a new discriminator.  Radius-1/radius-2
publisher repairs and pure circulants are likewise not live.  Generic search
is historically duplicative until it has a leakage-safe control advantage.

## Best live route

Run the **almost-regular order-42 exact feasibility pilot**
(`strategy-33eb5acd3b31` / the novel-42 branch), not a claim that all Ramsey
graphs are almost regular.

The local corpus premise was rechecked from the authenticated source
`sources/r55_42some.g6`, SHA-256
`067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.
NetworkX graph6 decoding of its 328 records and their complements gives 656
graphs, all with degree spread exactly three; none has `Delta-delta <= 1`.
This agrees with the corpus gate's 656 classes and global degree range 19--22
(`artifacts/authenticated_corpus_report.json`, SHA-256
`0d9b1801434edcc12f34e73cea6c98d911f0e0c6f0884f8f03d96a46eca1344c`).
Therefore a valid almost-regular order-42 graph would be new relative to the
supplied corpus.  That is a useful, falsifiable basin discriminator, not
evidence that the corpus is complete or that a 43-vertex graph exists.

The literature/data page expressly allows both further 42-vertex graphs and
43--47-vertex graphs.  The survey still calls the 656 conclusion strong
evidence only.  Thus the slice respects the central historical gap rather
than assuming it away.

## Cheapest discriminator

Before a solver budget, implement and unit-test the degree constraint as the
seven-way exact disjunction

```text
d(v) in {q,q+1}, for every v, q = 17,18,...,23.
```

For an order-42 `(5,5)` graph, the standard `R(4,5)=25` neighborhood bound
gives `17 <= d(v) <= 24`; the seven branches cover exactly the additional
condition `Delta-delta <= 1`.  Do not substitute the looser per-vertex range
or an average-degree condition.  Run a deterministic truth-table/property
test on small graphs and boundary degree vectors before generating production
CNFs.

Then make one deterministic CNF per `q`, with the 861 unordered edge bits,
both forbidden-color clauses for every 5-set, and an independently generated
cardinality encoding for all 42 degree rows.  The pilot is only a
300-second/1-GiB feasibility measurement across the fixed seven branches:

- a SAT model is admissible only after both full 5-set checkers, symmetry and
  degree scans, source-independent canonicalization, and comparison against
  all 656 supplied labels;
- a completed UNSAT branch is admissible only with deterministic CNF mapping,
  checked DRAT and a separately checked LRAT conversion; and
- a timeout, OOM, or partial portfolio proves nothing beyond the recorded
  resource result.

## Controls and failure modes

Hash-lock the corpus report and source bytes.  Cross-check production graph6
parsing against the existing parser gate; retain the spread histogram
`{3: 656}` as a positive corpus check.  Test the degree encoder on deliberately
accepted regular and `(q,q+1)` graphs, and rejected spread-two graphs, with a
separate evaluator rather than the CNF generator.  Mutation tests must detect
a shifted edge index, a missing incidence literal, one omitted five-set/color
clause, and a weakened cardinality bound.  A valid model must also have no
clique or coclique on any five vertices under both existing checkers.

The main risks are (1) accidentally encoding degree range rather than spread,
(2) treating all 656 supplied controls as a census, (3) calling a proofless
solver UNSAT an exclusion, (4) promoting a novel 42 graph to an R55 advance,
or (5) silently sharing the same degree/CNF logic between generator and
checker.  Also reject an immediate K43 extension campaign: a new 42 graph is
a control/basin result first, and a one-vertex extension needs its own exact
scope and evidence.

## Reusable artifact and stop rule

Preserve a seven-branch bundle: source/report hashes, degree-counter test
vectors, DIMACS and variable map, generator hashes, solver/version/options,
proofs where available, decoded models, dual checker reports, and canonical
comparison output.  It is reusable for a later novel-42 search and for a
certified small-case SAT pipeline; it does not certify the full order-42
space.

Stop immediately on any corpus, graph6, degree-counter, CNF-to-graph, proof,
or full-scan mismatch.  Otherwise stop at the pilot budget, a fully checked
new 42 graph, or complete proof-checked resolution of the *seven named
branches*.  Do not enlarge the degree spread or launch a 43 search merely
because the pilot is inconclusive.

## What Sol should independently verify or reject

Verify DS1.18's revision/status, the source and report hashes, the direct
spread recomputation, and that `{17,...,23}` covers every `Delta-delta <= 1`
degree profile allowed by the `R(4,5)=25` bounds.  Independently regenerate at
least one branch's five-set clauses and degree counter, and rescan any model.
Reject any statement that the 656 are exhaustive, that seven bounded slices
settle `R(5,5)`, that a timeout is an exclusion, or that almost-regularity is
a theorem about every order-42/43 Ramsey graph.
