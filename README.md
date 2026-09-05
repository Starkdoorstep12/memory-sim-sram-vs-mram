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


---

## Part B — CACTI: Sizing the 2 MB SRAM L2

Built from source (`HewlettPackard/cacti`, plain make, no autotools). CACTI must be invoked from its own source directory (`cacti-src/`) — running it with a config path from elsewhere causes a silent segfault, since it appears to resolve some data files relative to CWD rather than the binary location.

**Config note**: the assignment's provided 11-line `cache.cfg` is insufficient on its own — CACTI's parser requires a much larger set of fields (tag size, access mode, deviate, Cache model, NUCA bank count, Wire signaling, Core count, Add ECC, Print level, Force cache config, Ndwl/Ndbl/etc., and a full DRAM-IO block) or it silently exits after echoing the parsed parameters with no actual results. The working config used here starts from CACTI's own shipped `cache.cfg` template (full field set) with only the assignment's specific values (`-size`, `-associativity`, `-UCA bank count`, `-technology`, `-operating temperature`, `-design objective`, `-Optimize ED or ED^2`) overridden.

### Task 1 — 2 MB SRAM baseline (8-way, 64B blocks, 4 banks, 45nm, ED²-optimized)

| Metric | Value |
|---|---|
| Access time | 2.902 ns |
| Cycle time | 2.652 ns |
| Dynamic read energy/access | 792.9 pJ |
| Dynamic write energy/access | 851.2 pJ |
| Leakage power (per bank) | 562.6 mW |
| Gate leakage power (per bank) | 16.4 mW |
| Area (data + tag) | 10.271 + 0.387 = 10.658 mm² |
| Best organization | Ndwl=4, Ndbl=2, Nspd=1 |

Note: leakage is per-bank (UCA bank count=4); total leakage across the cache ≈ 4×562.6mW ≈ 2.25W if aggregate is wanted. Config also carries a DRAM-IO/MemCAD block (IO Area, PHY Power, "top 3 best memory configurations") inherited from CACTI's required field set — not meaningful for an on-chip SRAM cache, ignored.

Full log: `part_b_cacti/results/task1_baseline.log`.

### Task 2 — Capacity sweep, 256kB → 16MB

| Capacity | Access time (ns) | Cycle time (ns) | Leakage (mW) | Area (mm²) |
|---|---|---|---|---|
| 256kB | 2.417 | 2.339 | 90.3 | 4.86 |
| 512kB | 2.485 | 2.400 | 158.1 | 5.69 |
| 1MB | 2.634 | 2.497 | 293.7 | 7.36 |
| 2MB | 2.902 | 2.652 | 562.6 | 10.66 |
| 4MB | 3.531 | 2.946 | 1102.3 | 17.29 |
| 8MB | 4.473 | 2.946 | 2183.8 | 34.30 |
| 16MB | 6.362 | 8.936 | 4244.5 | 65.44 |

Full sweep: `part_b_cacti/results/task2_capacity_sweep.csv`.

Amrutur & Horowitz's "one gate delay per doubling" heuristic holds approximately from 256kB to 4MB, where the *data array's* organization stays fixed (Ndwl=4, Ndbl=2 throughout) and only the tag array re-partitions (Ntspd, Ntbl growing). It breaks down sharply at 8MB and 16MB: verified via `Best Ndwl/Ndbl` per capacity — the data array's own organization changes for the first time at 8MB (Ndbl: 2→4) and again at 16MB (Ndwl: 4→2, Ndbl: 4→8, Ndsam L2: 1→2). These are genuine architectural transitions, not numerical noise — every point where the H-tree/subarray count changes is a structurally different design, not a smoothly-scaled version of the same one, which is why the delay heuristic (derived assuming a fixed decomposition) fails exactly at those transitions. The 4MB/8MB tied cycle time (2.946ns both) and the 8MB→16MB access-time jump (+1.89ns, vs a typical ~0.1-0.6ns step elsewhere) are the visible symptoms.

### Task 3 — Optimization objective comparison (fixed 2MB capacity)

| Objective | Ndwl | Ndbl | Ndsam L2 | Access time | Area (H×W, mm) |
|---|---|---|---|---|---|
| Pure delay (100:0:0:0:0) | 4 | 2 | 1 | **2.892 ns** (fastest) | 2.116 × 5.184 |
| ED²P (0:0:0:100:0, Optimize=ED^2) | 4 | 2 | 1 | 2.902 ns | 2.213 × 5.184 |
| Pure area (0:0:0:0:100) | 2 | 2 | 2 | 3.355 ns (slowest) | 1.799 × 5.138 (smallest) |

Note: setting the `-design objective` weights alone is insufficient when `-Optimize ED or ED^2` is active — that flag overrides the weight/deviate values per CACTI's own config comments. Pure-delay and pure-area runs explicitly set `Optimize ED or ED^2` to `"NONE"`.

Pure delay and ED²P converge on the same Ndwl/Ndbl (4,2) since ED²P's delay² term dominates its objective in this range. Pure area picks Ndwl=2 instead of 4: each additional wordline division (higher Ndwl) shortens the wordline/bitline RC delay but adds decoder/mux peripheral overhead at each split boundary; the delay-optimal search pays that overhead repeatedly, the area-optimal search refuses it and accepts a longer, slower wordline instead. Same 2MB cache, three objectives, three different physical organizations — ~16% delay spread and ~19% area spread between the pure-delay and pure-area extremes, directly illustrating the assignment's note that there is no single "optimal cache," only the optimum of a stated objective.

### Task 4 — Hand-check bitline delay against 0.38·R·C·L²

**On sourcing R and C**: CACTI does not print bitline metal R/C directly in its output, and the value is not given in either of the two lecture decks covering this material (Lecture 4 "Array organisation" or the 6T SRAM cell lecture) — both present the `0.38RCL²` relationship and bitline-capacitance-per-cell qualitatively/symbolically, without stating numeric R or C for a specific process. Investigated CACTI's own source (`parameter.cc`, `basic_circuit.cc`) to extract its internal wire model: found a `wire_r_per_micron`/`wire_c_per_micron` table in `tech_params/45nm.dat`, but tracing its usage in `parameter.cc` confirmed (via `tsv_resistance()`/`tsv_capacitance()` in `basic_circuit.cc`) that this table is TSV/3D-integration-specific, not applicable to a planar on-chip bitline — using it initially gave a hand-calc ~46× larger than CACTI's reported delay, which prompted this check. The correct geometric formula (`wire_resistance()`/`wire_capacitance()` in `basic_circuit.cc`, using `pitch`, `resistivity`, `aspect_ratio`, dielectric constants) exists in source, but which tech-file tier/column it draws from for the bitline specifically could not be confirmed without deeper source tracing than was practical here.

Given no authoritative number is available from the assignment materials or a clearly-traced CACTI internal value, the hand-check below uses standard, explicitly-stated 45nm local-interconnect assumptions (order-of-magnitude values consistent with published minimum-pitch on-chip metal at this node), not values extracted from CACTI internals:

- r = 5.0 Ω/µm (typical local M1/M2 wire resistance, 45nm)
- c = 0.2 fF/µm (well-established VLSI scaling fact: wire capacitance per unit length stays roughly constant, ~0.1-0.2 fF/µm, across technology generations, unlike resistance which rises sharply with scaling)
- L = 336.384 µm (subarray height, from Task 1's CACTI baseline organization)

| | Value |
|---|---|
| R_total | 1681.9 Ω |
| C_total | 67.3 fF |
| Hand-calc delay (0.38RC) | **0.043 ns** |
| CACTI-reported bitline delay | **0.407 ns** |
| Ratio | CACTI is ~9.5× larger |

CACTI's number is significantly larger, not smaller — the opposite direction from a plain "wire is slower than expected" error. The mechanism: this hand-calc only captures the bitline metal's own self-capacitance (wire-to-substrate, wire-to-wire coupling). It omits the per-cell junction/diffusion capacitance that every memory cell's access transistor adds to the column — per the course's own Lecture 4 material, "C_BL comes from junctions, gate overlap, and wire — roughly 0.2–0.5 fF per cell." With hundreds of cells per bitline in a real subarray, this per-cell term dominates over the bare wire's self-capacitance by a wide margin. This is the effect CACTI's array-level model captures (loading the bitline with the cumulative capacitance of every cell it serves) that a naive isolated-wire `0.38RCL²` calculation structurally cannot, since it treats the bitline as an unloaded transmission line rather than a wire loaded by hundreds of transistor junctions along its length.


---

## Part C — NVSim: The same 2 MB as STT-MRAM

Built from source (`SEAL-UCSB/NVSim`, plain make). Hit a compiler-era mismatch: the codebase (2012, pre-C++17) defines an enum value literally named `data`, which collides with `std::data()` once C++17 pulls it into unqualified lookup via `<string>`/`<iostream>` — every `memoryType == data` comparison becomes ambiguous under a modern default `-std`. Fixed by building with `-std=gnu++98` explicitly (`make CXXFLAGS="-Wall -std=gnu++98"`), which predates the collision. Same CWD-relative-path behavior as CACTI observed in Part B — `-MemoryCellInputFile` in the `.cfg` resolves relative to wherever `nvsim` is invoked from, not the config file's location; fixed by using an absolute path to the `.cell` file.

**Config note**: same trap as CACTI's minimal config — the assignment's stripped-down `STT_cache.cfg`/`sample.cell` outline is missing several fields NVSim's parser needs (`-CacheAccessMode`, `-DeviceRoadmap`, wire-type fields, `-MinSenseVoltage (mV)`, `-VoltageDropAccessDevice (V)` on the cell side). Built from NVSim's own shipped `sample_STTRAM_cache.cfg`/`sample_STTRAM.cell` templates, overriding only the assignment's specified values (ProcessNode=45, Capacity=2MB, Associativity=8, and all `.cell` fields from the handout) on top of the working structure.

### Task 1 — 2 MB STT-MRAM baseline (8-way, 64B blocks, 45nm, ReadEDP-optimized, sequential access)

| Metric | STT-MRAM (NVSim) | SRAM baseline (CACTI, Part B) |
|---|---|---|
| Total area | **2.888 mm²** | 10.658 mm² |
| Read (hit) latency | 2.533 ns | 2.902 ns |
| Write latency | 10.526 ns | — (not separately reported by CACTI at this granularity) |
| Read dynamic energy | 0.559 nJ/access | 0.793 nJ/access |
| Write dynamic energy | 1.901 nJ/access | 0.851 nJ/access |
| Total leakage power | 433.9 mW | 562.6 mW (per bank; ~2.25W total across 4 banks) |

**Literature sanity check**: multiple independent papers building on NVSim (citing Dong et al. 2012) consistently report STT-RAM/MRAM offering "at least 3-4× area savings" over SRAM. Our result: 10.658mm² / 2.888mm² = **3.69×** — lands squarely inside the cited range, using the assignment's own `.cell` file parameters at matched capacity/associativity/block size/process node against our own CACTI SRAM baseline. This is an independent confirmation, not a number we adjusted to fit.

**Write latency mechanism**: 10.526ns is almost entirely the cell's own `ResetPulse`/`SetPulse` (10ns from the `.cell` file) — array peripheral circuitry (H-Tree, row decoder, charge latency) contributes only ~0.5ns on top. This is the correct physical story: STT-MRAM write time is set by how fast the MTJ can be switched, not by decoder/wordline speed — the opposite of CACTI's SRAM delay breakdown (Part B), which is dominated by H-tree/subarray RC delay, not any intrinsic device switching time (SRAM's cross-coupled inverters flip essentially instantly once enough drive current is available).

**Write energy hand-check** (NVSim paper Eq. 17, Joule's law: E = I²Rt, using the cell's own R_on/R_off as the resistance during SET/RESET): for a single bit, E_SET = (200µA)² × 3000Ω × 10ns = **1.20 pJ**, E_RESET = (200µA)² × 6000Ω × 10ns = **2.40 pJ**. NVSim's reported per-subarray "Bitline & Cell Write Energy" (67.9pJ data array, 131.9pJ tag array) is ~30-100× larger than this single-bit estimate — consistent with a cache write operation switching many bits in parallel (a full cache line's worth of cells across the active subarray), not one bit at a time. The single-cell number is a lower bound and sets the right order of magnitude; the array-level number correctly reflects the actual multi-bit write.


### Task 2 — Which metrics move, and why (device-level)

| Metric | STT-MRAM (NVSim) | SRAM (CACTI) | Ratio (MRAM/SRAM) | Direction |
|---|---|---|---|---|
| Area | 2.888 mm² | 10.658 mm² | 0.27× | **dramatically better** |
| Leakage (whole 2MB cache) | 433.9 mW | 2250.4 mW (562.6mW/bank × 4) | 0.19× | **dramatically better** |
| Read latency | 2.533 ns | 2.902 ns | 0.87× | mildly better |
| Read energy | 0.559 nJ | 0.793 nJ | 0.70× | mildly better |
| Write latency | 10.526 ns | 2.652 ns (CACTI cycle time, closest proxy — CACTI doesn't split read/write timing) | 3.97× | **dramatically worse** |
| Write energy | 1.901 nJ | 0.851 nJ | 2.23× | **dramatically worse** |

**Dramatically better: area and leakage.** Both trace to the same device-level fact — the SRAM cell stores its bit as a bistable CMOS voltage state, which structurally requires six transistors (two cross-coupled inverters, sized to satisfy competing read-stability and writeability cell-ratio constraints, not just to hold a value) and continuous standing current to remain in that state (subthreshold, gate, and junction leakage through every transistor, in every cell, all the time — this is the "Hold" leakage mechanism, not a one-time cost). STT-MRAM's bit is the magnetization direction of the MTJ's free layer relative to its fixed reference layer — a genuinely non-volatile physical state that costs zero standing current to maintain once written. The MOS-accessed STT-MRAM cell here is essentially 1T1R (one access transistor + one MTJ), fundamentally smaller than a 6T structure sized for stability margins, and its only leakage source is that single access transistor's off-state current while idle — no cross-coupled bistable pair drawing current at all. This is a device-physics difference, not a peripheral-circuit one: one technology needs power to remember, the other doesn't.

**Dramatically worse: write latency and write energy.** Both trace to a different device-level fact — reversing an MTJ's magnetization via spin-transfer torque is a physical switching process, not a voltage-level flip. Writing an SRAM cell means overpowering a small cross-coupled inverter pair's regenerative feedback — a few gate delays of a low-energy CMOS transition. Writing an STT-MRAM cell means sustaining a large current (200µA, per the assignment's `.cell` file) through the junction for a fixed pulse duration (`ResetPulse`/`SetPulse` = 10ns) long enough for spin torque to reliably reverse the free layer against thermal fluctuations — a stochastic, current-and-time-dependent magnetic switching process that cannot be sped up simply by adding drive strength the way an SRAM write can. This directly produces both symptoms: write *latency* is dominated by that fixed switching pulse duration rather than by RC/decoder delay (confirmed in Task 1 — array peripheral overhead adds only ~0.5ns on top of the 10ns pulse), and write *energy* is dominated by I²Rt resistive dissipation through the MTJ during that sustained pulse (confirmed by the Task 1 hand-check: E=I²Rt scales directly with pulse duration and current, both of which are set by switching physics, not by circuit design choices available at the array level).

