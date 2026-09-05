# Investigation log: buffer-drop bug (found, partially fixed) + channel-count mystery (open)

## Status: buffer bug CONFIRMED and root-caused. Channel-count result CONFIRMED REAL but mechanism NOT YET FOUND.

## Bug found: default request buffer size (32) causes massive silent request drops

While investigating why doubling channel count made latency worse instead of "barely
improving" (Task 4), checked `total_num_read_requests`/`total_num_write_requests`
against the trace's actual line counts and found catastrophic under-completion:

| Run | Completed reads | Attempted reads | Completion rate |
|---|---|---|---|
| Task 1 baseline (5000-line trace) | 92 | ~3500 | ~2.6% |
| Task 2 FRFCFS (20000-line multibank) | 1185 | 14013 | ~8.5% |
| Task 3 RoBaRaCoCh (20000-line multibank) | 962 | 14013 | ~6.9% |
| Task 4 1-channel (20000-line multibank, buffer=32) | 962 | 14013 | ~6.9% |
| Task 4 2-channel (buffer=32) | 1818 | 14013 | ~13.0% |

**Root cause**: `ReqBuffer::max_size` defaults to 32 (`base/request.h`). `GenericDRAMController::setup()` explicitly sets `m_priority_buffer.max_size = 512*3+32` but never touches `m_read_buffer.max_size` or `m_write_buffer.max_size` — both silently stay at the tiny default. Our synthetic traces deliberately generate bursts of 15-40 back-to-back same-region accesses (to stress scheduling), which overwhelms a 32-entry buffer almost immediately; `ReqBuffer::enqueue()` returns `false` on overflow and `GenericDRAMController::send()` (and above it, `ReadWriteTrace::tick()`) never checks that return value — the request is just silently discarded, with zero indication in the console output.

**This affects every single result reported in Part D up to this point** (Tasks 1-4), not just the channel comparison. All `avg_read_latency`/`row_hits`/`row_misses` numbers computed under the small-buffer configuration reflect a small, non-representative surviving subset of each trace, biased toward requests that happened to arrive when the queue had room — not the trace's actual full behavior.

## Fix (in progress)

Patched `GenericDRAMController::setup()` to explicitly size `m_read_buffer`/`m_write_buffer`.
Two false starts before landing on the right fix, both instructive:

1. **First attempt: `max_size = 1024`.** Improved completion (1-channel: 8678/14013 = 61.9% reads)
   but still far from 100%.
2. **Second attempt: `max_size = 8192`, then `16384`.** Reached 100% completion
   (14013/14013 reads, 5987/5987 writes) for both 1-channel and 2-channel configs on
   the 20000-line multibank trace. This is confirmed correct and necessary.
3. **Confound discovered mid-fix**: `set_write_mode()`'s read/write-mode-switching
   watermarks (`wr_high_watermark`/`wr_low_watermark`, default 0.8/0.2) are computed
   as *fractions of* `max_size` — so changing `max_size` also silently changes the
   *absolute* pending-write count needed to trigger a mode switch (from ~26 at the
   old default to ~13,107 at max_size=16384). Initially tried to "preserve" the old
   absolute threshold by overriding the watermark fractions in config — this was a
   **mistake**: the old absolute threshold (26) was never a deliberate design choice,
   just an accidental side effect of the unconfigured default buffer size. The
   fractional default (0.8/0.2) is the more principled, scale-invariant design.
   Reverted the watermark override; kept `max_size=16384` with default watermarks.
   Confirmed this reaches 100% completion cleanly with no distortion.

## Consequence: Tasks 1-3's "final" numbers in the README need re-running

Only Task 4's 1-channel vs 2-channel comparison has been re-run with the buffer fix
in place so far. **Tasks 1, 2, and 3's numbers currently in README.md were generated
with the buggy small buffer and need to be regenerated** with
`max_size=16384`/default watermarks before they can be trusted. The qualitative
findings (FRFCFS beats FCFS on row hits; RoBaRaCoCh vs ChRaBaRoCo genuinely differ)
are very likely still directionally correct, since both sides of each comparison used
the identically-sized (buggy) buffer — but the exact magnitudes need re-verification,
and given the channel-count result's ratio changed substantially (1.9x → 3.1x) once
corrected, magnitudes elsewhere may shift too, possibly non-trivially.

**TODO before finalizing Part D**: re-run Task 1 baseline, Task 2 (FRFCFS/FCFS), and
Task 3 (RoBaRaCoCh/ChRaBaRoCo) with the corrected buffer configuration, and update
the README with corrected numbers.

## Channel-count mystery: real, robust, root cause NOT yet found

With the buffer bug fixed (100% completion, verified identical total work in both
configs), the channel-count result not only survived but got *more* pronounced:

| | 1 channel | 2 channels (per channel) | Ratio |
|---|---|---|---|
| Buggy buffer (32) | 248.0 cycles | 476.4 / 455.1 cycles | ~1.9x |
| Fixed buffer (16384), 100% completion both sides | 1215.3 cycles | 3774.0 / 3826.1 cycles | **~3.1x** |

Row-buffer hit rates are nearly identical between 1-channel (74.6%) and 2-channel
(74.5% combined) — ruling out row-buffer efficiency as the differentiator.

**Hypotheses tested and REJECTED, each via a real ablation/comparison, not assumption**:
1. Survivorship bias from unequal buffer-drop rates — REJECTED: both configs now at
   100% completion, ratio got worse, not better, when this was controlled for.
2. `tRFC` (refresh) amortization — REJECTED: patched `AllBankRefresh` to never fire
   (`m_next_refresh_cycle = 999999999`), reran both configs, got bit-identical
   results to the refresh-enabled case. Refresh contributes nothing to this gap.
   (In hindsight, `tREFI≈12480` cycles exceeds the 7500-cycle short-trace window
   entirely, so refresh could never have fired in that run regardless — should have
   caught this by arithmetic before proposing the hypothesis, not after disproving it.)
3. Watermark distortion from the buffer-size fix itself — REJECTED: confirmed default
   0.8/0.2 fractional watermarks (not the artificially-preserved absolute thresholds)
   produce the same ~3.1x ratio; not an artifact of the buffer fix's side effects.

**Confirmed structurally sound** (not yet a root cause, just ruled out as trivial bugs):
- `GenericDRAMSystem::tick()` calls `m_dram->tick()` once and loops over ALL
  controllers calling `->tick()` every single system cycle — no round-robin/shared-slot
  serialization between channels at this level.
- `m_dram` is a single shared "top-level node wrapping all channel nodes" (per its own
  code comment) — this is the intended, normal design for a multi-channel model, not
  itself suspicious, but its *internal* per-channel timing/`check_ready()` logic has
  not yet been examined.

## Next steps (resume here)

1. Re-run Tasks 1-3 with the corrected buffer size; update README with real numbers.
2. For the channel mystery: read `IDRAM`'s (or `DDR4`'s) internal `check_ready()`
   implementation and per-channel timing-constraint bookkeeping — this is the one
   layer not yet opened. Check specifically whether any per-channel state
   (bandwidth counters, shared timing arrays) is inadvertently indexed/shared
   incorrectly across channel instances.
3. Consider also checking whether `clock_ratio` or `tCK`/frequency scale unexpectedly
   with channel count in the DDR4 timing model setup — a shared-bandwidth-pool effect
   would be consistent with the observed result (splitting into channels doesn't
   grant proportionally more real bandwidth) and hasn't been directly ruled out yet.

## Artifacts
- Modified source (uncommitted patch pending, revert-and-reapply cleanly before
  finalizing): `generic_dram_controller.cpp` (`m_read_buffer.max_size = 16384`,
  `m_write_buffer.max_size = 16384`, added after existing `m_priority_buffer.max_size` line)
- Results confirming the buffer bug and its fix: `results/task4_bufferfix_*.log`,
  `results/task4_buf8192_*.log`, `results/task4_final2_*.log`
- Refresh-ablation results (refresh disabled): `results/task4_norefresh_*.log`
