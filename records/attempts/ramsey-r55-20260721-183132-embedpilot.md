# Research attempt ramsey-r55-20260721-183132-embedpilot

Outcome: progress, not a Ramsey result.

## Exact scoped result

For the fixed labelled order-30 core from supplied source record 21, a custom
graph6/bitset DFS and NetworkX graph6/VF2 emitted identical complete streams:

```text
host                  embeddings   unique row-lex vectors
source record 21               2                        1
source record 12               2                        2
complement record 21           0                        0
```

All residual rows in the two positive hosts are distinct. The third checker
replayed every induced map and host pullback, recovered the retained row-sorted
record-21 graph and post-block record-12 candidate, rejected a one-edge vector
mutation and a map transposition, and had both exact five-set checkers accept
all three distinct labelled graphs.

The worst observed positive-host sum of the two implementation times is
30.7203 seconds, projecting to 5.5979 core-hours for 656 host
representations. This is only an estimate: unseen hosts can have more
embeddings or tied residual rows.

No boundary assignment was blocked, no supplied isomorphism class was fully
excluded, and `43 <= R(5,5) <= 46` is unchanged.

## Reproduction

Commands and limits are preserved in:

- `.proof-experiments/20260721-182632-8096f2`
- `.proof-experiments/20260721-182712-0ba9c4`
- `.proof-experiments/20260721-183048-41afe5`

The exact predeclaration is `docs/known-class-embedding-pilot-predeclaration.md`.
The decisive manifests are `artifacts/known_class_embedding_bitset_pilot.json`,
`artifacts/known_class_embedding_networkx_pilot.json`, and
`artifacts/known_class_embedding_pilot_audit.json`.

## Continuation

Generalize both enumerators into an atomic per-host checkpoint driver and
submit the complete 328-source-plus-328-complement reconciliation to the
checkpointed lab. Stop on any mismatch, per-host time at least 30 seconds,
1-GiB breach, tied expansion above 100,000, or aggregate projection above 12
core-hours/20 GiB. Do not emit blocks or call SAT on partial output.

GPT-5.6 Sol was principal. Supplied GPT-5.6 Terra delegates were advisory; no
new subagent was spawned. Full disclosure and hashes are in the JSON record.
