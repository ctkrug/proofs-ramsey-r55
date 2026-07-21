Best live route: authenticate-and-gate the Springer K43 seed, then exhaust its one-edge non-star neighborhood before any MaxSAT search.

I saved the full 875-word verification memo: [20260721-000000-experiment-verification.md](/root/proof-factory/research/ramsey-r55/workspace/docs/delegate-memos/20260721-000000-experiment-verification.md).

Key discriminator:

- Freeze the two matching publisher bodies from `https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07327-2/MediaObjects/41467_2018_7327_MOESM6_ESM.txt` (SHA-256 `c242…6990`).
- Independently parse the raw 43×43 matrix and exhaust all 903 single-edge flips.
- In particular, test the 741 flips avoiding all four shared conflict vertices. This guarantees any edit changes every relevant 42-vertex deletion remainder, excluding the historically saturated star-extension route.

The frozen seed has two zero-K5s, `[6,12,17,36,42]` and `[6,12,31,36,42]`, no one-K5s, and intersection `{6,12,36,42}`. A direct preliminary scan sets reproducibility targets: global radius 1 remains at burden 2; the strict 741-flip non-star slice has minimum burden 3. These are not accepted findings until rerun through the retained independent gate.

Controls and stop conditions:

- Require byte-identical dual retrievals, publisher URL/TLS metadata, raw-format validation, and separate Python/C raw parsers.
- Verify full violation identities with direct 5-subset enumeration and recursive bitset enumeration.
- Run mutation tests for forced clique/coclique and malformed matrices.
- Stop on any provenance, parser, identity, or score mismatch; stop normally once the finite radius-1 list is exhausted.
- Reject shared normalized parsing, unlogged UNSAT, star-only “repairs,” and any wording that treats the supplied 656 as complete or a local result as a Ramsey result.

The reusable deliverable is a hash-linked `publisher_seed_radius1_report.json`, complete flip ledger, checker/binary hashes, and cold-start replay.
