# Record-21 destroy-label quotient: predeclaration

Date: 2026-07-21 UTC

Strategy fingerprint: `a230b66ef386`

This is a symmetry-quotient validation experiment inside the historically
explored common-subgraph neighbourhood mechanism.  It is not a new Ramsey
construction method and it is not an exhaustive boundary classification.

## Falsifiable test

Freeze the induced graph on the 30 vertices outside the record-21 destroy set

```text
{2,3,10,12,14,25,27,30,36,37,38,41}.
```

Regenerate all raw Ramsey clauses on the 426 boundary edges, remove the old
source-relative Hamming counter completely, and require the twelve 30-bit
destroyed-to-core rows to be lexicographically nondecreasing.  Adjacent row
comparators use exact prefix-equality auxiliaries.

The small coverage gate ranges over every one of the `2^21 = 2,097,152`
labelled graphs on four fixed and three destroyed vertices.  It must exercise
all-distinct, one-tied-pair, and all-tied row multiplicities.  A separate truth
table must show that the comparator CNF is satisfiable for exactly the directly
ordered pairs and that its prefix assignment is unique.

After that gate, directly sort the authenticated source record 21 and require
that it satisfies the regenerated raw-plus-lex CNF.  Block exactly that one
426-bit canonical primary vector, then allow one CaDiCaL model with seed 1,
30 seconds, and a 1 GiB address-space limit.

## Decision signals

- Prediction: every small graph retains a sorted representative; the sorted
  record-21 source is a positive control.
- Success: all controls pass and the one post-block model passes full DIMACS
  evaluation, direct row-order checking, both exact five-set checkers, and
  canonical corpus classification.
- Failure: any small orbit loses coverage, the gadget differs from direct lex
  order, a tied-row case is lost, the Hamming counter remains, or any checker
  disagrees.
- Redirect: timeout, unproved UNSAT, or one valid supplied-class model.  Stop
  after that one model; do not resume labelled CEGAR.

## Search-efficiency ledger

The naive boundary contains `2^426` labelled assignments.  The `S_12` action
on destroyed labels preserves the frozen core and every Ramsey clause.  Sorting
core rows gives at least one representative per orbit.  With 12 distinct rows,
the representative is unique and the labelled orbit has size `12! =
479,001,600`; with ties, coverage remains but uniqueness and this factor are
not claimed.  The old Hamming restriction is non-invariant and is therefore
removed, along with its 155,550 auxiliaries and 311,159 clauses.

Nearest prior-art method IDs: `common-edge-subgraph-neighborhoods`,
`random-36-subgraph-extension`, and `known-class-avoidance-bias`.  The exact
delta is static destroy-label canonicalization and its exhaustive tied-row
coverage check; the expected first-model result is only a control.

