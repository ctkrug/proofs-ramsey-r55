# R(5,5) research checkpoint — epoch 1

Recorded: 2026-07-20 UTC

## Outcome and scope

Internal progress only; no new Ramsey bound, witness, classification, or
nonexistence result is claimed.  The maintained status remains
`43 <= R(5,5) <= 46`.

This epoch continued strategy `r55controls2026` and stopped at its required
source gate.  The exact evaluators and graph6 plumbing passed adversarial
controls.  The authoritative McKay order-42 corpus was not locally available,
so the corpus gate returned `source_preflight_failed` and explicitly recorded
`downstream_checks_run: false`.  No novel-42 search, K43 repair, SAT exclusion,
or canonical comparison against the 656 was started.

## Decisive observations

1. Current-source check: Dynamic Survey revision 18 (24 April 2026) and the
   2026 journal publication still support `43 <= R(5,5) <= 46`.
2. McKay's maintained data page still describes 328 supplied representatives
   and their 328 complements, without claiming completeness.
3. A public Hugging Face mirror page exposes an LFS metadata discriminator for
   `r55_42some.g6`: exactly 47,888 bytes and SHA-256
   `067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`.
   This is not authoritative-source authentication; it is only an exact
   acquisition check for the next retrieval.
4. The managed command environment denied both the direct authoritative URL
   (`curl` DNS failure, exit 6) and a direct-IP/Host attempt against the public
   mirror (`curl` connection failure, exit 7).  Browser access exposed metadata
   but not the binary payload.  Do not describe the corpus as mirrored locally.

## Completed bounded experiments

### Provisional K43 dual-check control

Experiment: `.proof-experiments/20260720-193914-fbe251`

- Runtime 19.857 s, return code 0, 1,024 MB cap, deterministic seed 0.
- Checker A (Python adjacency matrix plus literal `C(43,5)` scan) and Checker B
  (C bitsets plus recursive clique enumeration in graph and complement) agreed
  on every exact forbidden set.
- `graph1`: two zero-color K5s and no one-color K5.
- `graph2`: no zero-color K5 and exactly
  `{0,15,22,28,39}`, `{0,15,24,28,39}` in the one color.
- Conflict intersection `{0,15,28,39}`; union
  `{0,15,22,24,28,39}`.
- Deleting each intersection vertex produced a valid order-42 graph under both
  checkers.
- Forced clique/independent-set mutations were detected; truncated,
  non-binary, and asymmetric matrices were rejected by both parsers.
- Limitation: `inputs/k43_two_conflict_gist.txt` is a third-party visible
  transcription.  Agreement validates evaluator semantics, not publisher
  provenance.

### Exhaustive graph6 plumbing control

Experiment: `.proof-experiments/20260720-194142-be8455`

- Runtime 1.194 s, return code 0, 1,024 MB cap, deterministic seed 0.
- `nauty-geng` generated one representative of every 1,044 unlabeled simple
  graph class on 7 vertices.
- Both custom checkers agreed on exact forbidden-set lists for all 1,044 source
  records and their complements.
- NetworkX independently agreed on order, edge count, and ordered degrees for
  every record.
- The local graph6 complement transform agreed byte-for-byte with
  `nauty-complg` and applying it twice returned the original bytes.
- Order 7 was chosen because `C(7,2)=21` leaves three graph6 padding bits, the
  same padding count as `C(42,2)=861`.
- Scope: this validates short-graph6 plumbing across all order-7 isomorphism
  classes; it does not validate any order-42 corpus record.

### Corpus source preflight

Experiment: `.proof-experiments/20260720-193953-b4e5bd`

- Runtime 0.138 s, return code 2 (intentional fail-closed result), 256 MB cap.
- Expected `sources/r55_42some.g6`; file absent.
- Report status `source_preflight_failed`; no downstream checker,
  complement, histogram, degree, or canonicalization step ran.

## Reusable packet

- `scripts/run_corpus_gate.py` freezes the hash/size/record discriminator.  On
  an exact match it will check the 328 records and 328 derived complements with
  both exact checkers, require the published base edge histogram
  `423..430 -> 1,7,29,66,89,77,43,16`, require degree range `19..22`, test
  complement involution, run `nauty-labelg`, and require 656 distinct canonical
  labels.  It labels its successful scope as the supplied 656 controls, never
  a complete census.
- `scripts/test_graph6_plumbing.py` is the independent nauty/NetworkX regression
  described above.
- `sources/provenance.json` records the authoritative URLs, mirror discriminator,
  open provenance gates, and both Terra memo generations.

Environment used: Python 3.12.3, GCC 13.3.0, nauty 2.8.8+ds-5, NetworkX 2.8.8,
Linux 6.8.0-124-generic-x86_64.

## Exact next action

Acquire `https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6` as unchanged
bytes at `sources/r55_42some.g6`, recording retrieval timestamp, final URL,
headers/content type, byte count, and SHA-256.  Do not normalize line endings.

If and only if the file is 47,888 bytes with SHA-256
`067902e853d87b49bcef0d1d4c0e3bbadd238ee18bc65341b079a3ca4780eccb`, run:

```bash
python3 /root/proof-factory/skills/computational-researcher/scripts/run_experiment.py \
  --name r55-authenticated-corpus-gate \
  --hypothesis "The acquired McKay bytes encode the reported 328 controls and 328 complements" \
  --expected-signal "Two exact checkers report zero forbidden sets on 656 instances; published histogram and degree range reproduce; complement and 656-class canonical gates pass" \
  --timeout 3600 --memory-mb 2048 \
  --source-url https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6 \
  -- python3 scripts/run_corpus_gate.py \
  checkers/checker_a.py checkers/checker_b.c \
  sources/r55_42some.g6 artifacts/authenticated_corpus_report.json
```

Stop immediately on any byte, record, parser, violation-identity, edge,
degree, complement, or canonical-label mismatch.  Preserve the supplied bytes
and divergent outputs unchanged.  If the authoritative bytes differ from the
mirror discriminator, do not edit the constant to make the gate pass: obtain a
second independent authoritative retrieval or maintainer confirmation first.

After the corpus passes, the next source gate is the unchanged Springer
Supplementary Data 4 file
`41467_2018_7327_MOESM6_ESM.txt`.  Only after both raw-source gates pass should
the four valid K43-deletion controls be canonicalized against the 656, followed
by S3 (unknown-42 basin) or the authenticated six-vertex S4 repair slice.

## Sources and disclosure

- Dynamic Survey: https://www.combinatorics.org/ojs/index.php/eljc/article/download/DS1/pdf/0
- Published upper bound: https://onlinelibrary.wiley.com/doi/full/10.1002/jgt.70029
- McKay data page: https://users.cecs.anu.edu.au/~bdm/data/ramsey.html
- McKay corpus URL: https://users.cecs.anu.edu.au/~bdm/data/r55_42some.g6
- Mirror metadata: https://huggingface.co/datasets/linxy/RamseyGraph/blob/main/data/r55_42some.g6
- Molnar et al. article: https://doi.org/10.1038/s41467-018-07327-2

GPT-5.6 Sol was the principal investigator.  Two pairs of GPT-5.6 Terra
delegate memos supplied pre-epoch literature/verification reconnaissance; Sol
read them as advisory leads and independently replayed all relied-on local
claims.  Deterministic tools used were Python, C/GCC, nauty, NetworkX, SHA-256,
the experiment harness, shell diagnostics, web search, and read-only GitHub
fetch/search.  No SAT solver, proof assistant, cloud research search, or new
delegate was used this epoch.
