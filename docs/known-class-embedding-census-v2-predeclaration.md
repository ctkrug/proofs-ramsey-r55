# Known-class embedding census v2 predeclaration

Date: 2026-07-21

## Why v2 starts at host 0

The first job stopped after 49 hosts because its lab spec omitted the two imported-enumerator hashes,
did not record a clean protected-input boundary, and did not enforce the declared 30-second aggregate
host gate. Those 49 mutually agreeing receipts remain calibration evidence but are not part of this
census. V2 uses fresh checkpoint, progress, output, manifest, and job identifiers; no v1 row is copied.

## Immutable inputs

- runner: `scripts/run_known_class_embedding_census.py`, SHA-256
  `d571103060c50a82bc6b7d41c7affabc4062ef975750da397bacf93ae81623dc`;
- locked wrapper: `scripts/run_known_class_embedding_census_locked.sh`, SHA-256
  `4641fae36fd53c1b196696cee54cb5d846fcd6907b4a5a65ebb6c723b1c867a7`;
- bitset enumerator: SHA-256
  `01b3953b1db6a65737e4fb4ee176a88b7c8c8ed26a374c410cf274fe2500739a`;
- NetworkX enumerator: SHA-256
  `c4491591b16394e11d3bf0b907eea8c65a73308e8a2a366e5d594532c7010aaf`;
- 328-record corpus: SHA-256
  `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.

The wrapper checks the four non-wrapper hashes itself and refuses protected paths that differ from
the committed revision. The lab spec must additionally hash the wrapper, runner, both enumerators,
and corpus. Submission occurs only after this document and all protected inputs are committed with a
clean tracked worktree.

## Pilot and continuation gates

The local fresh host-0 canary completed in 15.149 seconds with exact implementation agreement. The
deployed pilot repeats host 0 in a one-host v2-canary namespace. Only a validated pass may authorize a
fresh 656-host job. That full job begins at host 0, pauses after its first measured segment, and then
uses 256-segment reviewed tranches. Each host has a 30-second aggregate wall gate across both
implementations; any timeout, implementation disagreement, correctness failure, missing checkpoint,
throughput below 0.001 host/second, or per-segment artifact growth above 200 MB stops automatically.

The decisive artifact is a complete 656-row ordered manifest whose host artifacts replay under the
standalone validator. Residual SAT is forbidden until this complete artifact passes independent
validation. A new order-42 class, if later found, must stop for dual checking and human review; no
automatic publication or scale-up is authorized.
