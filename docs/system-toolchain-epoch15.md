# Epoch-15 toolchain change

Recorded: 2026-07-21 UTC

The labelled-model CEGAR discriminator needed an incremental SAT API so the
508,157-clause base could be parsed once and learned clauses could be reused
after appending each primary-vector block.  The preinstalled `cadical` package
contained only the command-line executable, so this epoch installed the
matching Ubuntu development package:

```text
apt-get update -qq
apt-get install -y libcadical-dev
```

Verification after installation:

```text
cadical 1.7.4-1
libcadical-dev 1.7.4-1
/usr/include/cadical.hpp
/usr/lib/x86_64-linux-gnu/libcadical.a
```

The production driver is compiled from
`tools/novel42_incremental_enumerator.cpp` with `g++ -std=c++17 -O2 ...
-lcadical`.  No service, account, remote, or repository configuration was
changed.  The host reported a pending kernel update; this campaign did not
reboot the host.
