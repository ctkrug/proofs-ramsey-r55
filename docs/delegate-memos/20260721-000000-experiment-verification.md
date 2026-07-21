# Verification memo — publisher K43 radius-1 discriminator

**Scope:** a bounded experiment design and a small direct calculation on the
authenticated publisher bytes.  This is neither a Ramsey bound nor a claim
about the global minimum number of monochromatic `K5`s.

## Best live route

Run a fail-closed publisher-seed gate followed by the **complete one-edge
non-star neighbourhood** of the publisher's Supplementary Data 4 matrix.  The
two direct raw bodies already present at
`sources/retrievals/springer_supplementary_data4_audit{1,2}.txt` agree at
3,812 bytes and SHA-256
`c2429869f6fa47ab7388134b580b014efae01e6f0e474f5bab2233afb1ef6990`.
Their HTTP/2 header captures identify `application/octet-stream` at the
Springer-controlled raw URL; the experiment records are
`.proof-experiments/20260720-235158-0cfef1` and
`.proof-experiments/20260720-235208-a7e84e`.

This is the cheapest decisive S4 discriminator: it exhausts all 903 single
edge flips (and the meaningful non-star subfamilies) exactly.  It can refute
the specific premise that the two-conflict state is one edit from a witness,
or establish the exact radius-1 burden floor for this frozen seed.  It does
not address any larger Hamming ball or the global Ramsey problem.

## Frozen statement and expected control values

Parse the raw ASCII object directly: ignore its one `#` title line, require
exactly 43 space-delimited rows of 43 bits, a zero diagonal, and symmetry.
The admitted object has 454 one-edges.  Under `0`/`1` as printed, its only
monochromatic sets are the two all-zero sets

```
[6,12,17,36,42]
[6,12,31,36,42]
```

and no all-one `K5`.  Their intersection is `I={6,12,36,42}`.  The four
deletions at members of `I` must again be verified as valid order-42 graphs
and checked for membership in the *supplied* 656 labels only, never described
as a census.

For every edge `e`, flip only `e` and count all-zero plus all-one 5-sets.  A
direct enumeration used solely to set acceptance targets found the following:

| frozen edit family | number of flips | expected minimum total | minimizers |
| --- | ---: | ---: | --- |
| all edges | 903 | 2 | `(6,12)`, `(36,42)` |
| non-star relative to deleted vertex 6 (`e` not incident to 6) | 861 | 2 | `(36,42)` |
| edits avoiding every member of `I` | 741 | 3 | `(0,37)`, `(5,11)`, `(10,16)`, `(16,22)`, `(21,27)`, `(26,32)`, `(32,38)` |

These values are **not yet an accepted experiment result**: the gate below
must recompute them and retain its report.  The last slice is the strongest
one-edge non-star control: its edits change the remainder after deletion of
each of the four shared vertices, so it cannot secretly be a one-vertex
extension of any of those known 42-vertex deletions.

## Exact implementation and independent verification

1. Hash both raw bodies before parsing; reject unequal bytes, a changed hash,
   header/TLS/effective-URL failure, row-format variation, or a changed title
   object.  Retain both header captures and the curl transfer JSON, without
   requiring date/cache header equality.
2. Write two deliberately separate raw parsers: a simple 43-by-43 Boolean
   matrix parser used with direct `itertools.combinations`, and a C parser
   feeding recursive bitset clique enumeration.  They must read publisher
   whitespace independently; do not make a shared normalized matrix their
   only input.
3. Have each evaluator compute the seed's full violation identities.  For the
   complete radius-1 family, enumerate every changed matrix with the C
   evaluator.  Independently calculate its count vector by scanning every
   5-set once: a flip can change monochromatic status only when the 5-set is
   monochromatic, has exactly one one, or has exactly one zero.  Directly scan
   every minimizer and one representative from each larger burden class with
   the combinations evaluator.  Compare complete identities for all
   minimizers, not counts alone.
4. Positive controls: force a fixed all-one and a fixed all-zero 5-set in the
   raw representation; both parsers/evaluators must report it.  Negative
   controls: asymmetric entry, nonbinary token, shortened row, nonzero
   diagonal, altered raw body, and substituted provisional-Gist matrix must
   all fail before search.
5. Record raw/header/transfer/checker/compiler/binary/report SHA-256 values,
   the 903-edge ordered list, every score histogram, identities for all
   minima, and the precise family predicate.  A clean-room replay receives
   exactly these inputs plus the gate source.

## Stop conditions and failure modes

Stop at the first provenance, parser, checker, conflict-identity, mutation,
or score mismatch.  Stop successfully after the frozen radius-1 families are
exhausted; report only those families.  A zero requires both independent
checkers; a nonzero floor needs no SAT proof because the finite 903-flip list
is explicitly enumerated and retained.  Do not silently repair a body or
change expected values.

The principal hazards are: treating `static-content.springer.com` as a
non-publisher mirror; shared normalization hiding a raw-parser defect;
confusing 0/1 color convention; double-counting a 5-set in a recursive
enumerator; accepting a local optimum as global; and calling a star-only
change an escape from the known deletion basin.  The supplied-656 comparison
is a novelty control, not completeness evidence.

## Reusable artifact and Sol review

The deliverable should be a `publisher_seed_radius1_report.json` plus the two
raw acquisitions, parser sources, compiled-binary hash, complete flip ledger,
and cold-start replay command.  It is a benchmark and a verified local
landscape datum, useful before any radius-2 MaxSAT encoding.

Sol should independently recompute the two raw hashes, hand-check the two
seed conflicts from raw rows, inspect that the last 741-flip predicate avoids
all vertices in `I`, and run the second evaluator on every reported minimizer.
Sol should reject any result based only on the third-party transcription, an
unlogged solver `UNSAT`, a normalized shared parser, an unretained flip list,
or language implying a bounded radius-1 result determines `R(5,5)`.
