# Terra literature-strategy memo — epoch 13

**Best live route:** the exact adjacency-row pair-distance LP discriminator
(`strategy-r55-row-code-sdp`), not another q=20 SAT run. The cube pilot is
complete and inconclusive: all 16 production leaves were `UNKNOWN`, so
rerunning it without a changed solver/encoding violates its recorded stop
condition.

**Sourced status:** the maintained survey, revision 18 (24 April 2026), still
records `43 <= R(5,5) <= 46`, with strong evidence—but not a
classification—for 656 order-42 critical graphs. The current Angeltveit–McKay
primary preprint remains v2 and proves only `R(5,5) <= 46` via LP plus
extensive independent computation.

## Exact rationale

Source concept → prediction → test:

- Coding LPs constrain a binary code’s distance distribution; Schrijver’s SDP
  is a stronger later refinement.
- Treating adjacency rows as codewords should add necessary constraints beyond
  scalar degree counts.
- Before an SDP, test whether the cheaper rational pair relaxation excludes
  even one currently admissible profile at `n=43,44,45`.

This is deliberately a filter, not a novelty or bound claim. Historic R55 LP
machinery already uses degree and neighborhood data, so the discriminator must
compare against a precisely transcribed published baseline; otherwise “newly
cut” is undefined.

## Cheapest discriminator

For each `n` in `{43,44,45}`, enumerate only degree histograms surviving the
independently reconstructed baseline constraints, with degrees in `18..24`,
`19..24`, and `20..24`, respectively. For each profile, use exact rational
variables for ordered row-pair types `(epsilon,d_u,d_v,c_uv)`, where epsilon
records edge/nonedge and `h_uv=d_u+d_v-2c_uv`. Impose degree-pair marginals,
`c_uv<=13` on edges, and on nonedges
`n-2-d_u-d_v+c_uv<=13`. Aggregate to the row-distance distribution and impose
the ordinary exact Delsarte/Krawtchouk inequalities.

Success means an exact infeasibility/cut for a baseline-admissible profile,
with a rational dual independently checked. Otherwise park the route; do not
build the coloured Terwilliger SDP.

## Controls

- Extract per-graph row weights, pair intersections, edge/nonedge types, and
  distances from all authenticated 656 controls, using two independent
  implementations.
- Every control must satisfy every generated LP constraint exactly.
- Keep original graphs and complements separate: complementing a simple-graph
  adjacency matrix is not ordinary rowwise bit complementation, and the two
  row-index coordinates create an off-by-two trap.
- Independently verify the common-nonneighbour convention excludes `u,v`.
- Preserve a hash-locked manifest of corpus input, profile list, LP
  coefficients, solver input, and rational checker output.

Likely failure is that pair constraints add no information after degree/excess
restrictions; this is useful and is the intended stop. Invalid outcomes include
a floating-point-only cut, use of the 656 as an exhaustive census, failure of a
known control, or a baseline LP not reconstructed from cited work.

Sources supplied by the delegate:

- https://www.cs.rit.edu/~spr/ElJC/sur.pdf
- https://arxiv.org/abs/2409.15709
- https://ir.cwi.nl/pub/14098
- https://www.cs.rit.edu/~spr/PUBL/paper29.pdf

This promoted memo is advisory, not evidence. Its exact source hash and role
are recorded in `records/delegate-provenance-epoch13.json`.
