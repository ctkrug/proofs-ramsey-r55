# Terra literature-strategy memo — epoch 16 preflight

## Recommendation

Keep `strategy-a230b66ef386` as the highest-readiness *infrastructure gate*,
not as an unblocked novelty search.  It is the only live route with a measured
failure signature and a sound, local response: 64 exact labelled completions
of one frozen 30-vertex core collapsed to eight destroy-label normal forms.
The nearest historical methods are McKay--Radziszowski--Exoo deletion/extension,
annealing/tabu, novelty bias, and common-subgraph neighbourhood search.  The
proposed lex constraint is neither a new lower-bound mechanism nor an
isomorphism-class exclusion; it is standard symmetry breaking inside a more
controlled SAT boundary experiment.  Its falsifiable delta is only whether it
removes the measured destroy-label redundancy without losing an orbit.

The maintained survey is revision 18 (24 April 2026) and still gives
`43 <= R(5,5) <= 46`; it describes 656 order-42 graphs as strong evidence,
not a classification.  McKay--Radziszowski likewise report that many diverse
searches returned the same 656 graphs, so a further known-class rediscovery is
not evidence for a new construction.

Sources: https://www.cs.rit.edu/~spr/ElJC/sur.pdf ;
https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf ;
https://doi.org/10.1002/jgt.70029

## Crucial premise and cheapest discriminator

Remove the source-specific Hamming-at-least-60 condition before applying the
`S_12` destroy-label action: that condition is not invariant under a destroy
permutation.  The 30-bit frozen-core rows of source record 21's destroyed
vertices are in fact all distinct.  Consequently, its row-sorted destroy-label
permutation is a **guaranteed known valid solution** of the new formula.  Thus
an unblocked first SAT model is necessarily only a positive control; it cannot
be a novelty discriminator.

Run one bounded gate:

1. Independently encode adjacent 30-bit row lexicographic constraints and,
   on every labelled toy boundary with three fixed and three destroyed vertices
   (eight fixed cores times `2^(3*3+C(3,2)) = 32,768` assignments), compare
   the CNF predicate with direct row sorting over all `S_3` permutations.  Test
   both distinct and tied rows; require every orbit to have an accepted member.
2. Reconstruct the record-21 source, apply the deterministic row sort, and
   directly verify its primary assignment against the regenerated no-Hamming
   CNF and both exact graph checkers.  This is the obligatory positive control.
3. Block that one row-sorted primary vector, then permit exactly one
   post-block SAT model.  Record its normal form and supplied-corpus label,
   but do not treat a known model as a negative result or a novel model as
   sufficient without the existing dual full-graph and canonical-membership
   checks.

Success is exact agreement between direct and encoded toy predicates, complete
toy-orbit coverage, and the source positive control.  Failure is any missing
orbit, disagreement, residual Hamming clause, malformed primary mapping, or
checker/canonical-label discrepancy.  A solver `UNKNOWN` or unchecked `UNSAT`
is non-evidence.

## Efficiency and scope

The frozen core is still the justified reduction: 435 of 861 edge bits are
fixed (50.52%), 426 are primary, and 142,506 core-only five-sets are absent
from the boundary formula.  On the distinct-row stratum, lex ordering has a
theoretical maximum `12! = 479,001,600` destroy-label quotient; the only safe
empirical prediction is the observed 64-to-8 (8x) reduction, not `12!`.
Tied rows preserve coverage but leave permutations inside equal-row blocks,
which is why they must be exhaustively controlled rather than assumed away.

Use the existing incremental CaDiCaL state: parse the static formula once,
retain learned clauses, and add primary-only blocks.  Keep one compressed base
(2.62 MB rather than roughly 168 MB for 64 copies), compact bitsets, and batched
bitset/C full-five-set evaluation only after SAT.  Do not undertake the full
core-embedding census: even the retained negative host probe took 10.63 s and
the naive all-control deletion count is `656*C(42,12)`.  The quotient does not
create a class block, does not cover other core embeddings, and does not make
the 656 exhaustive.

## Stop and redirect

Stop this epoch on a toy coverage/encoding failure, a source-control failure,
a dual-checked supplied-corpus-novel graph, or the single post-block model.
Reject any claim that one labelled block excludes a supplied class, that a
normal-form count generalizes beyond the sampled boundary, or that an
unblocked first model tests novelty.  The Sol principal should independently
verify the direct source-row calculation (12 distinct rows), no-Hamming CNF
regeneration, `S_3` toy orbit enumeration, primary-variable polarity, and both
graph/canonicalization checks.

If the gate fails, do not broaden boundary search; redirect to
`strategy-r55-two-orbit-proof-compression`, whose output criterion is a raw
K5-clause theorem rather than more known-class sampling.  If it passes, the
next boundary budget must be stated in **row-sorted normal forms**, not raw
labelled solutions, and retain its limited order-42 scope.
