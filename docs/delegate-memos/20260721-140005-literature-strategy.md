# Terra literature-strategy memo — archive/I2-I3 audit

## Outcome

**Do not launch `strategy-1a9f19a608f2` as “reconstruct the published
order-45 I2/I3 baseline.”**  That premise is not supported by the cited
literature or archive.  The strongest remaining live route is instead the
**unknown-order-42 basin discriminator** (`strategy-r55-novel42`), with the
almost-regular branch kept as one explicitly scoped arm and with exact
canonical novelty as the gate.  This is a proposal, not a candidate or a
bound.

The maintained survey is now revision 18 (24 April 2026) and still records
the `R(5,5)` range `43 <= R(5,5) <= 46`.  It describes 656 order-42 graphs
as strong evidence rather than an exhaustive classification.  Source:
https://www.cs.rit.edu/~spr/ElJC/sur.pdf.

## What the audit established

**Sourced fact.**  In McKay--Radziszowski (1997), `I2` and `I3` are general
subgraph identities.  Their displayed LP with variables `n_i`, `g_{i,j}` and
`h_{i,j}` is then used to prove `R(4,6) <= 41`, not to publish an
order-45 `R(5,5)` profile system.  In that notation, `I2` needs only edge
counts, while `I3` needs, at fixed order and edge count, triangle bounds and
the range of

`g3(X,n) = e(X)(n-3v(X)+3) + 6 t(X) + 3 p(X)`,

where `p(X)` counts induced `T_{2,1}` (a two-edge three-vertex path).
The 2024/2026 `R(5,5)<=46` source instead visibly uses the `m=2` excess
identity plus a separately proved pointed-graph/gluing reduction; it does not
present the proposed order-45 I2/I3 scalar baseline.  Sources:

- https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf
- https://arxiv.org/abs/2409.15709

**Reproducible retrieval.**  On 2026-07-21 UTC:

```sh
curl --fail --silent --show-error --location --max-time 180 \
  --output r45extreme.tar.gz \
  https://users.cecs.anu.edu.au/~bdm/data/r45extreme.tar.gz
sha256sum r45extreme.tar.gz
# 9cfac9dbd1c209cfa342e5d5424df2a7a3fbb008ca00bf0a992e5bbe72f925b6
tar -tzf r45extreme.tar.gz
```

The 90,599,728-byte archive contains only graph6 members, no precomputed
triangle, pointed-neighbourhood, or I3 table.  It is nevertheless sufficient
to *derive* `e,t,p` for each supplied graph (`p = sum_v C(d_v,2) - 3t`).
For the orders needed by a hypothetical `(5,5,45)` graph, its complete edge
layers are only:

| order | all possible edge counts | supplied complete layers |
|---:|---:|---|
| 20 | 68--100 | 68, 69, 98, 99, 100 |
| 21 | 77--107 | 77, 78, 106, 107 |
| 22 | 88--114 | 88, 89, 113, 114 |
| 23 | 101--122 | 101--104, 119--122 |
| 24 | 116--132 | separate complete file `r45_24.g6` |

The separate 24-vertex corpus retrieved from
https://users.cecs.anu.edu.au/~bdm/data/r45_24.g6 has 352,366 graph6 records,
16,913,568 bytes, and SHA-256
`83ca4028f206b2fa4315ef219b8c2c57c7835209673dd8183d8fb4353bd4fdd0`.
The data index itself says the archive provides only the smallest and largest
few edge-count layers.  Thus it cannot supply valid extrema of `t`, `p`, or
`g3` for the many missing interior layers.  Optimizing only over supplied
graphs would be a subset statistic, not a bound for all `(4,5,n,e)` graphs.

## Best live route and cheapest discriminator

**Source concept -> prediction -> test.**  A 43-vertex witness, if it exists,
has 43 valid order-42 deletions.  Since none can lie in the supplied 656
nonextendible controls, a genuine new order-42 component is a necessary
milestone.  Test the nonlocal destroy-and-repair mechanism first on
authenticated controls: destroy 6--12 vertices jointly, repair with the exact
forbidden-five-set evaluator, canonicalize every valid order-42 result, and
require a result outside all 656 before allocating K43 search.

Run a separate degree-{20,21} arm only if its solver/encoding differs
materially from the blocked q=20 CaDiCaL configurations.  Do not repeat their
same monolith or 16-leaf 20-second pilot.  The reported induced-distance-six
separation from known controls remains a useful *reported* warning, not a
hard pruning rule without a replayable coverage artifact.

## Controls and failure modes

- Use the authenticated 656 corpus and two independent full K5/independent-5
  checkers; do not call it exhaustive.
- Split complement pairs/isomorphism classes before making damaged controls;
  otherwise recovery and learned repair rules leak labels.
- Compare any conflict-core or linkage proposal against exact-delta tabu,
  persistent clause weighting, AlphaEvolve-style high-violation induced-subgraph
  grafting, and ordinary crossover.  These are adjacent prior art, not novel
  baselines to omit.
- A rediscovered member of the 656, lower heuristic energy, or a partial DRAT
  stream is not a success.  Canonical labels, independent verification, and
  explicit novelty are mandatory.

## Reusable artifact and stop condition

This memo supplies the archive manifest, retrieval command, hashes, and the
precise `I2/I3` data-field map.  If a future team obtains a complete catalogue
or independently proved global `t/p/g3` bounds for every missing edge layer,
the feature route may reopen as a *new* exact inequality project.  Until then,
stop before LP/profile generation: the required universal I3 coefficient table
is absent.

The Sol principal should independently verify the source distinction (the
1997 LP's `R(4,6)` application versus the `R(5,5)` argument), recompute the
archive manifest/hash, and reject any claim that archive-only feature extrema
cover unsupplied edge layers or that they establish an order-45 exclusion.
