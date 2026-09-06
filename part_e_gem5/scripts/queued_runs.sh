# Run 2: SRAM + sssp (Caches.py already patched for SRAM: 6-cycle L2 latency, 2MB size via flag)
cd ~/memory-sim-sram-vs-mram/gem5-src
nohup ./build/X86/gem5.opt --outdir=../part_e_gem5/results/sram_sssp configs/deprecated/example/se.py \
  --cpu-type=O3CPU --caches --l2cache \
  --l1d_size=32kB --l1i_size=32kB \
  --l2_size=2MB --l2_assoc=8 \
  --mem-type=DDR4_2400_8x8 --mem-size=4GB \
  --cmd=../gapbs-src/sssp --options="-g 18" \
  > ../part_e_gem5/results/sram_sssp_run.log 2>&1 &
disown

# NOTE: before Run 3/4 (STT-MRAM), must re-patch Caches.py L2Cache class:
# tag_latency/data_latency/response_latency = 6 (unchanged, since our NVSim read latency
# also rounds to 6 cycles at 2GHz -- see README for the honest discussion of this).
# L2 size flag changes to --l2_size=8MB (our NVSim-derived STT-MRAM capacity, ~7.38MB rounded).

# Run 3: STT-MRAM + bfs
# cd ~/memory-sim-sram-vs-mram/gem5-src
# nohup ./build/X86/gem5.opt --outdir=../part_e_gem5/results/mram_bfs configs/deprecated/example/se.py \
#   --cpu-type=O3CPU --caches --l2cache \
#   --l1d_size=32kB --l1i_size=32kB \
#   --l2_size=8MB --l2_assoc=8 \
#   --mem-type=DDR4_2400_8x8 --mem-size=4GB \
#   --cmd=../gapbs-src/bfs --options="-g 18" \
#   > ../part_e_gem5/results/mram_bfs_run.log 2>&1 &
# disown

# Run 4: STT-MRAM + sssp
# cd ~/memory-sim-sram-vs-mram/gem5-src
# nohup ./build/X86/gem5.opt --outdir=../part_e_gem5/results/mram_sssp configs/deprecated/example/se.py \
#   --cpu-type=O3CPU --caches --l2cache \
#   --l1d_size=32kB --l1i_size=32kB \
#   --l2_size=8MB --l2_assoc=8 \
#   --mem-type=DDR4_2400_8x8 --mem-size=4GB \
#   --cmd=../gapbs-src/sssp --options="-g 18" \
#   > ../part_e_gem5/results/mram_sssp_run.log 2>&1 &
# disown
