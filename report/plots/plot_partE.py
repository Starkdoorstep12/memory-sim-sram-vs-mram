import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
matplotlib.rcParams['font.size'] = 11

df = pd.read_csv('data/partE_gem5.csv')
kernels = df['kernel'].unique()
x = np.arange(len(kernels))
width = 0.32

sram = df[df['config']=='SRAM'].set_index('kernel')
mram = df[df['config']=='STT-MRAM'].set_index('kernel')

fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.8))

axes[0].bar(x - width/2, sram.loc[kernels, 'ipc'], width, label='SRAM (2MB)', color='#4c72b0', edgecolor='black', linewidth=0.6)
axes[0].bar(x + width/2, mram.loc[kernels, 'ipc'], width, label='STT-MRAM (8MB)', color='#dd8452', edgecolor='black', linewidth=0.6)
axes[0].set_xticks(x); axes[0].set_xticklabels(kernels)
axes[0].set_ylabel('IPC'); axes[0].set_title('IPC (O3CPU)')
axes[0].legend(fontsize=9, loc='upper right')
for i, k in enumerate(kernels):
    axes[0].text(i - width/2, sram.loc[k,'ipc'] + 0.02, f"{sram.loc[k,'ipc']:.2f}", ha='center', fontsize=8.5)
    axes[0].text(i + width/2, mram.loc[k,'ipc'] + 0.02, f"{mram.loc[k,'ipc']:.2f}", ha='center', fontsize=8.5)
axes[0].set_ylim(0, 1.15)

axes[1].bar(x - width/2, sram.loc[kernels, 'l2_miss_rate_pct'], width, label='SRAM (2MB)', color='#4c72b0', edgecolor='black', linewidth=0.6)
axes[1].bar(x + width/2, mram.loc[kernels, 'l2_miss_rate_pct'], width, label='STT-MRAM (8MB)', color='#dd8452', edgecolor='black', linewidth=0.6)
axes[1].set_xticks(x); axes[1].set_xticklabels(kernels)
axes[1].set_ylabel('L2 miss rate (%)'); axes[1].set_title('L2 miss rate')
axes[1].legend(fontsize=9, loc='upper right')
for i, k in enumerate(kernels):
    axes[1].text(i - width/2, sram.loc[k,'l2_miss_rate_pct'] + 0.8, f"{sram.loc[k,'l2_miss_rate_pct']:.1f}%", ha='center', fontsize=8.5)
    axes[1].text(i + width/2, mram.loc[k,'l2_miss_rate_pct'] + 0.8, f"{mram.loc[k,'l2_miss_rate_pct']:.1f}%", ha='center', fontsize=8.5)
axes[1].set_ylim(0, 42)

fig.suptitle('gem5: SRAM vs STT-MRAM L2, O3CPU, GAPBS -g 18', fontsize=12)
plt.tight_layout(rect=[0, 0.02, 1, 0.93])
plt.savefig('plots/plot_partE.png', dpi=200)
print("saved")
