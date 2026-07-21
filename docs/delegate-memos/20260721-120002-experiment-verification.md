# Terra experiment-verification memo — epoch 13

The delegate recommended only the first, uncoloured fixed-degree-profile LP of
`strategy-r55-row-code-sdp`. It warned that the q=20 monolith and all 16 short
cubes were already blocked and that raw degree bands contain 6,992,920,
953,580, and 106,076 handshake-parity histograms at orders 43, 44, and 45.
Before any LP sweep, it required a cited scalar-profile manifest; absent a
manageable, precisely defined baseline, the route should be parked.

For degrees `a,b` and common-neighbour count `c`, the proposed uncoloured
support used `delta=a+b-2c`. Edge-compatible intersections satisfy

```text
max(0,a+b-n) <= c <= min(a-1,b-1,13),
```

and nonedge-compatible intersections satisfy

```text
max(0,a+b-n+2) <= c <= min(a,b,a+b-n+15).
```

For a fixed histogram `p_a`, the delegate proposed nonnegative pair variables
whose totals are `p_a p_b` for unequal weights and `p_a(p_a-1)` for equal
weights, with the `p_a` diagonal rows added separately at distance zero. It
explicitly warned that taking the union of edge and nonedge support does not
preserve edge colour and must not be described as a coloured adjacency model.
All binary Krawtchouk inequalities should be imposed with integer
coefficients.

Required controls were:

1. A direct Python graph6/combinations implementation.
2. An independent C bitset/parser implementation.
3. A small exact checker for marginals, nonnegativity, and Krawtchouk sums.
4. Complement controls without assuming row-distance invariance.
5. All labelled graphs through order 6.
6. Mutations of corpus bits, degree labels, support bounds, and certificate
   coefficients.

The delegate's reconnaissance predicted 194 distinct degree histograms,
off-diagonal distances 12--28, and sharp common-neighbour bounds among the 656
controls. These were planning observations only until reproduced. It rejected
floating-point infeasibility, shared-code checking, treating the controls as a
census, and any SDP escalation after an all-feasible pair LP.

Sources supplied by the delegate:

- https://arxiv.org/abs/2409.15709
- https://www.cs.rit.edu/~spr/ElJC/sur.pdf

This promoted memo is advisory, not evidence. Its exact source hash and role
are recorded in `records/delegate-provenance-epoch13.json`.
