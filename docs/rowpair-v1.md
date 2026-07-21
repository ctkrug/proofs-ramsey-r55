# The uncoloured adjacency-row pair LP is vacuous at orders 43--45

Recorded: 2026-07-21 UTC

## Exact scope

This note concerns only the following relaxation.  Fix an order `n` and a
degree histogram `p_a`, where `a` runs from `n-25` through `24`.  For every
unordered pair of degree classes `(a,b)`, distribute the required number of
off-diagonal row pairs among Hamming distances allowed by the union of the
edge and nonedge common-neighbour bounds.  Add the diagonal mass `n` at
distance zero and impose every binary Hamming-scheme Delsarte inequality

```text
sum_(u,v) K_k^(n)(d_H(row_u,row_v)) >= 0,  k=0,...,n.
```

The relaxation does not retain which pairs are edges, the degree-class edge
marginals, adjacency-matrix symmetry beyond symmetric pair counts, or the
zero-diagonal coordinates.  The result below therefore says nothing about a
coloured adjacency-aware LP, a Terwilliger SDP, graph existence, or the value
of `R(5,5)`.

## Central-distance feasible template

For any profile, put all off-diagonal mass for a degree pair `(a,b)` at

| order | `a+b` even | `a+b` odd |
|---:|---:|---:|
| 43 | 22 | 21 |
| 44 | 22 | 23 |
| 45 | 22 | 23 |

Direct enumeration of the edge and nonedge common-neighbour intervals proves
that the selected distance belongs to their union for every allowed degree
pair.  If `s` vertices have even degree and `n-s` have odd degree, the exact
Krawtchouk sum is

```text
n K_k(0)
+ [s(s-1) + (n-s)(n-s-1)] K_k(h_even)
+ 2s(n-s) K_k(h_odd).
```

The retained certificate evaluates this integer for every `s=0,...,n` and
`k=0,...,n`.  Every value is nonnegative.  The minima are 1, 0, and 1 at
orders 43, 44, and 45, respectively.  Hence the displayed assignment is a
feasible LP point for every degree histogram; no solver or numerical dual is
needed.

The handshake-parity profile counts are 6,992,920 at order 43, 953,580 at
order 44, and 106,076 at order 45, for 8,052,576 total.  Applying the published
`R(4,5,m)` edge extrema to the doubled `m=2` excess identity gives a lower and
upper contribution interval that strictly straddles zero for every allowed
degree.  Consequently this scalar interval test also removes none of those
profiles.  This is an interval-level statement, not a reconstruction of the
full McKay--Radziszowski `I2/I3` linear program.

## Controls and independent reconstruction

Fresh Python and C/bitset graph6 implementations emitted byte-identical
record-indexed ledgers for the 328 supplied order-42 graphs and their
complements.  The ledgers include degrees and ordered
`(degree_u,degree_v,edge,common-neighbours,common-nonneighbours,distance)`
counts.  They reproduce 194 distinct degree histograms and off-diagonal row
distances 12--28.  Across the 656 controls there are 12,144 ordered edge pairs
with 13 common neighbours and 12,144 ordered nonedge pairs with 13 common
nonneighbours, so changing either sharp bound to 12 fails.

The cold checker uses a three-term integer Krawtchouk recurrence rather than
the producer's binomial sum, and dynamic programming rather than recursive
profile enumeration.  It also exhausts all 33,867 labelled graphs through
order 6, checks the row-distance and complement transformations, and rejects
seven declared mutations.  The first production attempt correctly stopped on
an off-by-two bug in the common-nonneighbour ledger for adjacent pairs.  For a
general pair the endpoint-excluding formula is

```text
q_uv = n - 2 - d(u) - d(v) + 2 epsilon_uv + c_uv.
```

The corrected run and cold audit are the only accepted experiments.

## Disposition

The prediction that this uncoloured pair LP cuts a scalar-admissible profile is
false throughout the declared orders.  Per the predeclared stop rule, do not
build the custom SDP from this null result.  A future coloured model is a new
mechanism and must first preserve edge-degree marginals and graph-specific
aggregate identities, identify a frozen baseline stronger than the vacuous
extremal interval, and demonstrate why the central template no longer applies.

Primary sources: the maintained [Dynamic Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf),
the current [Angeltveit--McKay article](https://doi.org/10.1002/jgt.70029), and
McKay--Radziszowski's [subgraph-counting paper](https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf).
