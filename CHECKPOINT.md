# R(5,5) research checkpoint — epoch 5

Recorded: 2026-07-20 22:37 UTC

## Outcome and exact scope

The authoritative-source control blocker for McKay's supplied order-42 corpus
is closed. This is research-software progress, not a Ramsey-number result. No
new witness, bound, classification, target-instance exclusion, or canonical
novelty claim is made. The maintained rigorous status remains
`43 <= R(5,5) <= 46`.

Exactly 328 supplied order-42 graph6 records and their 328 derived complements
passed the full control gate. This does **not** prove that those 656 graphs are
all `(5,5,42)` graphs.

## What changed

A newly live command-network route enabled a second direct HTTPS retrieval from
McKay's authoritative URL:

`https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6`

The actual HTTP/2 200 response omits `Content-Type`. The prior sidecar's
inference of `text/plain` was rejected. Provenance schema v2 instead preserves
the missing field as `null` and requires hash-linked copies of:

- the raw response headers;
- the independently retrieved body;
- curl's transfer/TLS JSON;
- the deterministic retrieval experiment record.

The second body is byte-for-byte equal to the previously supplied body and to
the frozen acquisition discriminator:

- 47,888 bytes;
- 328 nonblank LF-terminated records;
- SHA-256
  `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.

## Decisive experiments

### Second authoritative retrieval

Experiment: `.proof-experiments/20260720-221528-34af71`

- Return code 0; duration 0.826 s; 256 MB cap.
- HTTP/2 200; TLS verification result 0; no redirect.
- `url_effective` is the authoritative URL.
- `content_type` is `null` in curl metadata and no `content-type` field occurs
  in the raw header block.
- Body: `sources/retrievals/r55_42some_authoritative_epoch5.g6`, SHA-256
  `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.
- Headers: `sources/retrievals/r55_42some_authoritative_epoch5.headers`,
  186 bytes, SHA-256
  `15d2e458cdc5a91c7c562460a91b15c0db15953c7e8174324aa1074063eaa430`.
- Experiment JSON SHA-256:
  `e05052b4db512684c45c9efb64654cfd1f32a8edfffdba1b8e8bfc5fab3ac233`.

### Provenance-v2 and graph6 regression

Experiment: `.proof-experiments/20260720-221937-5c7218`

- Return code 0; duration 1.389 s; 1,024 MB cap.
- A fixture with an explicitly absent `Content-Type` was accepted only when
  linked raw header/body/transfer/experiment artifacts agreed.
- Mutations to source authority, byte count, inference status, and raw-header
  hash were rejected.
- Both exact checkers, NetworkX, and `nauty-complg` retained full agreement on
  every one of the 1,044 unlabeled order-7 classes and their complements.
- Report: `artifacts/graph6_provenance_v2_regression.json`, SHA-256
  `c3f0b3d7a0a29b093bd151201669aa63b81870f453b3c979f4d6821923744421`.
- Experiment JSON SHA-256:
  `f4f49fe131916090d9123b3e2e937c32b17b78e94ca1e22b994bf989a95a5e19`.

### Full supplied-656 target gate

Experiment: `.proof-experiments/20260720-221949-1e01b8`

- One non-overlapping run; return code 0; duration 997.687 s; 2,048 MB cap;
  peak child RSS 41,964 KiB.
- Checker A: independently parsed Python Boolean matrices and direct exhaustive
  5-subset enumeration.
- Checker B: separately parsed C graph representation and recursive bitset
  clique enumeration; compiled binary SHA-256
  `f5e73e3a83cfff969b321e3288c7d90d083ddbc1517bba90a0d44e56ac455f51`.
- Both checkers found zero 5-cliques and zero independent 5-sets on all 656
  supplied/derived instances.
- NetworkX agreed with both checker parsers on every complete 861-bit adjacency
  fingerprint.
- Local complement bytes matched `nauty-complg` byte-for-byte; output SHA-256
  `8a8834f23a13d589df702df4016f308562c2226c445231ba2ea484f2e288d662`.
- Base edge histogram was exactly
  `{423:1,424:7,425:29,426:66,427:89,428:77,429:43,430:16}`.
- Degree range across the 656 instances was exactly 19..22.
- `nauty-labelg` produced 656 distinct canonical labels.
- The entire 328-entry per-record manifest and all decisive graph fields equal
  the prior host-side run; that earlier run's provenance was not accepted.
- Report: `artifacts/authenticated_corpus_report.json`, SHA-256
  `0d9b1801434edcc12f34e73cea6c98d911f0e0c6f0884f8f03d96a46eca1344c`.
- Experiment JSON SHA-256:
  `64332bc455ae9d04f743df14063910977e5f49c064ccd30a58f9c183322f3fca`.

## Current source/status audit

- Dynamic Survey DS1.18, revision 2026-04-24, reports the range 43..46 and
  describes the 656 count as strong evidence rather than a proved census:
  https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- McKay's maintained data page says the file contains 328 representatives and
  the other 328 are complements, while leaving open additional order-42 and
  larger graphs:
  https://users.cecs.anu.edu.au/~bdm/data/ramsey.html

## Exact continuation

Objective: authenticate unchanged Springer Supplementary Data 4, the published
two-conflict K43 seed. Do not begin conflict-core repair, deletion novelty
comparison, or unknown-42 search before this source gate passes.

First run this bounded raw retrieval from the repository root:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-springer-supplementary-data4-retrieval \
  --hypothesis "The publisher raw TXT is directly retrievable with immutable body and response metadata" \
  --expected-signal "Verified HTTPS response from the Springer raw URL, retained unchanged body and raw headers, and curl transfer JSON suitable for a fail-closed source gate" \
  --timeout 120 --memory-mb 256 \
  --source-url 'https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt' \
  -- curl --proto '=https' --tlsv1.2 --fail-with-body --silent --show-error \
  --location \
  --dump-header sources/retrievals/springer_supplementary_data4.headers \
  --output sources/retrievals/springer_supplementary_data4.txt \
  --write-out '%{json}\n' \
  'https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt'
```

Stop immediately if TLS verification fails, the final URL is not publisher
controlled, the response is not successful, the body is HTML/error content, or
two immediate direct retrievals differ. Preserve all divergent bytes and
metadata unchanged.

If retrieval is stable, create a source sidecar modeled on schema v2 without
inventing missing headers. Then write a dedicated publisher-seed gate that:

1. parses the raw publisher representation without using the gist parser;
2. identifies the color convention under both exact checkers;
3. requires the exact conflict identities to agree;
4. compares any claimed transformation to the provisional gist byte/object
   explicitly, rather than assuming provenance;
5. lists all valid vertex deletions and only then canonicalizes them against
   the authenticated supplied 656.

Only after that gate passes should one bounded six-vertex conflict-core repair
slice be attempted. A zero must pass both exact checkers; an UNSAT neighborhood
claim needs a checked exact certificate and applies only to that frozen slice.

## Delegate provenance and tool disclosure

GPT-5.6 Sol was principal investigator. Two precomputed GPT-5.6 Terra memos
were advisory. Sol hash-verified both. The experiment-verification memo
identified the inferred-Content-Type defect and recommended the second raw
retrieval plus one non-overlapping full gate; Sol independently inspected the
actual response, designed and mutation-tested provenance schema v2, and ran the
target gate. The substantive memo is retained at
`docs/delegate-memos/20260720-221349-experiment-verification.md`; provenance is
recorded in `records/delegate-provenance-epoch5.json`. The literature memo was
not used as decisive evidence. No new subagent was spawned.

Deterministic tools used: Python 3.12.3, C/GCC, curl 8.5.0 with OpenSSL 3.0.13,
NetworkX 3.3, nauty, SHA-256, Git diagnostics, and the
computational-researcher experiment harness. Web browsing checked the maintained
survey and authoritative data pages. No SAT solver or proof assistant was used.
