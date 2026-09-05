#!/bin/bash
cd ~/memory-sim-sram-vs-mram/part_b_cacti/configs
echo "capacity_bytes,access_time_ns,cycle_time_ns,dyn_read_energy_nJ,leakage_mW,area_mm2" > ../results/task2_capacity_sweep.csv

for size in 262144 524288 1048576 2097152 4194304 8388608 16777216; do
  sed "s/^-size (bytes) [0-9]*/-size (bytes) ${size}/" cache.cfg > sweep_cfg.cfg
  out=$(../../cacti-src/cacti -infile sweep_cfg.cfg 2>&1)

  access=$(echo "$out" | grep "Access time (ns):" | awk -F': ' '{print $2}')
  cycle=$(echo "$out" | grep "Cycle time (ns):" | awk -F': ' '{print $2}')
  energy=$(echo "$out" | grep "Total dynamic read energy per access (nJ):" | awk -F': ' '{print $2}')
  leak=$(echo "$out" | grep "Total leakage power of a bank (mW):" | head -1 | awk -F': ' '{print $2}')
  data_area=$(echo "$out" | grep "Data array: Area (mm2):" | awk -F': ' '{print $2}')
  tag_area=$(echo "$out" | grep "Tag array: Area (mm2):" | awk -F': ' '{print $2}')
  total_area=$(echo "$data_area + $tag_area" | bc)

  echo "${size},${access},${cycle},${energy},${leak},${total_area}" >> ../results/task2_capacity_sweep.csv
  echo "size=${size}B -> access=${access}ns leak=${leak}mW area=${total_area}mm2"
done

rm -f sweep_cfg.cfg
