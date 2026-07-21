# Terra experiment-verification memo, promoted with Sol scope guard

Source: `.delegates/20260721-193743-1d1e25/experiment-verification/memo.md`

Source SHA-256:
`67519406d18ce6578b75651e0b8534d3a15180e80a1b0d5c9795545d11236085`

The delegate recommended continuing the checkpointed 656-host supplied-class
embedding census, explicitly as a bounded control corpus rather than a
completeness claim or Ramsey bound.  It identified a reconstructibility gap:
per-host archives retain the full custom-DFS stream but only a NetworkX
summary.  Its proposed guard was a cold audit of every embedding-bearing host,
a stratified sample of empty hosts, every saved pullback, two exact graph
checkers, and corruption mutations before any block or residual SAT step.

Sol independently confirmed the archive asymmetry in the production script
and implemented the cold prefix auditor.  The delegate's numerical and
correctness statements were not treated as evidence.
