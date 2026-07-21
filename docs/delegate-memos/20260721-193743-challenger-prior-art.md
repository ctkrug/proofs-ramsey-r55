# Terra challenger/prior-art memo, promoted with Sol scope guard

Source: `.delegates/20260721-193743-1d1e25/challenger-prior-art/memo.md`

Source SHA-256:
`1a807594365db6d55a79705df9ea0f5f36e95c126a3a441f07e7205d4e1d1976`

The delegate retained raw-origin proof-core compression as the best challenger
and proposed a one-slice, at-most-20-origin discriminator.  It also stressed
that a partial census over the supplied 656 controls proves no complete block.

Sol did not execute or reopen the challenger this epoch because the incumbent
lab job had reached its mandatory review boundary with all continuation
thresholds satisfied.  The challenger remains the declared fallback if the
census fails a correctness, throughput, artifact-growth, or decision-value
gate.
