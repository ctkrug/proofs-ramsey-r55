# Terra literature-strategy memo — epoch 15

## Recommendation

**Keep the order-42 frozen-boundary route, but relabel its next pass
“labelled-model CEGAR,” not canonical/isomorphism-class CEGAR.**  Its exact
scope is the only live route with authenticated inputs, dual full-graph
checkers, a cold audit, and a recorded response to the observed failure
(rediscovery of supplied classes).  This is a proposed discriminator, not a
candidate, classification, or Ramsey bound.

The maintained Dynamic Survey is now revision 18 (24 April 2026) and still
gives `43 <= R(5,5) <= 46`; it continues to call the 656 order-42 graphs
strong evidence rather than a complete classification.  The 2026 journal
version of Angeltveit--McKay establishes only the upper bound 46.  Sources:

- https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- https://doi.org/10.1002/jgt.70029

## Exact rationale and cheapest discriminator

The eight first boundary models were all independently verified valid
order-42 graphs, but each canonicalized into the supplied 656.  Therefore a
plain restart, a new seed, or another first-model portfolio repeats a recorded
failure mode.  For *one* retained boundary (start with record 21), retain its
frozen induced 30-vertex core and its exact Ramsey/Hamming constraints; after
each dual-checked supplied-class model with primary boundary vector `b`, add
the 426-literal clause excluding exactly `b`, then continue to a predeclared
budget of 64 models.

The indispensable terminology correction is that this clause blocks **one
labelled 426-bit completion**, not an isomorphism class.  Canonicalization is
an acceptance test after SAT.  A true class block would have to exclude every
embedding of the fixed core into every supplied graph and every remaining
12-vertex relabelling; one core embedding alone can have up to `12! =
479,001,600` label assignments before automorphism coincidences.  Do not
claim that the proposed 64 clauses remove a supplied class.

The cheap preflight is a separate exact embedding census: enumerate which of
the 656 controls contain the particular frozen labelled 30-core and count the
compatible labelled completions or a proved compact representation of them.
If no compact, independently checked class-block encoding results, run the
model budget honestly as labelled CEGAR.  It remains informative only as a
rediscovery/novelty-rate measurement, never as an exclusion.

## Controls and failure modes

- Hash-gate the corpus (`067902e...0eccb`), regenerate the selected core and
  CNF, and keep the two full five-set checkers plus nauty membership and the
  NetworkX cold auditor.  A degree multiset is only a prefilter.
- Each block must be derived from the decoded *primary* 426 edges, then direct
  DIMACS evaluation must confirm the next model satisfies all prior blocks.
  Never block an auxiliary-variable assignment.
- Preserve the 60-distance condition.  Check an independently generated
  direct `sum(diff) >= 60` encoding against the retained Sinz formula on
  exhaustive small controls before using it in production.
- Stop immediately on checker/canonical-label disagreement, malformed or
  incomplete model, solver `UNKNOWN`, or an unverified UNSAT result.  A final
  UNSAT without a checked proof is not a boundary exclusion.

## Search-efficiency pass

The existing fixed core is the best already justified reduction: it freezes
`C(30,2)=435` of the `C(42,2)=861` edges, leaving 426 primary variables -- a
49.48% edge-variable reduction.  It removes `C(30,5)=142,506` of 850,668
five-sets (16.75%); the retained simplifier emits about 197k Ramsey clauses.
Do not quotient the destroy set or transfer a symmetry across a boundary
without an explicit automorphism/coverage proof.

The current distance counter consumes 155,550 of 155,976 variables.  A
separately audited prefix encoding of the direct lower bound `sum(diff)>=60`
can use at most `425*60 = 25,500` prefix auxiliaries (plus difference
definitions): an approximately 6.1-fold reduction in cardinality auxiliaries
and 83.6% fewer variables in that component.  This is a proposed encoding
change, so its small exhaustive equivalence gate is mandatory.

Batch different frozen boundaries, not successive CEGAR models of one
boundary.  For one boundary use an incremental solver API if it preserves the
base clauses and learned state while appending only audited primary blocks;
otherwise retain physical CNFs and hashes per round.  Generate five-set
clauses once, use bitsets only as a fast precheck, and still run both complete
evaluators on every accepted SAT model.  Core embeddings and canonical labels
should be cached with provenance; no cached result may substitute for the cold
audit.

## Literature audit: reject a tempting diversion

A 2026 presentation reports 141 of 313 hard-coded cases UNSAT for
`srg(45,22,10,11)` under `(5,5)`-goodness.  It is a construction hypothesis:
a satisfying graph would, with the established upper bound, prove `R(5,5)=46`.
But no source inspected proves that a 45-vertex Ramsey graph must have those
strongly-regular parameters, and the deck does not supply a complete checked
case cover.  Consequently, even a completed UNSAT run in that family would
not improve the global bound.  Reject it as the next main lane unless its
authors provide a necessary-condition theorem or a fully checkable witness.
Source: https://www.cs.rit.edu/~spr/COURSES/CCOMP/srg_r55.pdf

## Reusable artifact, stop, and independent review

The reusable deliverable should be an immutable per-round ledger: core hash,
base-CNF hash, ordered primary-vector blocks, model/canonical hashes,
dual-check outcomes, and the embedding-census result.  Stop on a dual-checked
supplied-corpus-novel order-42 graph, 64 verified labelled rediscoveries, or
any failure mode above.  The Sol principal should independently verify the
“labelled not canonical” distinction, rerun the cardinality-equivalence gate,
and reject any assertion that the 656 are exhaustive, that 64 blocks imply a
boundary exclusion, or that the partial SRG calculation narrows all
45-vertex Ramsey graphs.
