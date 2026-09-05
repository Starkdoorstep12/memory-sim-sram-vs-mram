# Memory Sim: SRAM vs STT-MRAM L2 (ECE2.414 Assignment 1)

Central question: should the 2 MB L2 cache in our accelerator be SRAM, or STT-MRAM?
Five tools, one design decision, carried end to end: ngspice → CACTI → NVSim → Ramulator 2.0 → gem5.

Repo layout: one directory per part (`part_a_ngspice/`, `part_b_cacti/`, ...), each with `netlists|configs/`, `results/`.

---

## Part A — ngspice: 6T SRAM bitcell read margin

Netlist: `part_a_ngspice/netlists/sram_6t_read.sp`. 45nm PTM BSIM4, VDD=1.1V, W_acc=0.16µm (nominal), Q=0/QB=1.1V stored.

### Task 1 — Read margin at nominal conditions

ΔV(BLB−BL) measured at t=2.0ns (as specified in the base netlist) = **729.9 mV**, against the 69 mV Lecture 1 reference.

The two numbers aren't measuring the same event. Tracing the full transient: ΔV first crosses 69 mV at t=1.1175ns — **67.5 ps after the wordline turns on** (WL asserts at 1.05ns) — where it measures 71.2 mV, matching the reference closely. The AT=2.0n sample point in the given netlist is taken ~950ps after WL turn-on, by which point BL has continued discharging well past any realistic sense-amp trip point. The 69mV reference corresponds to an early sense-amp decision window; AT=2.0n corresponds to near-complete, unterminated bitline discharge.

`qmax` (peak of v(q) during the read) = 205.5 mV at t=1.0575ns — the storage node does move during the read, confirming the cell is read-disturbed even at nominal sizing, though it does not flip (well below the ~550mV inverter trip point for this cell).

### Task 2 — Access transistor width sweep (cell ratio stress)

Widening MA1/MA2 from the assignment's suggested 0.24µm was extended into a full sweep (0.16µm → 1.00µm) to find the actual failure point, since 0.24µm alone (qmax=271.2mV) does not flip the cell.

| W_acc (µm) | ΔV @2ns | qmax |
|---|---|---|
| 0.16 (nominal) | 729.9 mV | 205.5 mV |
| 0.24 | 852.3 mV | 271.2 mV |
| 0.50 | 948.3 mV | 424.1 mV |
| 0.51 | 945.1 mV | 424.1 mV |
| **0.52** | **284.0 mV** | **533.0 mV** |
| 0.55 | 176.1 mV | 545.0 mV |
| 1.00 | 85.1 mV | 572.1 mV |

Full sweep data: `part_a_ngspice/results/task2_sweep/summary.csv` (22 points, 0.16–1.00µm).

Behavior up to ~0.50µm is a smooth resistive-divider trend (wider access transistor pulls q up further, but pull-down NMOS still wins). Between **W_acc = 0.51µm and 0.52µm** the cell flips discontinuously: qmax jumps from 424mV to 533mV (crossing the ~550mV regenerative trip point of the cross-coupled pair) and ΔV collapses from 945mV to 284mV in the same step, since a flipped q no longer sinks BL cleanly. Failure threshold: **W_acc ≈ 0.515µm ± 5nm, ~3.2× nominal**, corresponding to a cell ratio (pull-down/access) of 0.20/0.515 ≈ 0.39 — well under the >1 ratio needed for read stability.

### Task 3 — VDD sweep, ΔV vs sense-amp offset (25 mV)

Swept VDD from 1.10V down to 0.20V (extended past the assignment's 0.6V floor since ΔV had not yet crossed 25mV at 0.6V: still 143.9mV there). VBL scaled with VDD.

| VDD (V) | ΔV @2ns | qmax |
|---|---|---|
| 1.10 | 729.9 mV | 205.5 mV |
| 0.60 | 143.9 mV | 71.6 mV |
| 0.50 | 53.6 mV | 51.3 mV |
| 0.45 | 25.7 mV | 43.8 mV |
| **0.44** | **21.8 mV** | 42.5 mV |
| 0.40 | 10.7 mV | 38.1 mV |
| 0.20 | 0.11 mV | 25.4 mV |

Full sweep data: `part_a_ngspice/results/task3_vdd_sweep.csv` (22 points, 0.20–1.10V).

ΔV crosses below the 25mV sense-amp offset between **VDD = 0.45V and 0.44V** — **V_DD,min ≈ 0.445V ± 5mV**. Below ~0.40V, qmax becomes slightly non-monotonic (0.20V: 25.4mV vs 0.25V: 23.7mV), consistent with the access/pull-down devices entering subthreshold/near-threshold operation where the strong-inversion resistive-divider picture no longer holds cleanly.

Separately measured the time for ΔV to reach 25mV at each VDD (rather than ΔV at a fixed 2ns): this varies only ~1.06ns→1.20ns across the full VDD range, confirming the fixed-AT=2.0n methodology (matching the assignment's Task 1 setup) is appropriate for Task 3 — read latency degrades gently with VDD, while margin at a fixed sample time degrades sharply.

### Task 4 — Temperature (85°C repeat of Task 1)

| | 27°C | 85°C | Δ |
|---|---|---|---|
| ΔV @2ns | 729.9 mV | 582.1 mV | −147.8 mV (−20.3%) |
| qmax | 205.5 mV | 220.8 mV | +15.2 mV (+7.4%) |

ΔV moves more than the sense-amp offset, and ΔV is what sets the failure. The 20.3% ΔV drop at 85°C is a first-order effect of mobility degradation reducing the access transistor's discharge current (the same mechanism, structurally, as the VDD-sweep result in Task 3 — both act by reducing effective drive current on the access path). The 25mV sense-amp offset is dominated by fixed process-driven Vt mismatch between the amp's differential pair, which has comparatively weak, second-order temperature dependence. Because temperature and low VDD degrade the same quantity (access-path drive current) in the same direction, the Task 3 VDD_min crossing (~0.445V at 27°C) should shift upward at 85°C — worst-case read margin occurs at the low-VDD, high-temperature corner simultaneously, which is why real SRAM datasheets spec minimum VDD per temperature corner rather than a single number.

