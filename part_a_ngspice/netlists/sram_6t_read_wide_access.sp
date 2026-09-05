* AMCAS TakeHomeLab - 6T read, Task 2: widened access transistors (W=0.24u)
.include ../models/45nm_bulk.txt $ PTM BSIM4 card
.param VDD=1.1 VBL=1.1
Vdd vdd 0 'VDD'
Vwl wl 0 PWL(0 0 1n 0 1.05n 'VDD')
MP1 qb q vdd vdd pmos W=0.15u L=0.045u
MN1 qb q 0 0 nmos W=0.20u L=0.045u
MP2 q qb vdd vdd pmos W=0.15u L=0.045u
MN2 q qb 0 0 nmos W=0.20u L=0.045u
MA1 bl wl q 0 nmos W=0.24u L=0.045u
MA2 blb wl qb 0 nmos W=0.24u L=0.045u
Cbl bl 0 180f IC='VBL'
Cblb blb 0 180f IC='VBL'
.ic v(q)=0 v(qb)='VDD'
.control
 tran 5p 4n uic
 let dv_vec = v(blb) - v(bl)
 meas tran dv FIND dv_vec AT=2.0n
 meas tran qmax MAX v(q) FROM=1n TO=4n
 wrdata ../results/read_wide_access.csv v(bl) v(blb) v(q) v(qb)
.endc
.end
