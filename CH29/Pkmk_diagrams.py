# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 11:10:24 2025

@author: RArosio
"""

import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle


'''Chapter 29: Underwater Geomorphometry
    Lecours et al. 2026 
    In book: Geomorphometry - Concepts, Software, Applications
    Publisher: Elsevier'''
    
'''Python script to produce plots using "pkmk_des.csv", obtained from the analysis
    of pockmark features using the CoMMa Toolbox'''


##Load CSV file##
csv_file = '/pkmk_des.csv' ## <-- complete with directory name
df = pd.read_csv(csv_file)

###############################################################################

'''PLOT 1: Scatter Plot of pockmarks Area vs Relief (Conf_R) with zoom-in inset
            The pockmarks are subdivided in two groups (coloured blue and orange)
            based on their Polsby-Popper score (compactness). Regression lines 
            for the two groups are also shown'''

plt.figure(figsize=(12, 8), dpi=150)

##Zoom-in region coordinates##
x_zoom_min, x_zoom_max = 0, 1000000
y_zoom_min, y_zoom_max = 0, 20

##Pockmarks colour-coded on the base of PP_Score
high_pp_score = df[df['PP_Score'] >= 0.8]
low_pp_score = df[df['PP_Score'] < 0.8]

##Main scatter plot##
ax_main = plt.gca()
zoom_data_high = high_pp_score[(high_pp_score['Area'] >= x_zoom_min) & (high_pp_score['Area'] <= x_zoom_max) &
                                (high_pp_score['Conf_R'] >= y_zoom_min) & (high_pp_score['Conf_R'] <= y_zoom_max)]
zoom_data_low = low_pp_score[(low_pp_score['Area'] >= x_zoom_min) & (low_pp_score['Area'] <= x_zoom_max) &
                              (low_pp_score['Conf_R'] >= y_zoom_min) & (low_pp_score['Conf_R'] <= y_zoom_max)]

ax_main.scatter(zoom_data_high['Area'], zoom_data_high['Conf_R'], c='blue', label='PP_Score >= 0.8', alpha=0.8, edgecolor='k')
ax_main.scatter(zoom_data_low['Area'], zoom_data_low['Conf_R'], c='orange', label='PP_Score < 0.8', alpha=0.8, edgecolor='k')

##Regression lines##
for data, color, label in [(zoom_data_high, 'blue', 'High PP_Score'), (zoom_data_low, 'orange', 'Low PP_Score')]:
    if not data.empty:
        X = data['Area'].values.reshape(-1, 1)
        y = data['Conf_R'].values
        reg = LinearRegression().fit(X, y)
        y_pred = reg.predict(X)
        r2 = r2_score(y, y_pred)
        ax_main.plot(X, y_pred, color=color, label=f'{label} (R² = {r2:.2f})')

##Legend and labels##
ax_main.set_xlim(x_zoom_min, x_zoom_max)
ax_main.set_ylim(y_zoom_min, y_zoom_max)
ax_main.set_xlabel('Area', fontsize=14)
ax_main.set_ylabel('Relief', fontsize=14)
ax_main.grid(True, linestyle='--', alpha=0.6)
ax_main.legend(fontsize=12)

##Rectangle to highlight the zoom-in region##
rect_x, rect_y = x_zoom_min, y_zoom_min
rect_width, rect_height = x_zoom_max - x_zoom_min, y_zoom_max - y_zoom_min

##Zoomed-out inset##
ax_inset = plt.axes([0.65, 0.65, 0.3, 0.3])
ax_inset.scatter(df['Area'], df['Conf_R'], c='grey', alpha=0.4, edgecolor='k')
ax_inset.add_patch(Rectangle((rect_x, rect_y), rect_width, rect_height, 
                             linewidth=1.5, edgecolor='red', facecolor='none', linestyle='--'))
ax_inset.set_title('Full view', fontsize=10)
ax_inset.tick_params(axis='both', which='major', labelsize=8)
ax_inset.grid(True, linestyle='--', alpha=0.6)

plt.savefig('/pkmk_scaplot_relvsarea.jpg', format='jpg', 
            dpi=300, bbox_inches='tight') ## <-- complete with directory name
plt.show()


'''PLOT 2: Box Plot of pockmarks count by elongation (MBG_W_L)'''

plt.figure(figsize=(12, 7), dpi=120)
plt.boxplot([df[df['pit_no'] == x]['MBG_W_L'] for x in sorted(df['pit_no'].unique())],
            labels=sorted(df['pit_no'].unique()),
            patch_artist=True,
            boxprops=dict(facecolor='lightgreen', color='green'),
            medianprops=dict(color='red'))
plt.xlabel('pit_no', fontsize=12)
plt.ylabel('MBG_W_L', fontsize=12)
plt.title('MBG_W_L by pit_no', fontsize=14)
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()


'''PLOT 3: Box Plot of pockmarks count by Polsby-Popper (PP_score)'''

plt.figure(figsize=(12, 7), dpi=120)
pit_groups = df.groupby('pit_no')['PP_Score']
plt.boxplot([pit_groups.get_group(x) for x in pit_groups.groups], 
            labels=pit_groups.groups.keys(), patch_artist=True, 
            boxprops=dict(facecolor='lightblue', color='blue'), 
            medianprops=dict(color='red'))
plt.xlabel('No of pits (geomorphons)', fontsize=12)
plt.ylabel('PP score', fontsize=12)
plt.title('PP_score by pit_no', fontsize=14)
plt.xticks(rotation=45, fontsize=10) #rotation of the axis to make it more readable
plt.yticks(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.6)
#plt.savefig('/pkmk_des.csv', format='jpg', dpi=300, bbox_inches='tight') ## <-- complete with directory name
plt.show()


'''PLOT 4: Correlogram for selected variables'''

correlation_vars = ['Area', 'Perimeter', 'Conf_R', 'CH_Score', 'PP_Score', 
                    'MBG_Length', 'MBG_W_L', 'Depth_MEAN', 'pit_no'] #var selection
correlation_matrix = df[correlation_vars].corr()

fig, axes = plt.subplots(len(correlation_vars), len(correlation_vars), figsize=(18, 18), dpi=150)

for i, var1 in enumerate(correlation_vars):
    for j, var2 in enumerate(correlation_vars):
        ax = axes[i, j]

        if i == j:
            sns.histplot(df[var1], kde=True, ax=ax, color='dimgrey')
            ax.set_title(var1, fontsize=18)
            ax.set_ylabel('')
            ax.set_xlabel('')
        elif i > j:
            ##Below diagonal: heatmap cells
            value = correlation_matrix.loc[var1, var2]
            sns.heatmap([[value]], annot=True, cmap='coolwarm', vmin=-1, 
                        vmax=1, cbar=False, ax=ax, annot_kws={"fontsize": 18})
        else:
            ##Above diagonal: pie charts
            value = correlation_matrix.loc[var1, var2]
            wedge_sizes = [(1 + value) / 2, (1 - value) / 2]  # Normalize to 0-1
            ax.pie(wedge_sizes, colors=['dimgrey', 'lightgrey'], startangle=90)

        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        ax.set_xticks([])
        ax.set_yticks([])

##colorbar##
cbar_ax = fig.add_axes([0.92, 0.1, 0.02, 0.8])
sns.heatmap([[0]], cmap='coolwarm', cbar=True, 
            cbar_ax=cbar_ax, vmin=-1, vmax=1, annot=False)
cbar_ax.set_ylabel('Correlation', fontsize=20)
cbar_ax.set_xticks([])
cbar_ax.set_yticks([])

plt.tight_layout(rect=[0, 0, 0.9, 1])
plt.suptitle('Correlogram for selected variables', fontsize=24, y=1.02)
plt.savefig('/pkmk_correlogram_grey.jpg', format='jpg', 
            dpi=300, bbox_inches='tight') ## <-- complete with directory name
plt.show()