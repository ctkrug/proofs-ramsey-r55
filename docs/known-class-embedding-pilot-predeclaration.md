# Known-class embedding block: two-record predeclaration

Recorded: 2026-07-21 UTC

Strategy: `strategy-r55-known-class-embedding-block`  
Fingerprint: `r55knownclassembeddingblock2026`

## Scope and falsifiable hypothesis

This is a bounded feasibility and soundness test inside the historical
common-subgraph/extension family.  It is not a census of the supplied 656
classes, not an exclusion of a full isomorphism class, and not a Ramsey
bound.

Freeze the labelled order-30 core obtained from source record 21 by deleting

```text
{2,3,10,12,14,25,27,30,36,37,38,41}.
```

The hypothesis is that every induced embedding of this core into supplied
source records 21 and 12 can be enumerated in less than 30 seconds and less
than 1 GiB by each of two independent implementations, and that the two
implementations emit identical embedding and row-lex boundary-vector sets.
The complement of source record 21 is the negative control and must emit no
embedding.

The decisive observable is exact equality of the sorted embedding streams and
the sorted streams of 426-bit row-lex boundary assignments, followed by a
third replay checker.  The success certificate is the two manifests, exact
stream hashes, every embedding pullback, the two historical positive vectors,
and dual exact five-set checks of every emitted labelled graph.

## Independent implementations and replay

1. `scripts/enumerate_core_embeddings_bitset.py` uses its own short-graph6
   parser and a bit-mask induced-embedding DFS.  It enforces both edges and
   nonedges, dynamically selects the pattern vertex with the smallest feasible
   domain, and applies only sound unused-degree and Hall-union feasibility
   tests.
2. `scripts/enumerate_core_embeddings_networkx.py` lets NetworkX parse graph6
   and exhaustively iterates VF2 induced subgraph isomorphisms.  Its mapping is
   explicitly inverted from host-to-pattern to pattern-to-host.
3. `checkers/known_class_embedding_pilot_audit.py` imports neither enumerator.
   It reparses the corpus, checks every map pairwise, reconstructs every
   labelled completion, checks fixed-core equality and direct row order,
   verifies exact equality to the named host under the recorded bijection,
   compares the complete streams (not only their hashes), and runs the
   existing direct-combinations Python checker and recursive-bitset C checker
   on all unique emitted graphs.  A one-edge mutation and a one-map mutation
   must both be rejected by replay.

For one core embedding, the 12 residual vertices are grouped by their 30-bit
rows into the embedded core.  Row groups have a forced lexicographic order;
all permutations inside tied groups are enumerated because the existing CNF
does not break those ties.  The expansion count is exactly the product of the
factorials of the tie-group sizes.  Exact bitstrings, rather than digests, are
retained in the pilot manifests.

## Search-efficiency pass

The naive deleted-set view examines `C(42,12) = 11,058,116,888` residual sets
per host, before testing an isomorphism or its core automorphisms.  The chosen
search instead builds only adjacency-consistent injections and represents
candidate domains as 42-bit integers.  Mapped-edge and mapped-nonedge filters,
unused neighbor/nonneighbor capacity, most-constrained branching, and a Hall
union check are incremental, sound filters; they do not quotient or omit an
embedding.  The NetworkX path supplies a materially different coverage check.
Vectors are packed as 426-character bitstrings, sorted, and deduplicated
exactly.  No class-level reduction is credited until both exact streams and
the replay checker agree.

## Predeclared decisions

- **Success:** both positive cases finish below 30 seconds/1 GiB per
  implementation, the exact embedding and vector streams agree, record 21's
  identity embedding reproduces the retained row-sorted source, record 12
  reproduces the stored post-block candidate vector, the complement control
  is empty, and all replay/mutation/five-set checks pass.
- **Failure:** any stream mismatch, mapping-orientation error, positive-control
  omission, negative-control embedding, replay failure, checker disagreement,
  or mutation acceptance.
- **Redirect:** either positive case takes at least 30 seconds, any case
  expands above 100,000 boundary vectors, or the measured projection for both
  implementations over 656 hosts exceeds 12 core-hours or 20 GiB.  No
  corpus-wide pass and no residual SAT solve is part of this experiment.

Nearest prior work is McKay--Radziszowski's delete-three/extend closure and
their common-subgraph/neighborhood searches.  The exact local delta is a
complete, replayable set of row-lex boundary pullbacks for each supplied
control, rather than extension enumeration or one labelled SAT block.

Sources:

- https://www.combinatorics.org/ojs/index.php/eljc/article/download/DS1/pdf/0
- https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf
- https://arxiv.org/abs/2409.15709
