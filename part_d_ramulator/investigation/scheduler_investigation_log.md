# Investigation log: FRFCFS vs FCFS produce identical output (unsolved, revisit later)

## Status: PAUSED — real mechanism partially identified, root cause not yet confirmed

## The observation
Task 2 asks: switch Scheduler from FRFCFS to FCFS, expect row-buffer hit rate to
collapse and latency to increase (quantify in cycles, explain via tRCD/tRP).

Actual result across **four independently-designed synthetic traces** (increasing
in sophistication, each designed to fix a hypothesized flaw in the previous one):
FRFCFS and FCFS produce **bit-for-bit identical** `memory_system_cycles`,
`avg_read_latency_0`, `row_hits_0`, `row_misses_0`, and even byte-identical
per-cycle DRAM command sequences (verified via `TraceRecorder` plugin diff).

## Traces tried, in order, and why each was rejected as insufficient

1. `l2miss.trace` (5000 lines, heavy exact-address repetition, locality-biased).
   Rejected: repetition triggers store-to-load forwarding
   (`generic_dram_controller.cpp:132-141`), but only ~4% of lines — not enough
   to explain total invariance. Confirmed via direct trace analysis.

2. `l2miss_dense.trace` (20000 lines, 6 interleaved "hot rows", distinct
   addresses per row). Rejected: still fully identical output. Confirmed via
   `[compare]` debug print that `ready1`/`ready2` are equal in every sampled
   call (`cmd1=4 cmd2=4`, both false) — meaning FRFCFS's `ready1 ^ ready2`
   branch never fires; it always falls through to its own arrival-order
   fallback, converging with FCFS by construction for this trace.

3. `l2miss_burst.trace` (20000 lines, long bursts of 15-40 consecutive
   accesses to the *same* row before switching rows — designed to keep one
   row open long enough that some requests become row-hit-ready while a
   different-row request is still waiting on ACT). Rejected: identical result
   again. Tested under both `ClosedRowPolicy` and `OpenRowPolicy` (the latter
   confirmed to genuinely change `row_hits_0` from 201→934 in a single-scheduler
   test, proving the simulation IS sensitive to row policy — but scheduler
   choice still made zero difference).

4. `l2miss_multibank.trace` (20000 lines, 8 bank-target regions spaced
   50,000,000 addresses apart — deliberately far wider than DDR4_8Gb_x8's
   plausible bank-field width, to guarantee crossing bank-select address bits
   regardless of exact RoBaRaCoCh bit-layout assumptions). Rejected: still
   identical. `[compare]` sampling (every 500th call, ~477 samples spread
   across the full 20000-request run, not just startup) confirms `ready1==ready2`
   in 100% of sampled comparisons (417 both-false, 60 both-true, zero
   disagreements).

## What's confirmed (high confidence)
- Our new `FCFS` scheduler class is genuinely instantiated and invoked
  (confirmed via debug print inside `FCFS::compare()`).
- `memory_system_cycles` is a **deterministic function of trace line count
  alone**: exactly `num_lines × 3/8` in every trace tried (5000→1875,
  20000→7500). This is because `ReadWriteTrace::tick()`
  (`readwrite_trace.cpp`) calls `m_memory_system->send()` unconditionally,
  every tick, with **no backpressure check** — the frontend runs open-loop.
  Combined with our `is_finished()` fix (fires once the trace has been
  *submitted* once, not once it's been *serviced*), total simulated duration
  reflects submission time, not completion/congestion time. This alone
  explains why memory_system_cycles can never respond to a scheduling policy
  change, regardless of the readiness-symmetry question below.
- `check_ready()` returns the same boolean for both requests being compared,
  every single time, across all four traces and both row policies tested.
  `FRFCFS`'s only behavioral difference from FCFS (the `ready1 ^ ready2`
  branch in `generic_scheduler.cpp`) never fires as a result — the two
  schedulers are provably equivalent for every workload attempted so far,
  not coincidentally identical.

## Leading hypothesis, NOT yet confirmed
`check_ready()` may be gated primarily by a **shared command-bus/channel-level
constraint** (e.g., "can any command be issued on this channel this cycle at
all") rather than by per-bank/per-row state. If true, `ready1` and `ready2`
would be structurally equal for any two requests compared in the same tick,
regardless of which banks they target — meaning no synthetic trace could ever
produce disagreement, because the bottleneck isn't address-pattern-dependent
at all. This would need tracing `check_ready()`'s actual implementation in
the DDR4 device model (`src/dram/impl/DDR4.cpp` and whatever timing-constraint
base class it calls into) — a layer deeper than anything investigated so far
today.

## To resume this investigation
1. Read `IDRAM::check_ready()` and trace where it's actually implemented for
   DDR4 (likely a generic constraint-check function in `dram/node.cpp` or
   `dram/device.cpp`, since DDR4.cpp itself is mostly a DSL-driven timing
   spec, not raw C++ constraint logic).
2. If it IS a shared per-channel gate: confirm by checking whether it depends
   on `req->addr_vec` bank-index at all, or only on global channel/timing
   state (`m_clk` vs last-issued-command-cycle).
3. If confirmed structural: this becomes the real Task 2 answer — "in this
   single-channel Ramulator2 v2.0a config, FRFCFS and FCFS are provably
   equivalent because command issue is gated by a shared per-cycle resource,
   not per-bank readiness; bank-level scheduling benefits would only appear
   with a controller/config that allows genuinely concurrent per-bank command
   issue." This is a stronger, more specific finding than what's in the
   README currently.
4. Debug instrumentation added and since reverted (for a clean build): see
   `patches/scheduler_debug_instrumentation.patch` for the exact debug prints
   used, if reproducing this investigation.

## Artifacts
- Traces: `traces/l2miss.trace`, `l2miss_dense.trace`, `l2miss_burst.trace`,
  `l2miss_multibank.trace`
- Configs: `configs/ddr4_dense_frfcfs.yaml`, `ddr4_dense_fcfs.yaml`,
  `ddr4_burst_frfcfs.yaml`, `ddr4_burst_fcfs.yaml`, `ddr4_burst_open_frfcfs.yaml`,
  `ddr4_burst_open_fcfs.yaml`, `ddr4_multibank_frfcfs.yaml`, `ddr4_multibank_fcfs.yaml`
- Results/logs: `results/task2_*.log` (all variants)
- Debug patch (reverted from the working tree, kept for reference):
  `patches/scheduler_debug_instrumentation.patch`
