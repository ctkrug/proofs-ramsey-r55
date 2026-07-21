# Literature-strategy memo — R(5,5), epoch 8 intake

**Scope.** Compact reconnaissance only.  This memo makes no witness, bound,
classification, multiplicity-optimum, or originality claim.

## Status audit

The maintained source is unchanged: Radziszowski's *Small Ramsey Numbers*,
DS1.18 (revision 18, 24 April 2026), records strong evidence for 656
order-42 critical graphs, lower bound 43, and the Angeltveit--McKay upper bound
46.  Thus the published range remains `43 <= R(5,5) <= 46`.

- Survey: https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- Current upper-bound manuscript (v2, 1 September 2025):
  https://arxiv.org/abs/2409.15709
- Historical 656/control and non-extension evidence:
  https://users.cecs.anu.edu.au/~bdm/papers/r55.pdf

The local-state replay is consistent with the retained reports: the
authenticated Springer seed's complete radius-2 gate and its complete
distance-6 one-orbit gate both reran successfully from the frozen sources.
This reaffirms only their recorded scopes: all two-edge flips have burden at
least two, and the 43-bit distance-6 slice has minimum two with 86 optima.  It
does not validate a larger search family.

## Best live route

Run **strategy-r55-two-orbit-domain-wall**: release distance 6 and exactly one
of the other 20 cyclic-distance edge orbits of the authenticated 43-vertex
seed, leaving the other 19 frozen.  This is the strongest live route because
it is the immediate structured enlargement after three *completed* exclusions:
all radius-1 edits, all radius-2 edits, and the full `2^43` one-orbit family.
It also avoids historical duplication: pure circulant search is closed at this
order, star-only extension of the four known deletion remainders is saturated,
and generic local search has no demonstrated advantage.

The test is an inference, not a literature fact: if the observed interval
defect can escape without becoming unstructured, its first available degree of
freedom must couple to another orbit.  A null result merely closes twenty
specified near-circulant slices.

## Cheapest discriminator and controls

For each second distance `r != 6`, deterministically derive the burden-zero
CNF by enumerating all `C(43,5)=962,598` five-sets from the raw publisher
matrix.  The 86 variables are the edges in the two released orbits.  Require
a separately implemented derivation to agree on the complete clause multiset,
including multiplicities, before solving.

Use the common `C_43` vertex-rotation action only through a complete lex-leader
condition on the *concatenated* 86-bit assignment (or omit symmetry breaking
entirely).  Pinning a single bit such as `x_0` is unsound: valid assignments
may have a constant or otherwise excluded first orbit.  Record the exact
variable order and prove/check that every rotation preserves the frozen
background and maps clauses to clauses.

Controls:

- replay the frozen publisher provenance, radius-2, and one-orbit gates first;
- decode every SAT model to the full 43-by-43 matrix and run both complete K5
  checkers, with mutation tests and source hash retained;
- for every UNSAT result, retain deterministic CNF, solver/version/options,
  proof log, and an independent proof check; and
- verify the symmetry breaker against an unbroken small slice or by explicit
  orbit enumeration on sampled models.

## Failure modes, artifact, and stop rule

Main risks are a wrong undirected-orbit index, silently dropping K5 clauses
whose fixed edges already decide a color, treating solver UNSAT as certified,
or conflating a two-orbit conclusion with the 903-edge space.  The useful
artifact is a per-distance `CNF + clause-multiset digest + symmetry witness +
decoded-model/proof-log` bundle.  It is reusable for a later multi-orbit CSP
or for the trapping-atlas route, but it is not a Ramsey certificate by itself.

Stop immediately on provenance, clause-derivation, checker, or symmetry-orbit
mismatch.  Stop the family after twenty completed slices.  If none beats
burden two, close this two-orbit domain-wall ansatz and do not retune it;
transfer only its measured constraint cores to a *held-out* trapping-atlas
ablation.  If a slice beats two, independently verify it, then rank it by
burden and factor-graph width before any larger family is authorized.

## What Sol should independently reject or verify

Reject any claim that the 656 controls are complete, that a bounded UNSAT run
changes `R(5,5)`, or that ordinary cyclic symmetry permits an arbitrary fixed
edge.  Verify the official range above, the raw-source hashes and gate replay,
both independent clause derivations, symmetry coverage, and full-graph
checker agreement for every claimed model.
