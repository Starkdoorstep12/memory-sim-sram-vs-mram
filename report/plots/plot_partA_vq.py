import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.rcParams['font.size'] = 11

# wrdata format: t,v(bl),t,v(blb),t,v(q),t,v(qb) -- no header.
# Confirmed column 5 = v(q): max within [1ns,4ns] = 0.2055V, matching Task 1's
# ngspice-reported qmax exactly. The netlist's own .meas restricts to
# FROM=1n TO=4n specifically because WL=0 until t=1n (PWL(0 0 1n 0 1.05n VDD)) --
# nothing can physically couple into q before the wordline asserts, so anything
# before 1ns is pre-read numerical settling, not real device behavior. Plot
# starts at 0.9ns to show the WL turn-on cleanly without that meaningless region.
df = pd.read_csv('data/partA_vq_nominal_raw.csv', header=None, sep=r'\s+')
t_ns = df[4] * 1e9
vq = df[5]
mask = t_ns >= 0.9
t_ns, vq = t_ns[mask], vq[mask]

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.plot(t_ns, vq, color='#4c72b0', linewidth=1.8)
ax.axvline(1.0, color='#2ca02c', linestyle='-', linewidth=1, alpha=0.7, label='WL asserts (t=1.0ns)')
ax.axhline(0.55, color='#d62728', linestyle='--', linewidth=1, label='Inverter trip point (~550mV)')
ax.axvline(2.0, color='gray', linestyle=':', linewidth=1, label='t=2.0ns (Task 1 \u0394V measurement)')
qmax_val = vq[(t_ns >= 1.0) & (t_ns <= 4.0)].max()
qmax_t = t_ns[vq == qmax_val].values[0]
ax.plot(qmax_t, qmax_val, 'o', color='#d62728', markersize=6, zorder=5)
ax.annotate(f'qmax={qmax_val*1000:.1f}mV', (qmax_t, qmax_val), textcoords="offset points", xytext=(8, 8), fontsize=9)
ax.set_xlabel('Time (ns)')
ax.set_ylabel('v(q) (V)')
ax.set_title('Storage node v(q) during read, nominal W_acc=0.16\u00b5m')
ax.legend(fontsize=8.5, loc='upper right')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('plots/plot_partA_vq.png', dpi=200)
print("saved")
