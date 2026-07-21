# Experiment-verification memo — R(5,5), epoch 12 intake

**Scope.** Experiment design and adversarial verification only.  This proposes
no Ramsey graph, exclusion, catalogue completeness claim, or new bound.

## Best live route

Use the recorded next route: a **16-leaf, proof-carrying cube pilot** for the
already audited fixed-root `q=20` order-42 formula.  The normalized monolith is
blocked from an identical retry: it returned `UNKNOWN` after 300.226 seconds.
Its formula packet remains useful because its exact CNF hash is
`87b70753dd07b3fc04ddb62799701a8a379efb2cd5c9ea9ddbd026f6679865dd`, its
71,421 variables and 1,844,093 clauses were independently audited, and the
root normalization coverage lemma is proved.  Cube units change architecture
without changing the represented normalized formula.

Do not revisit the exhausted one-/two-orbit seed families, the unchanged
monolith, or q=17--19.  The cube pilot is a cost/heterogeneity discriminator,
not a proof of the complete almost-regular slice.

## Exact cheapest discriminator

Let `A={1,...,20}` be the fixed root-neighbor part and
`B={21,...,41}` its fixed nonneighbor part.  Branch on this declared,
alternating cross-part path:

```text
edge       (1,21) (2,21) (2,22) (3,22)
DIMACS var    212    213    234    235
```

These are four distinct primary variables, not root units or auxiliaries.  A
path has substantially less within-cube permutation redundancy than a matching
or a `2 x 2` rectangle, while sharing vertices so the degree counters see a
nontrivial local assignment.  This is a deterministic engineering choice, not
a claim that the path has special Ramsey meaning.

For each `b=0,...,15` in lexicographic binary order, construct a leaf CNF as
the normalized body with exactly four final units, positive iff the associated
bit is one.  Its header is exactly

```text
p cnf 71421 1844097
```

and all 16 leaves are run sequentially with `cadical -q -t 20`, a 1-GiB RSS
limit, and a 64-MiB per-leaf DRAT file limit.  Therefore the maximum solver
budget is 320 seconds (unless a validated SAT leaf stops it earlier).  Crucial:
put the cube units into each physical CNF.  Do not use solver assumptions,
because an assumption-mode proof does not by itself certify the corresponding
unit-augmented leaf.

## Controls and independent verification

1. **Parent identity and leaf construction.** Hash-lock the retained normalized
   CNF and map.  A cube producer writes a manifest and a separate auditor that
   does not import it rederives the variable arithmetic, checks the four edge
   pairs, verifies that they are cross-part/non-unit/primary, and checks every
   leaf's header, unchanged parent clause body, and canonical four-unit suffix.
2. **Complete cover.** The independent auditor enumerates all 16 four-bit
   assignments and requires exactly one leaf for each.  For every distinct pair
   it requires a variable with opposite literals, establishing disjointness.
   Its cover statement is only `F = union_b (F and cube_b)`; do not invoke
   unproved isomorphism pruning among leaves.
3. **Toy end-to-end gate first.** On normalized `R(3,3,6)`, use the analogous
   cross-part path `(1,3),(1,4),(2,4),(2,5)`, DIMACS variables `5,8,9,13`.
   Produce all 16 physical leaves, check the cover independently, and require
   every leaf's DRAT to convert and pass LRAT checking.  This supplements--not
   replaces--the existing normalized R(3,3,6) proof because it tests cube
   mapping and reconstruction.
4. **Leaf disposition.** A production SAT leaf must be decoded from all 861
   primary literals and pass the direct Python five-set/degree/root scan and
   the independent C recursive-bitset scan.  An UNSAT leaf counts only after
   fresh `drat-trim` conversion and separately compiled `lrat-check` accept
   the reconstructed leaf CNF.  A timeout, proof-size limit, or failed proof
   is `UNKNOWN`, never an exclusion.
5. **Mutation tests.** The independent audit must reject a missing/duplicate
   cube, a cube bit sign reversal, a repeated or shifted variable, an auxiliary
   variable, a root-unit variable, a leaf with parent-body drift, and a proof
   checked against the parent instead of its leaf.

Store the parent CNF once plus a cube manifest, exact reconstruction program,
per-leaf unit suffix/hash, transcript, resource data, proof/LRAT where
complete, and audit report.  Do not store 16 opaque copies of the 80-MB parent
CNF; cold reconstruction from the hashed parent plus suffix is required for
each proof replay.

## Failure modes, stop rules, and Sol review

The most likely unsoundness is confusing a partition of solver assumptions
with a proof-carrying partition of CNFs.  Other risks are edge-order/polarity
drift, accidentally branching on fixed root units, a malformed DIMACS header,
proof checker inputting the wrong leaf, treating a partial set of refuted cubes
as the parent formula, and treating the supplied 656 order-42 graphs as a
census.  The P5 selection is not a symmetry quotient: any apparent equivalent
leaves must still be run unless a new checked symmetry argument is supplied.

Stop immediately on any parent hash, cube-cover, reconstruction, model-scan,
or DRAT/LRAT mismatch.  Also stop the production pilot if no leaf is fully
resolved within 20 seconds, or if aggregate retained DRAT+LRAT data exceeds
256 MiB; that is the predeclared storage gate for a possible full campaign.
Only a validated SAT leaf ends the whole run with a graph requiring independent
review.  A validated UNSAT leaf eliminates only that named cube.  Do not
escalate to q=17--19, order 43, more cubes, or more time from an inconclusive
pilot.

Sol should independently rederive variables 212/213/234/235 and the 16-cube
cover, cold-reconstruct at least one toy and one production leaf, and run both
proof checkers on every claimed UNSAT leaf.  Reject any report that labels an
UNKNOWN leaf as refuted, aggregates an incomplete cube set into a q=20
exclusion, accepts assumption proofs as unit-CNF proofs, or makes a global
R(5,5) statement from this bounded branch.
