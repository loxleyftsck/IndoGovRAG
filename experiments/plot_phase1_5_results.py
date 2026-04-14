"""
Phase 1.5 Results Visualization
Generates 3 plots to visualize optimization trade-offs
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (18, 6)
plt.rcParams['font.size'] = 10

# Data from 18 configurations
# Format: {config_id: {latency, cost, faithfulness, compression, cache_threshold, hit_rate, cost_reduction}}
configs = {
    '#1': {'latency': 15.3, 'cost': 0.0029, 'faithfulness': 0.780, 'compression': 1.0, 'cache': 0, 'hit_rate': 0, 'cost_reduction': 0},
    '#2': {'latency': 8.2, 'cost': 0.0014, 'faithfulness': 0.780, 'compression': 1.0, 'cache': 0.9, 'hit_rate': 63, 'cost_reduction': 52},
    '#3': {'latency': 8.5, 'cost': 0.0015, 'faithfulness': 0.780, 'compression': 1.0, 'cache': 0.95, 'hit_rate': 54, 'cost_reduction': 48},
    '#4': {'latency': 11.2, 'cost': 0.0019, 'faithfulness': 0.780, 'compression': 1.0, 'cache': 0.97, 'hit_rate': 38, 'cost_reduction': 34},
    '#5': {'latency': 11.8, 'cost': 0.0020, 'faithfulness': 0.768, 'compression': 0.7, 'cache': 0, 'hit_rate': 0, 'cost_reduction': 0},
    '#6': {'latency': 6.4, 'cost': 0.0010, 'faithfulness': 0.768, 'compression': 0.7, 'cache': 0.9, 'hit_rate': 63, 'cost_reduction': 66},
    '#7': {'latency': 6.8, 'cost': 0.0011, 'faithfulness': 0.768, 'compression': 0.7, 'cache': 0.9, 'hit_rate': 63, 'cost_reduction': 62},
    '#8': {'latency': 10.4, 'cost': 0.0017, 'faithfulness': 0.763, 'compression': 0.7, 'cache': 0.95, 'hit_rate': 52, 'cost_reduction': 41},
    '#9': {'latency': 8.9, 'cost': 0.0013, 'faithfulness': 0.768, 'compression': 0.7, 'cache': 0.97, 'hit_rate': 38, 'cost_reduction': 55},
    '#10': {'latency': 9.2, 'cost': 0.0015, 'faithfulness': 0.740, 'compression': 0.5, 'cache': 0, 'hit_rate': 0, 'cost_reduction': 0},
    '#11': {'latency': 5.1, 'cost': 0.0007, 'faithfulness': 0.740, 'compression': 0.5, 'cache': 0.9, 'hit_rate': 63, 'cost_reduction': 76},
    '#12': {'latency': 5.5, 'cost': 0.0008, 'faithfulness': 0.740, 'compression': 0.5, 'cache': 0.95, 'hit_rate': 54, 'cost_reduction': 72},
    '#13': {'latency': 7.2, 'cost': 0.0010, 'faithfulness': 0.740, 'compression': 0.5, 'cache': 0.97, 'hit_rate': 38, 'cost_reduction': 66},
    '#14': {'latency': 17.8, 'cost': 0.0032, 'faithfulness': 0.858, 'compression': 1.0, 'cache': 0, 'hit_rate': 0, 'cost_reduction': 0},
    '#15': {'latency': 10.2, 'cost': 0.0017, 'faithfulness': 0.858, 'compression': 1.0, 'cache': 0.95, 'hit_rate': 54, 'cost_reduction': 41},
    '#16': {'latency': 14.1, 'cost': 0.0023, 'faithfulness': 0.845, 'compression': 0.7, 'cache': 0, 'hit_rate': 0, 'cost_reduction': 0},
    '#17': {'latency': 8.2, 'cost': 0.0013, 'faithfulness': 0.845, 'compression': 0.7, 'cache': 0.95, 'hit_rate': 54, 'cost_reduction': 55},
    '#18': {'latency': 6.9, 'cost': 0.0010, 'faithfulness': 0.815, 'compression': 0.5, 'cache': 0.95, 'hit_rate': 54, 'cost_reduction': 66},
}

def plot_compression_trade_offs():
    """Plot 1: Compression ratio vs Quality vs Latency"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Group by compression ratio
    compression_groups = {
        1.0: [],
        0.7: [],
        0.5: []
    }
    
    for config_id, data in configs.items():
        compression_groups[data['compression']].append((config_id, data))
    
    # Plot each group
    colors = {1.0: 'blue', 0.7: 'green', 0.5: 'red'}
    markers = {1.0: 'o', 0.7: 's', 0.5: '^'}
    
    for comp_ratio, group in compression_groups.items():
        latencies = [d['latency'] for _, d in group]
        qualities = [d['faithfulness'] for _, d in group]
        labels = [cid for cid, _ in group]
        
        ax.scatter(latencies, qualities, 
                  s=200, alpha=0.6, 
                  color=colors[comp_ratio], 
                  marker=markers[comp_ratio],
                  edgecolors='black', linewidth=1.5,
                  label=f'Compression {comp_ratio}')
        
        # Annotate special configs
        for config_id, data in group:
            if config_id in ['#1', '#8', '#17']:
                ax.annotate(config_id, 
                           (data['latency'], data['faithfulness']),
                           fontsize=12, fontweight='bold',
                           xytext=(5, 5), textcoords='offset points')
    
    # Target zone
    ax.add_patch(Rectangle((0, 0.74), 9, 0.12, alpha=0.1, facecolor='green', label='Target Zone'))
    ax.axvline(x=9, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Latency Target: 9s')
    ax.axhline(y=0.74, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Quality Target: 0.74')
    
    ax.set_xlabel('P95 Latency (seconds)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Faithfulness Score', fontsize=14, fontweight='bold')
    ax.set_title('Compression Trade-Off: Latency vs Quality', fontsize=16, fontweight='bold')
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('experiments/plot1_compression_tradeoff.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plot1_compression_tradeoff.png")

def plot_cache_efficiency():
    """Plot 2: Cache threshold vs Cost vs Hit Rate"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Only configs with cache enabled
    cached_configs = {k: v for k, v in configs.items() if v['cache'] > 0}
    
    # Group by cache threshold
    cache_groups = {
        0.9: [],
        0.95: [],
        0.97: []
    }
    
    for config_id, data in cached_configs.items():
        cache_groups[data['cache']].append((config_id, data))
    
    colors = {0.9: 'orange', 0.95: 'green', 0.97: 'blue'}
    markers = {0.9: 'D', 0.95: 's', 0.97: 'v'}
    
    for threshold, group in cache_groups.items():
        hit_rates = [d['hit_rate'] for _, d in group]
        costs = [d['cost'] * 1000 for _, d in group]  # Convert to per-1000-requests
        
        ax.scatter(hit_rates, costs,
                  s=200, alpha=0.6,
                  color=colors[threshold],
                  marker=markers[threshold],
                  edgecolors='black', linewidth=1.5,
                  label=f'Cache Threshold {threshold}')
        
        # Annotate special configs
        for config_id, data in group:
            if config_id in ['#7', '#8', '#17']:
                ax.annotate(config_id,
                           (data['hit_rate'], data['cost'] * 1000),
                           fontsize=12, fontweight='bold',
                           xytext=(5, 5), textcoords='offset points')
    
    # Target zone
    ax.add_patch(Rectangle((40, 0), 30, 1.5, alpha=0.1, facecolor='green', label='Target Zone'))
    ax.axvline(x=40, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Hit Rate Target: 40%')
    ax.axhline(y=1.5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Cost Target: $1.50/1k')
    
    ax.set_xlabel('Cache Hit Rate (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Cost per 1000 Requests ($)', fontsize=14, fontweight='bold')
    ax.set_title('Cache Efficiency: Hit Rate vs Cost', fontsize=16, fontweight='bold')
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('experiments/plot2_cache_efficiency.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plot2_cache_efficiency.png")

def plot_config_comparison():
    """Plot 3: Config ID vs Cost & Quality (dual-axis bar chart)"""
    fig, ax1 = plt.subplots(figsize=(16, 8))
    
    # Sort configs by ID number
    sorted_configs = sorted(configs.items(), key=lambda x: int(x[0].replace('#', '')))
    
    config_ids = [cid for cid, _ in sorted_configs]
    costs = [d['cost'] * 1000 for _, d in sorted_configs]  # Per 1000 requests
    qualities = [d['faithfulness'] for _, d in sorted_configs]
    
    # Create bars
    x = np.arange(len(config_ids))
    width = 0.35
    
    # Cost bars (left axis)
    bars1 = ax1.bar(x - width/2, costs, width, label='Cost ($/1k req)', 
                    color='steelblue', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Configuration ID', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Cost per 1000 Requests ($)', fontsize=14, fontweight='bold', color='steelblue')
    ax1.tick_params(axis='y', labelcolor='steelblue')
    ax1.set_xticks(x)
    ax1.set_xticklabels(config_ids, rotation=45, ha='right')
    
    # Quality bars (right axis)
    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, qualities, width, label='Faithfulness', 
                    color='forestgreen', alpha=0.7, edgecolor='black')
    ax2.set_ylabel('Faithfulness Score', fontsize=14, fontweight='bold', color='forestgreen')
    ax2.tick_params(axis='y', labelcolor='forestgreen')
    ax2.set_ylim([0.70, 0.90])
    
    # Highlight recommended configs
    for i, (config_id, _) in enumerate(sorted_configs):
        if config_id == '#8':
            # Green box for Config #8
            ax1.add_patch(Rectangle((i - 0.5, 0), 1, max(costs), 
                                   alpha=0.15, facecolor='green', zorder=0))
            ax1.text(i, max(costs) * 0.95, 'RECOMMENDED\nBETA', 
                    ha='center', va='top', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        elif config_id == '#17':
            # Purple box for Config #17
            ax1.add_patch(Rectangle((i - 0.5, 0), 1, max(costs),
                                   alpha=0.15, facecolor='purple', zorder=0))
            ax1.text(i, max(costs) * 0.85, 'SCALE-OUT', 
                    ha='center', va='top', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='plum', alpha=0.8))
    
    # Target lines
    ax1.axhline(y=1.5, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Cost Target')
    ax2.axhline(y=0.74, color='darkred', linestyle='--', linewidth=2, alpha=0.5, label='Quality Threshold')
    
    ax1.set_title('Configuration Comparison: Cost vs Quality', fontsize=16, fontweight='bold', pad=20)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    ax1.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('experiments/plot3_config_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plot3_config_comparison.png")

def main():
    """Generate all 3 plots"""
    print("\n🎨 Generating Phase 1.5 Visualization Plots...\n")
    
    plot_compression_trade_offs()
    plot_cache_efficiency()
    plot_config_comparison()
    
    print("\n✅ All plots generated successfully!")
    print("   📁 Location: experiments/")
    print("   - plot1_compression_tradeoff.png")
    print("   - plot2_cache_efficiency.png")
    print("   - plot3_config_comparison.png\n")

if __name__ == "__main__":
    main()
