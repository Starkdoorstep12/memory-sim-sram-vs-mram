import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.rcParams['font.size'] = 11

df = pd.read_csv('data/partD_scheduler.csv')
colors = ['#1f77b4', '#ff7f0e']

fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.8))

axes[0].bar(df['scheduler'], df['row_buffer_hits'], color=colors, edgecolor='black', linewidth=0.6, width=0.55)
axes[0].set_ylabel('Row-buffer hits (count)')
axes[0].set_title('Row-buffer hits')
axes[0].set_ylim(0, max(df['row_buffer_hits'])*1.15)
for i, v in enumerate(df['row_buffer_hits']):
    axes[0].text(i, v + 40, str(v), ha='center', fontsize=10)
pct_hits = (df['row_buffer_hits'][0]/df['row_buffer_hits'][1] - 1) * 100
axes[0].text(0.5, -0.22, f'+{pct_hits:.1f}% with FRFCFS', transform=axes[0].transAxes, ha='center', fontsize=9, style='italic')

axes[1].bar(df['scheduler'], df['avg_read_latency_cycles'], color=colors, edgecolor='black', linewidth=0.6, width=0.55)
axes[1].set_ylabel('Average read latency (cycles)')
axes[1].set_title('Average read latency')
axes[1].set_ylim(0, max(df['avg_read_latency_cycles'])*1.15)
for i, v in enumerate(df['avg_read_latency_cycles']):
    axes[1].text(i, v + 20, f'{v:.1f}', ha='center', fontsize=10)
pct_lat = (df['avg_read_latency_cycles'][0]/df['avg_read_latency_cycles'][1] - 1) * 100
axes[1].text(0.5, -0.22, f'{pct_lat:.1f}% with FRFCFS', transform=axes[1].transAxes, ha='center', fontsize=9, style='italic')

fig.suptitle('Ramulator 2.0: FRFCFS vs FCFS on multi-bank trace (14,013 reads, 5,987 writes)', fontsize=12)
plt.tight_layout(rect=[0, 0.03, 1, 0.94])
plt.savefig('plots/plot_partD.png', dpi=200)
print("saved")
