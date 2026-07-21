## Verification memo — adjacency-row pair-distance filter

**Best live route:** `strategy-r55-row-code-sdp`, but only its first, uncoloured fixed-degree-profile LP. The q=20 SAT branch is correctly blocked: monolith and all 16 checked cubes timed out, so another similar run has no discriminator value.

**Rationale:** turn adjacency rows into a binary-code multiset. For degrees \(a,b\) and common-neighbour count \(c\),

\[
d_H(a_u,a_v)=a+b-2c.
\]

For an edge, \(c\le13\); for a nonedge, common nonneighbours \(\le13\). This gives exact allowed row-distance sets for each degree pair, while Delsarte/Krawtchouk PSD inequalities supply a cheap necessary condition. The current upper-bound paper confirms the broader LP-plus-independent-computation architecture, but this is only a new filter experiment, not an upper-bound proof. [Angeltveit–McKay](https://arxiv.org/abs/2409.15709)

**Critical preflight:** degree bounds alone are too broad. I counted 6,992,920 / 953,580 / 106,076 even-sum degree histograms for \(n=43/44/45\), respectively. Before solving any profile LP, Sol should create a cited, machine-readable `scalar-profile-manifest` containing only profiles surviving the intended published degree/excess restrictions. If that manifest is absent, or remains above a declared practical threshold, park this route rather than silently turning a “cheap” test into millions of LPs.

### Cheapest decisive experiment

For each fixed histogram \(p_a\) in that manifest, solve the following rational feasibility LP.

- Degrees are \(a\in[n-25,24]\); \(p_a\) is fixed.
- For each degree pair \(a,b\), use ordered-pair variables \(x_{ab\delta}\), where \(\delta\) is an allowed row distance.
- Enforce exact pair-type totals:
  - \(\sum_\delta x_{ab\delta}=p_ap_b\) for \(a\ne b\);
  - \(\sum_\delta x_{aa\delta}=p_a(p_a-1)\).
- Add the diagonal contribution \(p_a\) at distance zero separately. Do not assume rows are distinct.
- Edge-compatible distances arise from

\[
\max(0,a+b-n)\le c\le\min(a-1,b-1,13).
\]

- Nonedge-compatible distances arise from

\[
\max(0,a+b-n+2)\le c\le\min(a,b,a+b-n+15).
\]

For either permitted interval, include \(\delta=a+b-2c\). The LP may use the union of edge/nonedge possibilities; it must not claim to preserve edge color.

- For every \(k=0,\ldots,n\), impose

\[
\sum_{u,v}K_k^{(n)}(d_H(a_u,a_v))\ge0,
\]

implemented from the \(x\)-ledger plus diagonals, with integer Krawtchouk coefficients.

**Prediction:** at least one scalar-admissible histogram is LP-infeasible.  
**Decisive outcome:** an exact Farkas certificate excluding at least one manifest profile. If every manifest profile has an exact rational feasible point, archive a negative result and stop before SDP.

### Controls and independent verification

The input gate already supplies a strong control packet: `r55_42some.g6` SHA-256 `067902…0eccb`; the authenticated report passes 656 supplied/complemented controls, all K5 checks, complement involution, and 656 distinct canonical classes. This is not a classification.

Require two fresh ledger implementations:

1. Python direct graph6 parser/combinations path, independent of the LP producer.
2. C bitset/parser path, independent of Python.

Both must emit record-indexed degree histograms and ordered \((a,b,\delta)\) ledgers with identical hashes. Then a third, tiny rational checker verifies every LP equality, non-negativity condition, and Krawtchouk inequality using integer/Fraction arithmetic.

Useful mutation controls:

- All 656 controls must produce explicit feasible primal ledgers.
- Complement every control and verify the transformed ledger directly; do not assume row distance is complement-invariant.
- The controls attain the sharp bound: reconnaissance counted 6,072 edge pairs with \(c=13\) and 6,072 nonedge pairs with common-nonneighbour count 13. A deliberate `≤12` mutation must fail.
- Exhaust all labelled graphs through order 6 to test the row-distance identity and Krawtchouk implementation independently of the Ramsey corpus.
- Tamper with one graph6 bit, one degree label, one allowed-distance interval, and one certificate coefficient; each must fail closed.

My in-memory reconnaissance found 194 distinct degree histograms among the 656 controls and row distances 12–28. Treat this only as a planning observation until reproduced by the two ledger programs.

### Failure modes to attack

- **False strength:** treating the union-of-colors support as a colored adjacency relaxation. It is not; any cut is weaker than a true colored model.
- **Unsound code assumption:** imposing \(A_0=1\) or distinct adjacency rows. Use a multiset formulation with explicit diagonal mass.
- **Numerical overclaim:** SciPy is installed, but no exact LP tool was found locally. Its output may generate candidate certificates only. Accept infeasibility solely from a rational Farkas witness checked independently.
- **Baseline laundering:** “cuts a profile” is meaningless unless the exact scalar-profile manifest and its source provenance are frozen first.
- **Scope creep:** do not build Terwilliger/PSD blocks, a colored coherent configuration, or retry q=20 unless this stage yields an exact new profile cut.

**Reusable artifact:** `rowpair-v1` should contain the source hashes, scalar-profile manifest, two per-graph ledgers, canonical LP JSON, exact primal/Farkas certificates, and a checker that outputs only PASS/FAIL with hashes.

**Sol should reject:** a floating-point infeasibility claim; any result that fails one known control; an enumeration launched from raw degree bounds alone; using the 656 controls as exhaustive; or an SDP escalation after an all-feasible/null pair-LP result.
