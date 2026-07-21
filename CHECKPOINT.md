# R(5,5) research checkpoint — epoch 6

Recorded: 2026-07-21 00:08:55 UTC

## Outcome and exact scope

Springer Supplementary Data 4 is now authenticated as the published
two-conflict K43 seed, and its complete Hamming-radius-1 edge neighborhood is
exhausted. This is a reproducible local-landscape result and research artifact,
not a Ramsey witness, bound, global multiplicity optimum, or order-42 census.
The maintained published status remains `43 <= R(5,5) <= 46`.

For exactly the frozen 43-vertex matrix with SHA-256
`c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990`:

- it has 454 one-edges;
- its only monochromatic K5s are the all-zero sets
  `[6,12,17,36,42]` and `[6,12,31,36,42]`;
- all 903 one-edge flips have total monochromatic-K5 burden at least 2;
- the two global radius-1 minimizers are flips `(6,12)` and `(36,42)`,
  both with burden 2;
- among the 861 flips not incident to vertex 6, the unique minimum is
  `(36,42)` with burden 2;
- among all 741 flips avoiding every shared conflict vertex
  `{6,12,36,42}`, the exact minimum is 3, attained by
  `(0,37)`, `(5,11)`, `(10,16)`, `(16,22)`, `(21,27)`, `(26,32)`, and
  `(32,38)`.

The last predicate is a strict non-star firewall: its changed edge remains in
the graph after deleting any of the four shared conflict vertices. It therefore
changes every relevant order-42 deletion remainder, though it says nothing
about larger edit sets or unknown order-42 components.

## Source and provenance gate

Primary article: https://doi.org/10.1038/s41467-018-07327-2

Publisher object:
https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt

Two direct retrievals are retained as
`sources/retrievals/springer_supplementary_data4_audit{1,2}.{txt,headers}`.
Both bodies are 3,812 bytes and byte-identical. Each retrieval record reports
HTTP/2 200, verified TLS, no redirect, the publisher-controlled effective URL,
`Content-Type: application/octet-stream`, and the correct byte count:

- `.proof-experiments/20260720-235158-0cfef1`;
- `.proof-experiments/20260720-235208-a7e84e`.

The gate hash-links both bodies, both raw header captures, both curl transfer
records, and both experiment JSON files. It refuses a changed body even if the
changed matrix remains structurally valid.

## Decisive experiment

Experiment: `.proof-experiments/20260721-000810-1f70a4`

- Return code 0; duration 45.243 s; 1,024 MB cap; peak child RSS 34,560 KiB.
- Experiment JSON SHA-256:
  `3ce459a1a214f1c86dcc9351e4cabbae961a210785cab8e576c78c2f0dc8f98f`.
- Report: `artifacts/publisher_seed_radius1_report.json`, 1,544,868 bytes,
  SHA-256
  `0db3cca75888b70850b60e1b891d8e08349ab0bec6196cd8f4c528603fa04fe9`.
- The report retains the ordered 903-entry flip ledger, full violation
  identities, family histograms, minimizer identities, provenance, mutations,
  parser rejections, deletion membership, checker/compiler hashes, and 41
  direct rescans.

Checker A (`checkers/publisher_radius1_a.py`, SHA-256
`f34ea148c36ab74b0c11784f9b4d333dc915ef0a6bd3d70c7ef9c2aa03f5a535`)
independently parses the raw whitespace in Python, scans all `C(43,5)` subsets,
and derives exact one-edge deltas. Checker B
(`checkers/publisher_radius1_b.c`, SHA-256
`b1bfd2a51511ae0f3e6caccbaa29235cf65df2f8a3cae7ccdfce934af1f5914a`)
parses fixed raw byte positions in C and recursively enumerates K5s in the graph
and complement afresh after every flip. Their complete identity ledgers agree.

The report additionally rescans every family minimizer and one representative
of every global burden class with both full evaluators. Forced clique and
coclique mutations are detected. Both parsers reject nonbinary, shortened,
nonzero-diagonal, asymmetric, and substituted-Gist inputs. A UBSan build of
Checker B also reproduced the retained 903-entry ledger with no diagnostic:
`.proof-experiments/20260721-001630-5af604`, experiment JSON SHA-256
`2d22200322a85d0874f75253e86be41eda5500c1bfc7a57f1f4ea8f648a07032`.

An attempted combined ASan+UBSan replay under the harness's 1,024 MB
`RLIMIT_AS` aborted before evaluation because ASan requires a much larger
virtual shadow reservation. The captured failure is
`.proof-experiments/20260721-001555-dfd5af`, experiment JSON SHA-256
`969331a4fdfc9d8083fb545888d5093b42f6fdb9451c0ca465a13491dd16c6a8`.
The durable repair is the UBSan-only audit above; the ASan failure is not a
checker failure and is not counted as validation.

An initial development version of Checker A failed the cross-check because its
delta ledger omitted seed conflicts unaffected by the changed edge. That result
was discarded, the recurrence was corrected, and the official experiment was
run only after complete identity agreement. This failure is preserved here to
prevent reintroducing the defect.

## Deletion and novelty firewall

The two conflicts intersect in `{6,12,36,42}`. Deleting any member yields a
valid order-42 graph because the seed's complete violation list contains only
those two sets. `nauty-labelg` places all four deletions in the authenticated
supplied-656 packet:

- delete 6 or 42: canonical SHA-256
  `ee2269437c3ba4cd8cde512768489089a5865ab701b38e8716acaddcdd07c3a7`,
  complement of supplied record 42;
- delete 12 or 36: canonical SHA-256
  `3f16d9a422f89c250bebd7d50fa6cb4006de0655513bac24f34232d2620c623f`,
  complement of supplied record 256.

This is membership in the supplied 656 only. It does not prove completeness.
Ordinary star-only extension from these deletions remains historically
saturated and should not be reopened.

## Cold replay

From the repository root:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-publisher-seed-radius1-replay \
  --hypothesis "The retained authenticated publisher seed has no radius-1 witness and its strict avoid-intersection slice has minimum burden 3" \
  --expected-signal "Byte/provenance/mutation gates pass and both exact implementations reproduce all 903 identities, global minimum 2, and strict 741-flip minimum 3" \
  --timeout 240 --memory-mb 1024 \
  --source-url 'https://doi.org/10.1038/s41467-018-07327-2' \
  --source-url 'https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt' \
  -- python3 scripts/run_publisher_radius1_gate.py \
  checkers/publisher_radius1_a.py checkers/publisher_radius1_b.c \
  sources/retrievals/springer_supplementary_data4_audit1.txt \
  sources/retrievals/springer_supplementary_data4_audit2.txt \
  artifacts/authenticated_corpus_report.json \
  artifacts/publisher_seed_radius1_report.replay.json
```

Require the replay report's mathematical fields to equal the retained report;
the report hash itself may differ because absolute temporary compiler paths or
tool metadata can change only if the script is later revised. Stop immediately
on any source, parser, mutation, canonical, or ledger mismatch.

## Exact continuation

Continue strategy `strategy-r55-conflict-core`, fingerprint `r55twocore2026`.
The next discriminator is the full Hamming-radius-2 neighborhood:
`C(903,2)=407253` unordered two-edge flips.

Implement two materially different evaluators:

1. a C evaluator that toggles each lexicographically ordered edge pair and
   recursively enumerates K5s in the graph and complement;
2. a Python evaluator that scans each 5-set and accounts exactly for whether
   zero, one, or both edited edges lie in that 5-set.

Retain a compact complete pair-score ledger and full identities for every
minimizer. Separately report the deletion-remainder-change slice defined by:

```text
for every v in {6,12,36,42}, at least one edited edge is not incident to v.
```

This predicate ensures the two-edge edit changes each of the four known
deletion remainders. It is broader than requiring one edge to avoid the whole
intersection.

Stop on the first provenance, parser, ordering, score, or identity mismatch.
Otherwise stop after all 407,253 pairs are recorded and independently agreed.
A zero must pass both complete exact checkers. A nonzero minimum is only a
radius-2 statement; it is not a Ramsey bound. Do not start radius 3 or a
MaxSAT/UNSAT claim in the same pass unless radius 2 changes the decision and a
new explicit certificate contract is written.

## Tool and delegate disclosure

GPT-5.6 Sol was principal investigator. Two precomputed GPT-5.6 Terra delegates
provided advisory literature-strategy and experiment-verification memos. Sol
hash-verified their original memo files, independently inspected the primary
bytes and experiment records, implemented the retained checkers/gate, caught a
delta-checker defect through cross-encoding disagreement, and ran the official
experiment. No new subagent was spawned.

Deterministic tools used: Python 3.12.3, C/GCC 13.3.0, nauty `labelg`, curl
8.5.0 with OpenSSL 3.0.13, SHA-256, jq, Git diagnostics, AddressSanitizer,
UndefinedBehaviorSanitizer, an attempted AddressSanitizer run limited by the
harness address-space cap, and the computational-researcher experiment harness.
No SAT solver, CAS, or proof assistant was used.
