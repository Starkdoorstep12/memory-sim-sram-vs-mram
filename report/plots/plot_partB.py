import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
matplotlib.rcParams['font.size'] = 11

df = pd.read_csv('data/partB_capacity_sweep.csv')
df['log2_capacity_KB'] = np.log2(df['capacity_bytes'] / 1024)

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.plot(df['log2_capacity_KB'], df['access_time_ns'], marker='o', color='#4c72b0', linewidth=2)
ax.set_xlabel('log2(capacity in KB)')
ax.set_ylabel('Access time (ns)')
ax.set_title('CACTI: access time vs capacity, 256KB \u2192 16MB (45nm, ED\u00b2P)')
ax.set_ylim(2, 7)

labels = [f"{int(c/1024)}KB" if c < 1048576 else f"{int(c/1048576)}MB" for c in df['capacity_bytes']]
for x, y, lbl in zip(df['log2_capacity_KB'], df['access_time_ns'], labels):
    ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8.5)

ax.axvspan(df['log2_capacity_KB'].iloc[0]-0.3, df['log2_capacity_KB'].iloc[4]+0.3, alpha=0.08, color='green')
ax.text(df['log2_capacity_KB'].iloc[2], 6.3, 'Amrutur & Horowitz heuristic\nholds (256KB\u20134MB)',
        ha='center', fontsize=9, color='#2ca02c')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('plots/plot_partB.png', dpi=200)
print("saved")
