## Literature-strategy memo

**Best live route:** the exact adjacency-row pair-distance LP discriminator (`strategy-r55-row-code-sdp`), not another q=20 SAT run. The cube pilot is complete and inconclusive: all 16 production leaves were `UNKNOWN`, so rerunning it without a changed solver/encoding violates its recorded stop condition.

**Sourced status:** the maintained survey, revision 18 (24 April 2026), still records \(43\le R(5,5)\le46\), with strong evidence—but not a classification—for 656 order-42 critical graphs. The current Angeltveit–McKay primary preprint remains v2 and proves only \(R(5,5)\le46\) via LP plus extensive independent computation. [Dynamic Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf), [Angeltveit–McKay](https://arxiv.org/abs/2409.15709)

### Exact rationale

Source concept → prediction → test:

- Coding LPs constrain a binary code’s distance distribution; Schrijver’s SDP is a stronger later refinement. [Schrijver](https://ir.cwi.nl/pub/14098)
- Treating adjacency rows as codewords should add necessary constraints beyond scalar degree counts.
- Before an SDP, test whether the cheaper rational pair relaxation excludes even one currently admissible profile at \(n=43,44,45\).

This is deliberately a **filter**, not a novelty or bound claim. Historic R55 LP machinery already uses degree and neighborhood data, so the discriminator must compare against a precisely transcribed published baseline; otherwise “newly cut” is undefined. [McKay–Radziszowski](https://www.cs.rit.edu/~spr/PUBL/paper29.pdf)

### Cheapest discriminator

For each \(n\in\{43,44,45\}\), enumerate only degree histograms surviving the independently reconstructed baseline constraints, with degrees in:

- \(18,\ldots,24\) for \(n=43\);
- \(19,\ldots,24\) for \(n=44\);
- \(20,\ldots,24\) for \(n=45\).

For each profile, use exact rational variables for ordered row-pair types
\((\epsilon,d_u,d_v,c_{uv})\), where \(\epsilon\) records edge/nonedge and

\[
h_{uv}=d_u+d_v-2c_{uv}.
\]

Impose degree-pair marginals, \(c_{uv}\le13\) on edges, and, on nonedges,
\[
n-2-d_u-d_v+c_{uv}\le13.
\]
Aggregate these to the row-distance distribution \(A_h\), then impose the ordinary exact Delsarte/Krawtchouk inequalities \(\sum_h A_hK_j(h)\ge0\). This is a necessary relaxation only.

Success means: an exact infeasibility/cut for a baseline-admissible profile, with a rational dual independently checked. Otherwise park the route; do not build the colored Terwilliger SDP.

### Controls

- Extract per-graph row weights, pair intersections, edge/nonedge types, and distances from all authenticated 656 controls, using two independent implementations.
- Every control must satisfy every generated LP constraint exactly.
- Keep original graphs and complements separate: with zero diagonals, complementing a simple-graph adjacency matrix is not ordinary rowwise bit-complementation; distance handling has an off-by-two trap at the two row indices.
- Independently verify the common-nonneighbor convention excludes \(u,v\).
- Preserve a hash-locked manifest of corpus input, profile list, LP coefficients, solver input, and rational checker output.

### Failure modes

The likely negative outcome is that pair constraints add no information after degree/excess restrictions; that is useful and is the intended stop. Other invalidating failures are: a floating-point-only cut, accidental use of the 656 as an exhaustive census, failure of a known control, or a baseline LP not reconstructed from the cited work.

The pair LP also discards adjacency symmetry, diagonal structure, and most edge/nonedge coupling. A numerical SDP must not be started merely because the LP is feasible; it needs an actual profile cut first.

### Reusable artifact

Produce a small `row-code` packet: dual-parser control distributions; explicit profile enumerator; rational LP generator; exact Krawtchouk/dual checker; and a profile-by-profile verdict table. It can support later colored moment work or inequality discovery without asserting any Ramsey result.

### What Sol should reject or verify independently

Reject:

- any q=20 or cube retry using the same CaDiCaL configuration;
- claims that a generic code LP respects graph symmetry;
- any “new exclusion” not compared with a frozen published-baseline profile list;
- numerical duals without exact rational checking;
- inferences from the 656 controls to global nonexistence.

Independently verify the row convention, both \(13\)-bounds, all control feasibility, profile-baseline construction, and each purported rational certificate.
