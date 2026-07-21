# R(5,5) epoch 13 attempt: rowpair-v1

- Strategy: `strategy-r55-row-code-sdp` / `r55rowcodesdp2026`
- Outcome: progress by exact falsification of the first-stage relaxation
- Accepted gate: `.proof-experiments/20260721-122138-bd5745`
- Cold audit: `.proof-experiments/20260721-122217-a1e4eb`
- Failed preflight retained: `.proof-experiments/20260721-121817-c060be`

The tested uncoloured union-support Delsarte pair LP cuts none of the
8,052,576 handshake-parity degree histograms in the Ramsey degree bands at
orders 43--45.  An explicit central-distance feasible point covers every
profile.  The full mathematical scope, controls, hashes, repair history, and
replay commands are in `docs/rowpair-v1.md`, `CHECKPOINT.md`, and `README.md`.

No graph was constructed or excluded, and the published bound remains
`43 <= R(5,5) <= 46`.  The strategy is parked before SDP according to its
predeclared stop condition.
