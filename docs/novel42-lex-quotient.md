# Record-21 destroy-label quotient: exact scoped result

Recorded: 2026-07-21 17:24 UTC

Strategy: `strategy-a230b66ef386` / fingerprint `a230b66ef386`

## Outcome

The static `S_12` quotient is sound for the retained source-record-21 frozen
core, including tied core-neighbourhood rows.  It is an exact local
search-space reduction, not a class block and not a Ramsey bound.

The 30-vertex core fixes 435 of the 861 order-42 edge variables.  Among the
remaining 426 variables, 360 encode destroyed-to-core rows and 66 encode
destroyed-to-destroyed edges.  Requiring the twelve 30-bit rows to be
nondecreasing changes the represented primary space from

```text
2^426
```

to exactly

```text
2^66 * C(2^30 + 11, 12).
```

Thus the exact labelled-assignment reduction factor is

```text
2^360 / C(2^30 + 11, 12) = 479001570.5570708...
```

which is slightly less than `12! = 479001600` because tied rows retain more
than one representative.  Every orbit remains covered.  With distinct rows,
the representative is unique and the full `12!` factor applies.

## Exhaustive coverage gate

The producer enumerated all `2^21 = 2,097,152` labelled graphs on four core
and three destroyed vertices.  For each graph it explicitly permuted every
edge, including destroyed-to-destroyed edges, by stable row sorting; the core
was unchanged and the output rows were ordered.  The exact row census was:

```text
all distinct      1,720,320
one tied pair       368,640
all tied              8,192
directly sorted      417,792
S_3 orbits           382,976  (Burnside count)
```

The four-bit comparator truth table covered all 256 row pairs and all eight
assignments to its three prefix auxiliaries.  Exactly the 136 directly ordered
pairs had one satisfying prefix assignment; every other pair had none.

The delegates projected 175 clauses per 30-bit comparator.  Sol's exact
encoding and truth table show that 174 suffice: 30 ordering clauses, four
clauses for the first equality prefix, and five clauses for each of the next
28 prefixes.  Consequently the physical counts are 319 lex auxiliaries and
1,914 lex clauses, not 1,925.

## Production control

The regenerated boundary contains exactly 196,998 raw Ramsey clauses.  The
old source-relative Hamming counter is completely absent.  The row-sorted
record-21 graph has 12 distinct rows and satisfies all 198,912 raw-plus-lex
base clauses.  A single 426-literal clause then blocks exactly this one primary
vector.

The resulting physical formula has 745 variables and 198,913 clauses,
SHA-256 `92eb867d7e523e673de1b9ea2b848600abf793eacad0b59cce7861cfc94fbe41`.
CaDiCaL 1.7.3, seed 1, returned SAT in 4.849 seconds under the predeclared
30-second/1-GiB limit.  Both exact full-graph checkers accepted the model.
Nauty classified it as supplied source record 12, so the predeclared stop
condition fired.  No additional model was requested.

The adversarial cold audit imports no producer.  It independently rebuilt all
196,998 raw clauses, rebuilt all eleven physical lex gadgets, evaluated all
198,913 clauses, obtained clique number four in the graph and complement, and
confirmed the record-12 target with NetworkX isomorphism.  Swapping the first
two distinct-row destroyed labels preserved all raw Ramsey clauses and the
frozen core but was rejected by the lex clauses, as required.

## Scope and disposition

This packet establishes quotient coverage only for label permutations of the
12 destroyed vertices with this labelled order-30 core fixed.  It does not
quotient core automorphisms, block an order-42 isomorphism class, enumerate all
boundary completions, prove the 656 controls complete, or change
`43 <= R(5,5) <= 46`.

Do not continue this boundary with an arbitrary normal-form budget.  The
single post-block model is another supplied class, and no sound compact
class-level block exists.  The next bounded discriminator should redirect to
`strategy-r55-two-orbit-proof-compression`: deletion-minimize one certified
raw K5-clause refutation and stop immediately if its core exceeds 20 clauses;
only then consider the 20-distance atlas and five-template threshold.

## Reproduction

Production:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-record21-lex-quotient \
  --hypothesis 'The S_12 row-order quotient retains every small tied-row orbit, the row-sorted record-21 source satisfies the no-Hamming CNF, and one post-source-block model is exactly checkable.' \
  --expected-signal 'The 2^21 small gate and 256-pair gadget gate pass; the source control satisfies 198912 base clauses; one seed-1 30-second solve returns a dual-checked classified model or an explicit bounded stop.' \
  --timeout 240 --memory-mb 2048 \
  --source-url https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf -- \
  python3 scripts/run_novel42_lex_quotient.py \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json \
  checkers/checker_a.py checkers/checker_b.c \
  artifacts/novel42_lex_quotient artifacts/novel42_lex_quotient_report.json \
  30 1 21
```

Adversarial cold replay:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-record21-lex-quotient-adversarial-cold-audit \
  --hypothesis 'The physical lex gadgets equal a separate reconstruction, and a destroy-label transposition preserves all raw Ramsey clauses while being rejected solely by row order.' \
  --expected-signal 'The checker matches all 11 gadgets, the transposed source satisfies 196998 raw clauses, and the lex clauses reject its unsorted distinct rows.' \
  --timeout 180 --memory-mb 2048 \
  --source-url https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf -- \
  python3 checkers/novel42_lex_quotient_audit.py \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json \
  artifacts/novel42_lex_quotient_report.json artifacts/novel42_lex_quotient \
  artifacts/novel42_lex_quotient_cold_audit_v2.json
```

Key artifacts:

```text
production experiment  .proof-experiments/20260721-172006-427f4a
adversarial audit       .proof-experiments/20260721-172356-d34034
production report       b3dba7917002fc7f49fdaefe25bc65e79a51f461878405f38233bd467f7e33ee
cold audit v2           edcde85e7fff664770a7e26f32d531cab9cb338c5814842901cff132923ec7ab
physical CNF            92eb867d7e523e673de1b9ea2b848600abf793eacad0b59cce7861cfc94fbe41
post-block graph6       26b331eb29478b6920883bd72d389c98952171026871143829435c87ae8ba5ce
```

## Sources and disclosure

- https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf

GPT-5.6 Sol was principal investigator.  Supplied GPT-5.6 Terra
literature-strategy and experiment-verification memos were advisory; Sol
audited their claims, corrected the comparator count, implemented the
experiment, and wrote the independent checker.  No new subagent was spawned.
Deterministic tools were Python 3.12.3, GCC 13.3.0, CaDiCaL 1.7.3, nauty
`labelg`, NetworkX 3.3, jq, pdftotext, curl, SHA-256, and the
computational-researcher experiment harness.  No CAS, proof assistant,
external publication, remote account, or system-level change was used.
