import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.rcParams['font.size'] = 11

df = pd.read_csv('data/partA_vdd_sweep.csv')
df['dv_mV'] = df['dv'] * 1000

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.plot(df['vdd'], df['dv_mV'], marker='o', color='#4c72b0', linewidth=2, markersize=4)
ax.axhline(25, color='#d62728', linestyle='--', linewidth=1.2, label='Sense-amp offset (25mV)')
ax.axvline(0.445, color='gray', linestyle=':', linewidth=1, label='V_DD,min \u2248 0.445V')
ax.set_xlabel('V_DD (V)')
ax.set_ylabel('\u0394V (mV)')
ax.set_title('\u0394V(BL,BLB) at t=2.0ns vs V_DD, nominal cell')
ax.legend(fontsize=9, loc='upper left')
ax.grid(alpha=0.3)
ax.invert_xaxis()
plt.tight_layout()
plt.savefig('plots/plot_partA_vdd.png', dpi=200)
print("saved")
