import os
import re  # regular expressions
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import csv


# define colors
default_blue = '#1f77b4'
default_orange = '#ff7f0e'
default_purple = '#9467bd'

# Optional (but use consistent styles for all plots)
# plt.style.use('seaborn')

# According to the IEEE format
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Times"],
    "font.size": 10,
    "legend.fontsize": 8,  # verify
    "xtick.labelsize": 8,  # verify
    "ytick.labelsize": 8,  # verify
    "axes.labelsize": 10})


def set_size(width, fraction=1, subplots=(1, 1)):
    """Set figure dimensions to avoid scaling in LaTeX.
    Parameters
    ----------
    width: float or string
            Document width in points, or string of predined document type
    fraction: float, optional
            Fraction of the width which you wish the figure to occupy
    subplots: array-like, optional
            The number of rows and columns of subplots.
    Returns
    -------
    fig_dim: tuple
            Dimensions of figure in inches
    """
    if width == 'ieee-textwidth':
        width_pt = 516
    elif width == 'ieee-columnwidth':
        width_pt = 252
    else:
        width_pt = width
    # Width of figure (in pts)
    fig_width_pt = width_pt * fraction
    # Convert from pt to inches
    inches_per_pt = 1 / 72.27
    # Golden ratio to set aesthetic figure height
    # https://disq.us/p/2940ij3
    golden_ratio = (5**.5 - 1) / 2
    # Figure width in inches
    fig_width_in = fig_width_pt * inches_per_pt
    # Figure height in inches
    fig_height_in = fig_width_in * golden_ratio * (subplots[0] / subplots[1])
    return (fig_width_in, fig_height_in)


datadir = '../../data/discharging/'
# Get all files with discharge data
files = []
for fname in os.listdir(datadir):
    if re.match('^vbat_.*', fname) is not None:
        files.append(fname)

fig = plt.figure(1, figsize=set_size('ieee-columnwidth'))
ax = fig.add_subplot(1,1,1)

t = []  # handlers for the thrust plots so that the legend can be ordered
linestyles = ['dashdot', 'dotted', 'dashed', 'solid']
excluded = [15, 30, 50, 85]
ii = 0
for fname in files:
    isHover = re.match('vbat_.', fname).group(0)[-1] == 'h'
    with open(datadir + fname) as filehandle:
        time, voltage = [], []
        csv_reader = csv.reader(filehandle)
        for line in csv_reader:
            time.append(int(line[0]))
            voltage.append(float(line[1]))
    # Reset t=0 and bring units from microseconds to minutes
    t0 = time[0]
    for i in range(len(time)):
        time[i] -= t0
        time[i] /= (1000 * 60)
    if not isHover:
        thrust = int(re.search('_t-(\d*)_n-(\d*)\.csv', fname).group(1))
        label = 'Thrust = {}\%'.format(str(thrust))
        trial_no = int(re.search('_t-(\d*)_n-(\d*)\.csv', fname).group(2))
    else:
        trial_no = int(re.search('_h_n-(\d*)\.csv', fname).group(1))
        # average thrust for vbat_h_n-1.csv (without panels) was 61.3%
        # average thrust for vbat_h_n-2.csv (with two MPT4.8-75) was 70.8%
        if trial_no == 1:
            label = 'Hover (avg 61.3\%)'
        elif trial_no == 2:
            label = 'Hover (avg 70.8\%, with panels)'
            print('Hover flight time with two MPT4.8-75 was {} min'.format(time[-1]))
    if isHover or thrust not in excluded:
        t.append(ax.plot(time, voltage, label=label, linewidth=1, linestyle=linestyles[ii]))
        ii += 1
ax.legend(handles=[t[0][0], t[3][0], t[1][0], t[2][0]], loc='center', ncol=len(ax.lines)//2, bbox_to_anchor=(0.41,1.15))
ax.grid()
ax.set_ylabel('Battery level (V)')
ax.set_xlabel('Time (min)')
plt.savefig('../../img/discharging-curves.eps', bbox_inches='tight')
print('Saved ../../img/discharging-curves.eps')
plt.savefig('../../img/discharging-curves.pdf', bbox_inches='tight')
print('Saved ../../img/discharging-curves.pdf')
plt.savefig('../../img/discharging-curves.png', bbox_inches='tight')
print('Saved ../../img/discharging-curves.png')
