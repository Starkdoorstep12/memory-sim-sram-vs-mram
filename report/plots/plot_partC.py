import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.rcParams['font.size'] = 11

df = pd.read_csv('data/partC_sram_vs_mram.csv')
df['ratio'] = df['mram'] / df['sram']
df = df.sort_values('ratio')
colors = ['#2ca02c' if r < 1 else '#d62728' for r in df['ratio']]

fig, ax = plt.subplots(figsize=(7.5, 4.2))
y_pos = range(len(df))
bars = ax.barh(y_pos, df['ratio'], color=colors, edgecolor='black', linewidth=0.6)
ax.axvline(1, color='black', linewidth=1, linestyle='--')
ax.set_yticks(y_pos)
ax.set_yticklabels(df['metric'])
ax.set_xlabel('STT-MRAM / SRAM ratio (log scale)')
ax.set_xscale('log')
ax.set_xlim(0.05, 8)
ax.set_title('STT-MRAM vs SRAM L2 (2 MB, 45nm)', fontsize=13)

for bar, r in zip(bars, df['ratio']):
    label = f'{r:.2f}x'
    x = bar.get_width()
    if r < 1:
        ax.text(x * 0.85, bar.get_y() + bar.get_height()/2, label, va='center', ha='right', fontsize=9)
    else:
        ax.text(x * 1.1, bar.get_y() + bar.get_height()/2, label, va='center', ha='left', fontsize=9)

ax.text(0.98, -0.16, 'STT-MRAM worse \u2192', transform=ax.transAxes, ha='right', fontsize=9, color='#d62728')
ax.text(0.02, -0.16, '\u2190 STT-MRAM better', transform=ax.transAxes, ha='left', fontsize=9, color='#2ca02c')
plt.tight_layout()
plt.savefig('plots/plot_partC.png', dpi=200)
print("saved")
