# Terra experiment-verification memo: known-class embedding blocks

Source: `.delegates/20260721-181713-93cca4/experiment-verification/memo.md`  
Source SHA-256: `b86d23872f8789c6b75be5ce996a294045763347b5a707dc1ba244649369a7b9`

## Recommended bounded pilot

Enumerate every induced embedding of the fixed labelled order-30 core into
supplied records 21 and 12, then emit and deduplicate every row-lex-accepted
426-bit boundary vector. Use two independent implementations: a custom
graph6/bitset induced-embedding DFS and NetworkX graph6/VF2 exhaustive
enumeration. For each embedding, enumerate all residual orders compatible
with nondecreasing 30-bit rows, including every order within tied rows.

Required controls were:

- record 21 includes the identity embedding and reproduces the retained
  row-sorted source;
- record 12 emits the stored post-block candidate vector;
- complement record 21 emits zero embeddings;
- a separate replay checker verifies fixed-core equality, direct row order,
  exact host pullback, and both exact five-set checks;
- compare exact mapping/vector sets and deterministic stream hashes;
- corrupt one edge and one mapping record and require both to fail replay.

Stop before any corpus-wide pass or residual SAT if either positive case takes
at least 30 seconds or 1 GiB, implementations disagree, the negative control
emits anything, tied-row expansion exceeds 100,000 vectors, or projected full
work exceeds 12 core-hours or 20 GiB.

The memo emphasized that the 656 supplied graphs are not a complete census,
that one vector per tied row class is unsound, and that residual UNSAT after
blocking supplied controls would not be a global Ramsey upper bound.

Sol disposition: accepted as the predeclared verification plan. Sol wrote and
ran both enumerators and the independent replay checker; the retained artifacts
are the evidence, not this memo.
