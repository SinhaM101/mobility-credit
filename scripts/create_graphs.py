"""
Generate Matplotlib Graphs for Income vs Voting Analysis
NYC Borough-Level Analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Load the merged analysis data
df = pd.read_csv("nyc_income_voting_analysis.csv")

# Sort by median income for consistent ordering
df = df.sort_values('median_household_income', ascending=True)

# Set up the figure with multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle('Income Inequality vs Voting Patterns in NYC (2024)', fontsize=16, fontweight='bold')

# Color scheme
dem_color = '#3498db'  # Blue for Democratic
rep_color = '#e74c3c'  # Red for Republican
income_color = '#2ecc71'  # Green for income
poverty_color = '#9b59b6'  # Purple for poverty

# =============================================================================
# CHART 1: Median Income by Borough (Horizontal Bar)
# =============================================================================
ax1 = axes[0, 0]
bars1 = ax1.barh(df['borough'], df['median_household_income'], color=income_color, edgecolor='black')
ax1.set_xlabel('Median Household Income ($)', fontsize=11)
ax1.set_title('Median Household Income by Borough', fontsize=12, fontweight='bold')
ax1.set_xlim(0, 120000)

# Add value labels
for bar, val in zip(bars1, df['median_household_income']):
    ax1.text(val + 2000, bar.get_y() + bar.get_height()/2, f'${val:,}', 
             va='center', fontsize=10)

# =============================================================================
# CHART 2: Democratic Margin by Borough (Horizontal Bar)
# =============================================================================
ax2 = axes[0, 1]
colors = [dem_color if x > 0 else rep_color for x in df['dem_margin']]
bars2 = ax2.barh(df['borough'], df['dem_margin'], color=colors, edgecolor='black')
ax2.axvline(x=0, color='black', linewidth=1)
ax2.set_xlabel('Democratic Margin (%)', fontsize=11)
ax2.set_title('2024 Presidential Vote Margin by Borough', fontsize=12, fontweight='bold')
ax2.set_xlim(-40, 80)

# Add value labels
for bar, val in zip(bars2, df['dem_margin']):
    offset = 3 if val > 0 else -8
    ax2.text(val + offset, bar.get_y() + bar.get_height()/2, f'{val:+.1f}%', 
             va='center', fontsize=10)

# Legend
dem_patch = mpatches.Patch(color=dem_color, label='Democratic Lead')
rep_patch = mpatches.Patch(color=rep_color, label='Republican Lead')
ax2.legend(handles=[dem_patch, rep_patch], loc='lower right')

# =============================================================================
# CHART 3: Income vs Democratic Margin (Scatter Plot)
# =============================================================================
ax3 = axes[1, 0]
scatter = ax3.scatter(df['median_household_income'], df['dem_margin'], 
                      s=df['population']/10000, c=df['poverty_rate'], 
                      cmap='RdYlGn_r', edgecolors='black', alpha=0.8)

# Add borough labels
for _, row in df.iterrows():
    ax3.annotate(row['borough'], (row['median_household_income'], row['dem_margin']),
                 xytext=(5, 5), textcoords='offset points', fontsize=10)

ax3.set_xlabel('Median Household Income ($)', fontsize=11)
ax3.set_ylabel('Democratic Margin (%)', fontsize=11)
ax3.set_title('Income vs Voting Pattern\n(Size = Population, Color = Poverty Rate)', 
              fontsize=12, fontweight='bold')
ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

# Colorbar
cbar = plt.colorbar(scatter, ax=ax3)
cbar.set_label('Poverty Rate (%)')

# =============================================================================
# CHART 4: Multi-metric Comparison (Grouped Bar)
# =============================================================================
ax4 = axes[1, 1]

# Normalize metrics for comparison (0-100 scale)
df_norm = df.copy()
df_norm['income_norm'] = df['median_household_income'] / 1000  # Scale to ~40-100
df_norm['dem_margin_norm'] = df['dem_margin'] + 30  # Shift to positive
df_norm['inequality_norm'] = df['income_inequality_ratio'] * 40  # Scale up

x = range(len(df))
width = 0.25

bars_income = ax4.bar([i - width for i in x], df_norm['income_norm'], width, 
                       label='Income (÷1000)', color=income_color, edgecolor='black')
bars_dem = ax4.bar(x, df_norm['dem_margin_norm'], width, 
                    label='Dem Margin (+30)', color=dem_color, edgecolor='black')
bars_ineq = ax4.bar([i + width for i in x], df_norm['inequality_norm'], width, 
                     label='Inequality (×40)', color='#f39c12', edgecolor='black')

ax4.set_xticks(x)
ax4.set_xticklabels(df['borough'], rotation=45, ha='right')
ax4.set_ylabel('Normalized Value', fontsize=11)
ax4.set_title('Multi-Metric Comparison by Borough', fontsize=12, fontweight='bold')
ax4.legend(loc='upper left')

# Adjust layout
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# Save the figure
plt.savefig('nyc_income_voting_graphs.png', dpi=150, bbox_inches='tight')
print("Saved: nyc_income_voting_graphs.png")

# Also create a summary table figure
fig2, ax = plt.subplots(figsize=(12, 4))
ax.axis('off')

# Create table data
table_data = []
for _, row in df.sort_values('median_household_income', ascending=False).iterrows():
    table_data.append([
        row['borough'],
        f"${row['median_household_income']:,}",
        f"{row['income_inequality_ratio']:.2f}",
        f"{row['poverty_rate']:.1f}%",
        f"{row['dem_margin']:+.1f}%",
        f"{row['bachelors_or_higher']:.1f}%"
    ])

columns = ['Borough', 'Median Income', 'Inequality Ratio', 'Poverty Rate', 
           'Dem Margin (2024)', 'Bachelor\'s+']

table = ax.table(cellText=table_data, colLabels=columns, loc='center',
                 cellLoc='center', colColours=['#3498db']*6)
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.8)

# Style header
for i in range(len(columns)):
    table[(0, i)].set_text_props(color='white', fontweight='bold')

ax.set_title('NYC Borough Economic & Voting Summary', fontsize=14, fontweight='bold', pad=20)

plt.savefig('nyc_summary_table.png', dpi=150, bbox_inches='tight', facecolor='white')
print("Saved: nyc_summary_table.png")

plt.show()
print("\nGraphs generated successfully!")
