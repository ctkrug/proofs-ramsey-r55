# R(5,5) research checkpoint — epoch 7

Recorded: 2026-07-21 01:10:03 UTC

## Outcome and exact scope

Springer Supplementary Data 4 is now authenticated as the published
two-conflict K43 seed, and its complete Hamming-radius-1 edge neighborhood is
exhausted through radius 2.  The seed's only two radius-2 minimizers are
isomorphic translations of the seed, and the complete 43-bit cyclic-distance-6
slice containing it is exactly classified. These are reproducible local and
structured-slice results, not a Ramsey witness, bound, global multiplicity
optimum, or order-42 census. The maintained published status remains
`43 <= R(5,5) <= 46`.

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
- all `C(903,2)=407253` distinct two-edge flips have burden at least 2;
- exactly two radius-2 pairs attain 2:
  `{(6,12),(9,15)}` and `{(33,39),(36,42)}`;
- the 403,809-pair deletion-remainder-change slice also has minimum 2 at
  exactly those two pairs.

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

## Complete radius 2

Experiment: `.proof-experiments/20260721-005729-caca87`

- Return code 0; duration 39.595 s; peak child RSS 124,698,624 bytes.
- Report: `artifacts/publisher_seed_radius2_report.json`, SHA-256
  `ee32f396c898894d32ffcbe69987caded6731f32398ce3be28cfde1d1b9c107a`.
- Compact complete score ledger:
  `artifacts/publisher_seed_radius2_scores.u16le`, 814,506 bytes, SHA-256
  `60ba5158f8d7579785e026a9f00f0722a61fb8d47ed4d279ae128c419c524edb`.

Checker A scans all `C(43,5)` five-sets once and applies exact two-edit
contribution cases. Checker B toggles each pair in C and recursively enumerates
K5s in the graph and complement afresh. They agree entry-for-entry on all
407,253 burdens and on every minimizer identity. Eight independently selected
pairs were also rescanned for full identities.

The only radius-2 minimizers merely relocate the two conflicts:

- `{(6,12),(9,15)}` leaves zero K5s `[4,9,15,22,28]` and
  `[9,15,22,28,33]`;
- `{(33,39),(36,42)}` leaves zero K5s `[1,20,26,33,39]` and
  `[15,20,26,33,39]`.

Nauty canonical labels and explicit NetworkX mappings show that these are the
seed relabeled by vertex rotations `u -> u-27` and `u -> u+27` modulo 43,
respectively. Thus radius 2 exposes no new burden-2 isomorphism class.

## Exact distance-6 slice classification

Experiment: `.proof-experiments/20260721-010952-d08716`

- Return code 0; duration 10.882 s; peak child RSS 66,306,048 bytes.
- Report: `artifacts/distance6_slice_exact_report.json`, SHA-256
  `8c8c64a82c84913222578fad537cc9beb73e74de5260a84090b9406f798a9fb1`.

Twenty of the seed's 21 cyclic-distance edge orbits are constant. The sole
exception is distance 6. If `x_u` colors edge `{u,u+6 mod 43}` and coordinates
are changed to `u=27t mod 43`, every potentially monochromatic K5 in this
43-variable slice reduces to translations of only three constraint shapes:

```text
x_t or x_(t+18)                 (multiplicity 2)
x_t or x_(t+20)                 (multiplicity 2)
not x_t or not x_(t+5) or not x_(t+24)  (multiplicity 1)
```

There are 215 active five-sets and 129 unique constraints. An independent
Python/Z3 pseudo-Boolean enumeration and a custom C relaxation-case DPLL agree
that burdens 0 and 1 are UNSAT, burden 2 is attainable, and there are exactly
86 optima. They are precisely:

- 43 rotations of one step-27 cyclic interval of 24 ones;
- 43 rotations of one step-27 cyclic interval of 25 ones.

The publisher seed is one length-24 interval. Its distance-6 word is
`0111000111001110011100011100111001110001110` in vertex order and
`0000001111111111111111111111110000000000000` in step-27 order. Six full
graph/complement K5 rescans agree with the reduced burdens. This exhausts all
`2^43` assignments in this one-orbit ansatz, not the whole graph space.

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

Continue the conflict-core route as a cyclic-domain-wall CSP rather than an
unstructured Hamming-ball search. The first discriminator is the 20-slice
sweep obtained by releasing distance 6 together with exactly one of the other
20 cyclic-distance orbits, leaving the remaining 19 orbits frozen.

For each 86-variable slice:

1. derive every active K5 clause directly from the frozen matrix;
2. symmetry-break the common vertex-rotation action without excluding an
   orbit of assignments;
3. ask first for burden 0, then minimum burden only when the SAT question is
   resolved;
4. decode every SAT model to a 43-vertex matrix and require both complete K5
   checkers before retaining it;
5. treat an UNSAT response as a search discriminator unless a deterministic
   CNF and independently checked proof log are retained.

Rank second orbits by achieved exact burden and by factor-graph width. The
prediction is concrete: if the one-dimensional defect must escape by coupling
to another orbit, at least one two-orbit slice should beat burden 2 or expose a
small recurrent obstruction suitable for a transfer-matrix or trapping-set
lemma. If all 20 slices have certified minimum 2 and only symmetry copies,
close this near-circulant family and redirect compute to multi-orbit/nonlocal
surgery. Do not launch all `C(903,3)` flips first; radius 2 already shows that
the apparent local moves only translate the domain wall.

## Tool and delegate disclosure

GPT-5.6 Sol performed the epoch-7 local work without spawning a subagent. It
implemented both radius-2 evaluators, the exact slice encodings, the custom C
DPLL, the fail-closed gates, direct rescans, and the cyclic/isomorphism
analysis. Earlier epoch-6 delegate memos remain advisory provenance only.

Deterministic tools added in this epoch: Python 3.14.6, C/Apple Clang 17,
Z3 4.15.4, remote Debian nauty `labelg`, NetworkX explicit isomorphism maps,
SHA-256, Git diagnostics, and the computational-researcher experiment harness.
Z3 and the custom DPLL independently enumerated the complete optimum model set;
no global Ramsey SAT/UNSAT claim, CAS result, or proof-assistant theorem was
made.
