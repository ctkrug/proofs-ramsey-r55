# Literature-strategy memo — R(5,5)

**Scope:** reconnaissance and a bounded source/control audit. This memo makes
no Ramsey-bound, witness, completeness, or global-optimality claim.

## Best live route

Pursue **S4 only through a publisher-seed normalization and novelty firewall**:
first freeze and independently gate Molnár et al.'s actual Supplementary Data
4, then make one *non-star* bounded repair slice around its six-vertex
conflict support.  Do not restart ordinary K43 local search and do not use the
visible Gist transcription as the seed.

The precondition that blocked S4 has materially improved.  Two direct HTTPS
retrievals of

`https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt`

returned identical 3,812-byte bodies, SHA-256
`c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990`.
The first response was HTTP/2 200 with TLS verification zero,
`Content-Type: application/octet-stream`, and the publisher object's title is
“Supplementary Data 4: The coloring matrix with only 2 monochromatic
5-cliques of a complete graph with 43 nodes.”  Retained inputs are
`sources/retrievals/springer_supplementary_data4_audit{1,2}.{txt,headers}` and
the experiment records are
`.proof-experiments/20260720-235158-0cfef1` and
`.proof-experiments/20260720-235208-a7e84e`.

This aligns with the primary article, which says its N=43 coloring has two
monochromatic 5-cliques on six nodes and points specifically to Supplementary
Data 4: https://doi.org/10.1038/s41467-018-07327-2 .  It does not make the
two-conflict state a global minimum or a Ramsey result.

## Exact rationale

The frozen publisher matrix is a symmetric zero-diagonal 43-by-43 matrix with
454 one-edges.  Checker A (direct 5-subset enumeration) and Checker B
(recursive bitset clique enumeration), fed independently normalized raw
rows, agree on exactly two all-zero K5s:

```
[6,12,17,36,42]
[6,12,31,36,42]
```

Thus the intersection is `[6,12,36,42]` and the union has six vertices,
matching the paper's stated topology.  There are no all-one K5s.

Each of the four intersection deletions is a valid order-42 graph.  Canonical
labels from `nauty-labelg` match the authenticated supplied 656 control packet:
deleting 6 or 42 gives canonical SHA-256
`ee2269437c3ba4cd8cde512768489089a5865ab701b38e8716acaddcdd07c3a7`;
deleting 12 or 36 gives
`3f16d9a422f89c250bebd7d50fa6cb4006de0655513bac24f34232d2620c623f`.
This is a key strategy constraint, not a discovery.  The 1997 result that the
known controls do not one-vertex extend means a repair that keeps any such
42-vertex deletion fixed and only changes its missing vertex's incident edges
is historically saturated.  A viable S4 slice must force at least one
edge-change inside every relevant deletion remainder.

The old Gist control is not the publisher matrix under its displayed labeling:
it has 448/449 one-edges for its two matrices, versus 454 for the publisher
matrix.  Hence it cannot be isomorphic to the publisher matrix either.  Keep
it only as a parser/evaluator mutation control.

The broader status is unchanged: Dynamic Survey DS1.18 (revision 2026-04-24)
records strong evidence, rather than a census, for 656 42-vertex critical
graphs and the published upper bound 46:
https://www.cs.rit.edu/~spr/ElJC/sur.pdf .  McKay's data page likewise says
more 42-vertex or 43--47-vertex graphs could exist:
https://users.cecs.anu.edu.au/~bdm/data/ramsey.html .

## Cheapest discriminator

Before any optimizer, add a dedicated, fail-closed **publisher-seed gate**
whose two parsers read the publisher's space-delimited representation directly
(not a shared pre-normalized file).  Require the body hash, 43 rows of 43
bits, symmetry/diagonal checks, the two exact K5 identities above, no
all-one K5, the four deletion labels above, and an explicit report that each
label is in the supplied 656 only—not in an exhaustive census.

Then test the smallest repair family that excludes star-only extension:
choose one intersection vertex `v`; retain the publisher matrix outside a
frozen edit set, but require at least one edit among the remaining 42
vertices.  Search increasing edit cardinality and retain every SAT model for
both exact checkers.  An UNSAT claim is admissible only for the precisely
encoded bounded family with a checkable proof log.  This discriminator answers
whether the published seed has any advantage once the known-extension basin is
explicitly escaped; it does not ask an optimizer to solve R(5,5).

## Controls, failure modes, and stop condition

Controls: retain both raw bodies, raw headers, transfer JSON, and experiment
hashes; do not require header-byte equality because date/cache fields differ.
Recompute body hash and parse from raw bytes in two implementations; repeat
the 656 canonical membership comparison against
`artifacts/authenticated_corpus_report.json`; positive-test each parser with a
forced clique and forced coclique; and A/B compare the bounded repair against
a basic tabu/annealer at matched seeds and budgets.

Stop at any provenance/body/parser/conflict/canonical-label mismatch.  Stop
the first repair slice when its exact radius is exhausted; report only that
slice.  Also stop and reject star-only repair, a two-conflict local optimum
presented as global, an unlogged UNSAT result, similarity scoring as a final
evaluator, or any claim that the 656 supplied labels are complete.

## Reusable artifact and independent Sol review

The reusable artifact is the authenticated publisher raw packet plus a
dedicated seed-gate report recording exact conflict/deletion identities and
canonical hashes.  It is a durable benchmark for future K43 repair methods
and distinguishes the real seed from the unrelated visible transcription.

Sol should independently verify: (1) both downloaded body hashes and the
publisher-controlled effective URL/TLS status; (2) the raw-matrix parse and
two K5 identities; (3) both deletion-label membership tests; and (4) that any
next repair edit family changes a deletion remainder.  Sol should reject any
proposal that labels the publisher seed a new 42 basin, relies on a direct
one-vertex extension of its known deletions, or promotes a bounded repair
result to a Ramsey-number conclusion.
