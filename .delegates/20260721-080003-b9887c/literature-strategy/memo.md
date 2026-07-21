Audit complete. The best live route is the symmetry-normalized q=20 almost-regular order-42 SAT pilot.

- Rationale: every degree-{20,21} graph is complement/relabel equivalent to one with `N(0)={1,…,20}`. Adding those 41 unit clauses is a sound change from the timed-out unsymmetrized pilot.
- Cheapest discriminator: audit the 41 units and coverage independently, then give exactly this normalized branch one 300-second/1-GiB proof-logging run.
- Controls: independent root-unit ledger, C five-set ledger, degree tests, mutation tests, dual full-graph scans for SAT, DRAT and LRAT checks for UNSAT.
- Stop: any audit mismatch, checked SAT/UNSAT, or timeout. Do not run other degree bands or K43 search afterward without new evidence.
- Reject: claims that 656 is complete, that a timeout excludes anything, or that this bounded slice determines `R(5,5)`.

The maintained status is unchanged: Dynamic Survey DS1.18 (24 Apr 2026) gives `43 ≤ R(5,5) ≤ 46`; it calls the 656 order-42 graphs strong evidence, not a classification. [Survey](https://www.cs.rit.edu/~spr/ElJC/sur.pdf) [McKay data page](https://users.cecs.anu.edu.au/~bdm/data/ramsey.html) [Angeltveit–McKay](https://arxiv.org/abs/2409.15709)

Memo saved: [20260721-080003-literature-strategy.md](/root/proof-factory/research/ramsey-r55/workspace/docs/delegate-memos/20260721-080003-literature-strategy.md) (858 words; SHA-256 `34dc3a…ad9c6`).
