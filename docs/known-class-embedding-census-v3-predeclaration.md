# Known-class embedding census v3 continuation predeclaration

**Status:** Not submitted. The stopped v2 experiment remains immutable. This continuation is authorized
only if the separately recorded host-254 calibration passes every threshold in
`known-class-embedding-host254-calibration-efficiency.json`.

## Decisive observable

Complete all 656 supplied source/complement hosts with exact agreement between the bitset enumerator and
the materially different NetworkX VF2 enumerator. Produce a sequential, hash-verified manifest and
compressed per-host artifacts that pass the independent final validator. This classifies only the supplied
known-class embedding boundary; it does not change a Ramsey bound.

## Preserved prefix and gate schedule

- Hosts 0–253 come from stopped job `lab-ramsey-r55-census-v2-full` and must retain manifest-prefix SHA-256
  `50946975a8be443f08218377924028e6b4762b0a84fd47f10ecb0125e4cfff95` and a declared 30-second host gate.
- Host 254 must come from the isolated cap-60 calibration and pass in at most 45 measured seconds.
- Hosts 254–655 declare a 60-second aggregate gate. A later gate hit stops the new job with reason; it does
  not authorize another automatic increase.
- The v3 job starts from a new copy of the validated 255-host calibration prefix. Neither v2 nor calibration
  paths are mutable inputs to v3.

## Resource and continuation contract

The measured v2 prefix used about 105 MB peak service memory, no service swap, and tiny artifacts. Its
successful host median was about 20 seconds and the remaining 402 hosts projected near 2.1 core-hours;
the 60-second worst-case ceiling is about 6.7 hours. V3 remains one host per segment, 120 seconds and
1,000 MB per segment, with durable progress/checkpoint records and a 64 MiB total artifact-growth ceiling.

The first v3 segment is a bounded lifecycle pilot over host 255. Continue through the remaining tranche
only if it advances exactly one host, exact agreement remains true, throughput is at least 0.015 hosts per
second, artifact growth remains within the declared limit, and the immutable input/prefix receipts verify.
After that review, the next scheduled review is the final declared segment; per-segment safety checks still
stop immediately on any threshold failure.

## Independent validation

Completion is `completed_awaiting_review`, not validated. A separate validation lab job must run the final
checker over the frozen manifest/artifacts and explicit mixed gate schedule. Validation must bind the
producer job, checker revision and hash, exact checked input hash, command, exit status, stdout/result hash,
and final artifact hashes. Residual SAT is forbidden until that independent validation job is itself
completed and the operator applies its receipt.
