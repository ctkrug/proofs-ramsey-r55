# R(5,5) adversarial audit and field-progress gate

Recorded: 2026-07-21 UTC

## Verdict

**No field-progress condition is met.** The retained radius-one, radius-two, and distance-six claims
survive independent attack, and the complete 20-family two-orbit sweep is a certified negative:
every family has exact minimum burden 2, and equality always leaves the second orbit frozen. The work
is therefore a **verified negative experiment plus certificate-carrying infrastructure result**, not
a Ramsey bound, multiplicity theorem, novel witness, accepted search-space reduction, or demonstrated
algorithmic advance.

The maintained status remains `43 <= R(5,5) <= 46`. The current Dynamic Survey revision was checked
again on 2026-07-21, as was Angeltveit–McKay's `R(5,5)<=46` paper. No external acceptance event exists
for the work below.

## Claim-by-claim audit

| Claim | Verdict | Independent evidence |
|---|---|---|
| Springer body is 3,812 bytes with SHA-256 `c242...6990` | **Verified** | Two hash-linked successful HTTPS retrieval records, headers, transfer metadata, and byte-identical bodies in `artifacts/adversarial_audit_report.json` |
| Seed has exactly zero-K5s `[6,12,17,36,42]`, `[6,12,31,36,42]` | **Verified** | New exhaustive Python induced-edge scan and C++ bitset count |
| Seed has no one-K5 | **Verified** | Same two full evaluators |
| All 903 one-edge flips have burden at least 2 | **Verified** | Independent C++ triangle/common-neighborhood bitset enumeration reproduced the complete retained histogram; minimum 2 at `(6,12)` and `(36,42)` |
| All 407,253 two-edge flips have burden at least 2 | **Verified** | Independent C++ enumeration reproduced the full 814,506-byte score ledger byte-for-byte |
| The 403,809-pair deletion-remainder-change family has minimum 2 | **Verified** | Independently re-evaluated predicate, cardinality, histogram, and minima |
| Exactly two radius-two minima: `{(6,12),(9,15)}` and `{(33,39),(36,42)}` | **Verified** | Complete ledger plus 20 boundary/random direct Python rescans |
| Minima are rotations `-27` and `+27` | **Verified** | Explicit comparison of all 1,849 matrix entries under each vertex permutation |
| Twenty cyclic-distance orbits are constant; only distance 6 varies | **Verified** | Independently derived 21-orbit profile |
| Reduced translated shapes are positive pairs `{0,18}`, `{0,20}` with multiplicity 2 and negative triple `{0,5,24}` with multiplicity 1 | **Verified** | Fresh derivation from every `C(43,5)=962,598` five-set |
| 215 active five-sets and 129 unique constraints | **Verified** | Exact five-set disposition ledger: 215 active, 962,383 fixed-bichromatic inactive |
| Distance-six burden 0 and 1 are impossible | **Verified** | Deterministic CNFs and independently checked DRAT proofs |
| Exactly 86 burden-two words, the 43 rotations each of step-27 intervals of lengths 24 and 25 | **Verified** | Independent CaDiCaL enumeration, two full graph checkers on every model, and a 25 MB direct-cardinality CNF plus checked DRAT proof excluding any 87th word |

Malformed nonbinary, shortened, nonzero-diagonal, asymmetric, and extra-line inputs were rejected by
both new parsers. Forced-clique and forced-coclique mutations were detected. Pair-index boundaries and
12 deterministic random pairs were rescanned directly.

## New two-orbit experiment

For each `d in {1,...,21} \ {6}`, define `F_{6,d}` by varying exactly the 43 distance-6 edges and
43 distance-`d` edges of the authenticated Springer matrix while freezing the remaining 19 cyclic
distance orbits.

| Measured outcome | Result |
|---|---:|
| Precisely defined families | 20 |
| Variables per family | 86 |
| Raw active five-sets | 731–3,913 |
| Unique raw clauses | 258–1,763 |
| Primal min-fill width upper bound | 37–58 |
| Families containing a zero-conflict witness | 0 |
| Families with minimum below 2 | 0 |
| Families with exact minimum 2 | 20 |
| Families creating a new burden-2 class | 0 |
| Checked DRAT proofs | 60 |
| Independent unsymmetrized Z3 decisions | 60 |

The exact finite statement is:

> For every `d != 6`, every coloring in `F_{6,d}` has at least two monochromatic K5s. Equality
> forces the entire distance-`d` orbit to its Springer frozen color, and the distance-6 word is a
> step-27 cyclic interval of length 24 or 25.

This gives 86 labeled minima in each family: two common-rotation orbits and two graph-isomorphism
classes, distinguished already by edge counts 454 and 455. None is new relative to the one-orbit
classification.

The common `Z_43` rotation action was broken by an exact lex leader over the concatenated 86-bit word.
All generated clauses and all 42 nonidentity shifts were independently audited. Every finite rotation
orbit contains a lexicographically least representative, including periodic ties. Separately, an
unsymmetrized Z3 pseudo-Boolean formulation reproduced all 60 decisions, so the result does not rest
on symmetry coverage alone.

## Field-progress gate

| Condition | Met? | Reason |
|---|---:|---|
| 1. Dual-checked zero-conflict K43 witness | **No** | No family contains burden 0. |
| 2. Lower conflict count in a broader interesting family | **No** | Every family remains at 2 and creates no new minimum class. |
| 3. Concise structural theorem explaining failure | **No** | The finite statement is certificate-backed, but there is not yet a concise human-checkable explanation covering all 20 families. |
| 4. Certified material reduction of an accepted R(5,5) search space | **No** | The certificates are sound and retained, but these narrow near-circulant slices are not an accepted material fraction of the global search space; no external audience has accepted the reduction. |
| 5. Held-out matched-compute algorithm improvement | **No** | No algorithm benchmark was run. |

### Contribution assessment

- **Exact class:** verified negative experiment plus certificate-carrying research infrastructure.
- **Closest baseline:** Molnár et al.'s published two-conflict K43 seed; the retained exact one-orbit
  minimum-two classification; and the prior exact closure of pure circulants at `C(5,5)=41`.
- **Measurable improvement:** verification rose from two local enumerators to deterministic CNFs and
  63 checked DRAT proofs overall; every two-orbit decision also has an independent unsymmetrized Z3
  check. The structured family expanded from one 43-variable slice to twenty 86-variable slices.
  Neither the best conflict count nor a Ramsey bound improved.
- **Independent validation:** exhaustive Python five-set scans; C++20 bitset triangle/common-neighbor
  counts; byte-exact pair-ledger replay; CaDiCaL 3.0.1; drat-trim; Z3 4.15.4.
- **Accepted external audience/channel:** none. No specialist, repository, venue, or review process has
  accepted this as useful field progress.
- **Unproved:** existence/nonexistence of a K43 witness; global order-43 multiplicity; all families
  releasing at least three orbits; a human structural proof; historical novelty or expert interest in
  the finite classification.

## Route decision and next discriminator

**Close the one- and two-orbit witness route. Do not launch all 190 three-orbit families by default.**
Redirect once to proof compression, because that is the only nearby outcome that can satisfy gate
condition 3.

- **Hypothesis:** the 20 unsymmetrized burden-zero exclusions have rotation-normalized,
  deletion-minimal raw-clause cores of at most 20 clauses that collapse to at most five parameterized
  obstruction types.
- **Discriminator:** extract exact minimal raw K5-clause cores, canonicalize their signed incidence
  hypergraphs, and require a deterministic map from all 20 distances to at most five symbolic
  templates whose originating five-sets can be checked without SAT auxiliaries or symmetry clauses.
- **Success certificate:** a short theorem and human-checkable proof plus a script instantiating every
  template for all 20 distances.
- **Stop condition:** if any minimized core still exceeds 20 raw clauses or more than five
  nonisomorphic types remain, abandon theorem compression and redirect to the leakage-safe held-out
  algorithm benchmark required by gate condition 5.

## Reproducibility anchors

- Final adversarial audit: `.proof-experiments/20260721-022123-71d7c4`
- Independent one-orbit CNF/DRAT classification: `.proof-experiments/20260721-020646-b4834f`
- Certified 20-family sweep: `.proof-experiments/20260721-020930-8c427b`
- Machine-readable adjudication: `artifacts/field_progress_gate_report.json`
- Full two-orbit report: `artifacts/two_orbit_certified_sweep_report.json`
- CNFs, proof logs, solver logs, checker logs, and metadata:
  `artifacts/one_orbit_sat_certificates/` and `artifacts/two_orbit_certificates/`

Primary status/baseline sources:

- Dynamic Survey revision 18: https://www.cs.rit.edu/~spr/ElJC/eline.html
- Angeltveit–McKay, `R(5,5)<=46`: https://arxiv.org/abs/2409.15709
- Molnár et al., published two-conflict K43 seed: https://www.nature.com/articles/s41467-018-07327-2
- Furini–Ljubić–San Segundo, `C(5,5)=41`:
  https://optimization-online.org/wp-content/uploads/2021/09/8578.pdf
