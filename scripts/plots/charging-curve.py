import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import (MINUTELY, RRuleLocator, rrulewrapper, DateFormatter)
from matplotlib.lines import Line2D
import pandas as pd  # to read csv, more convenient than csv module
import datetime


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
    return (fig_width_in, fig_height_in-2)  # the "-2" is added manually to reduce the height for MPT4.8-75(2-panels) case


# data
datadir = '../../data/charging/'
# panel = 'MPT4.8-75(4-panels)'  # possible values: MPT4.8-75(4-panels), MPT4.8-75(4-panels), MPT6-75(4-panels)
panel = 'MPT4.8-75(2-panels)'  # possible values: MPT4.8-75(4-panels), MPT4.8-75(4-panels), MPT6-75(4-panels)
# panel = 'MPT6-75(4-panels)'  # possible values: MPT4.8-75(4-panels), MPT4.8-75(4-panels), MPT6-75(4-panels)
datafile = datadir + panel + '.csv'
data = pd.read_csv(datafile)
data = data.astype({'Lux': 'Int64', 'Iin (mA)': 'Float64', 'Vin': 'Float64', 'Iout (mA)': 'Float64', 'Vout': 'Float64', 'Notes': 'string', 'Date': 'string', 'Time': 'string', 'Efficiency': 'float'})
datetime_arr = np.asarray([datetime.datetime.strptime(d, '%Y/%m/%d-%H:%M %Z') for d in np.asarray('2021/' + data.iloc[:,0] + '-' + data.iloc[:,1] + ' PST')])
lux_arr = np.asarray(data.get('Lux'))
Vin_arr = np.asarray(data.get('Vin'))
Vout_arr = np.asarray(data.get('Vout'))

# Remove the open circuit readings (for plotting current, efficiency)
trimmed_data = data.loc[data.get('Notes') != 'Open circuit']
trimmed_datetime_arr = np.asarray([datetime.datetime.strptime(d, '%Y/%m/%d-%H:%M %Z') for d in np.asarray('2021/' + trimmed_data.iloc[:,0] + '-' + trimmed_data.iloc[:,1] + ' PST')])
trimmed_lux_arr = np.asarray(trimmed_data.get('Lux'))
Iin_arr = np.asarray(trimmed_data.get('Iin (mA)'))
Iout_arr = np.asarray(trimmed_data.get('Iout (mA)'))
efficiency_arr = np.asarray(trimmed_data.get('Efficiency'))

print('Plotting data for {}'.format(panel))

## Plot Vout
if panel == 'MPT6-75(4-panels)':
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=set_size('ieee-textwidth', subplots=(1,2)))
    # limits
    ax1.set_ylim(3.25, 4.3)
    ax2.set_ylim(3.25, 4.3)
    # plot
    ax1.plot(datetime_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-14')], Vout_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-14')], color=default_blue, marker='o', linewidth=2)
    ax2.plot(datetime_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-15')], Vout_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-15')], color=default_blue, marker='o', linewidth=2)
    # show days on the top
    ax1.set_title('Day 1')
    ax2.set_title('Day 2')
    # ticks and grid
    ax1.xaxis.set_major_locator(RRuleLocator(rrulewrapper(MINUTELY, interval=5, dtstart=datetime_arr[0]+datetime.timedelta(minutes=5))))
    ax2.xaxis.set_major_locator(RRuleLocator(rrulewrapper(MINUTELY, interval=5, dtstart=datetime_arr[np.asarray([d.date() for d in datetime_arr]) == datetime.datetime.strptime('2021-01-15', '%Y-%m-%d').date()][0])))
    ax1.grid(b=True, which='major', axis='both')
    ax2.grid(b=True, which='major', axis='both')
    # tick formatting
    ax1.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax2.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    # remove spines between the two plots
    ax1.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    # axis labels
    ax1.set_ylabel('Volts', color=default_blue)
    ax1.tick_params(axis='y', labelcolor=default_blue)
    ax2.yaxis.set_ticklabels([])
    fig.subplots_adjust(wspace=0.02)
    ax1.yaxis.set_ticks_position('left')
    # Kinks in the time axis
    d = .015  # how big to make the diagonal lines in axes coordinates
    kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False)
    ax1.plot((1-d, 1+d), (-d, +d), **kwargs)        # top-left diagonal
    ax1.plot((1-d, 1+d), (1-d, 1+d), **kwargs)  # top-right diagonal
    kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
    ax2.plot((-d, +d), (1-d, 1+d), **kwargs)  # bottom-left diagonal
    ax2.plot((-d, +d), (-d, +d), **kwargs)  # bottom-right diagonal
else:
    fig, ax = plt.subplots(1, 1, figsize=set_size('ieee-textwidth'))
    ax.set_ylim(3.10, 4.3)
    if panel == 'MPT4.8-75(4-panels)':
        ax.plot(datetime_arr, Vout_arr, color=default_blue, marker='o', linewidth=2)
    elif panel == 'MPT4.8-75(2-panels)':
        ax.plot(datetime_arr[::2], Vout_arr[::2], color=default_blue, marker='o', linewidth=2)
    ax.xaxis.set_major_locator(RRuleLocator(rrulewrapper(MINUTELY, interval=5, dtstart=datetime_arr[0]+datetime.timedelta(minutes=5))))
    ax.grid(b=True, which='major', axis='both')
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.set_ylabel('Volts', color=default_blue)
    ax.tick_params(axis='y', labelcolor=default_blue)
    ax.yaxis.set_ticks_position('left')

## Plot sunlight intensity
if panel == 'MPT6-75(4-panels)':
    ax1 = ax1.twinx()
    ax2 = ax2.twinx()
    # limits
    ax1.set_ylim(min(lux_arr) - 15000, max(lux_arr) + 5000)
    ax2.set_ylim(min(lux_arr) - 15000, max(lux_arr) + 5000)
    # plot
    ax1.plot(datetime_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-14')], lux_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-14')], color=default_orange, marker='o', linestyle='--', markersize=4, linewidth=1)
    ax2.plot(datetime_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-15')], lux_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-15')], color=default_orange, marker='o', linestyle='--', markersize=4, linewidth=1)
    # tick formatting
    ax1.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax2.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    # remove spines between the two plots
    ax1.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    # axis labels
    ax1.yaxis.set_ticklabels([])
    ax1.yaxis.set_ticks([])
    ax2.yaxis.set_ticks_position('right')
    ax2.yaxis.set_ticklabels([])
    ax2.yaxis.set_ticks([])
    # show intensity as a text annotation near the point
    xoffset = datetime.timedelta(minutes=2.5)
    yoffset = 3000
    for datetimestamp, intensity in zip(datetime_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-14')], lux_arr[np.array([d.date() for d in datetime_arr]) == datetime.date.fromisoformat('2021-01-14')]):
        ax1.text(datetimestamp + xoffset, intensity + yoffset, intensity/1000, horizontalalignment='center', verticalalignment='center', color=default_orange, fontsize='small')
    for datetimestamp, intensity in zip(trimmed_datetime_arr[np.array([d.date() for d in trimmed_datetime_arr]) == datetime.date.fromisoformat('2021-01-15')], trimmed_lux_arr[np.array([d.date() for d in trimmed_datetime_arr]) == datetime.date.fromisoformat('2021-01-15')]):
        ax2.text(datetimestamp + xoffset, intensity + yoffset, intensity/1000, horizontalalignment='center', verticalalignment='center', color=default_orange, fontsize='small')
else:
    ax = ax.twinx()
    ax.set_ylim(min(lux_arr) - 5000, max(lux_arr) + 15000)
    if panel == 'MPT4.8-75(4-panels)':
        ax.plot(datetime_arr, lux_arr, color=default_orange, marker='o', linestyle='--', markersize=4, linewidth=1)
    if panel == 'MPT4.8-75(2-panels)':
        ax.plot(datetime_arr[2::2], lux_arr[2::2], color=default_orange, marker='o', linestyle='--', markersize=4, linewidth=1)
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.yaxis.set_ticklabels([])
    ax.yaxis.set_ticks([])
    ax.yaxis.set_ticks_position('right')
    # show intensity as a text annotation near the point
    if panel == 'MPT4.8-75(4-panels)':
        xoffset = datetime.timedelta(minutes=0)
        yoffset = 5000
        for datetimestamp, intensity in zip(datetime_arr, lux_arr):
            ax.text(datetimestamp + xoffset, intensity + yoffset, intensity/1000, horizontalalignment='center', verticalalignment='center', color=default_orange, fontsize='small')
    elif panel == 'MPT4.8-75(2-panels)':
        xoffset = datetime.timedelta(minutes=2.5)
        yoffsets = [9000, 9000, 6000, 6000, 6000, 5000, 4000, 6000, 6000, 6000, 6000, 6000, 7000, 6000, 8000, 8000, 8000, 8000, 6000, -3000]
        for datetimestamp, intensity in zip(datetime_arr[2::2], lux_arr[2::2]):
            ax.text(datetimestamp + xoffset, intensity - yoffsets.pop(0), intensity/1000, horizontalalignment='center', verticalalignment='center', color=default_orange, fontsize='x-small', fontweight='heavy', zorder=10)

## Plot current output from the charger (show that it follows light intensity trend)
if panel == 'MPT6-75(4-panels)':
    ax1 = ax1.twinx()
    ax2 = ax2.twinx()
    # limits
    ax1.set_ylim(min(Iout_arr) - 30, max(Iout_arr) + 50)
    ax2.set_ylim(min(Iout_arr) - 30, max(Iout_arr) + 50)
    # plot
    ax1.plot(trimmed_datetime_arr[np.array([d.date() for d in trimmed_datetime_arr]) == datetime.date.fromisoformat('2021-01-14')], Iout_arr[np.array([d.date() for d in trimmed_datetime_arr]) == datetime.date.fromisoformat('2021-01-14')], color=default_purple, marker='o', linestyle=':', linewidth=1, markersize=4, zorder=2)
    ax2.plot(trimmed_datetime_arr[np.array([d.date() for d in trimmed_datetime_arr]) == datetime.date.fromisoformat('2021-01-15')], Iout_arr[np.array([d.date() for d in trimmed_datetime_arr]) == datetime.date.fromisoformat('2021-01-15')], color=default_purple, marker='o', linestyle=':', linewidth=1, markersize=4, zorder=2)
    # tick formatting
    ax1.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax2.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    # remove spines between the two plots
    ax1.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    # axis labels
    ax2.set_ylabel('mA', color=default_purple)
    ax2.tick_params(axis='y', labelcolor=default_purple)
    ax1.yaxis.set_ticklabels([])
    ax1.yaxis.set_ticks([])
    ax2.yaxis.set_ticks_position('right')
else:
    ax = ax.twinx()
    ax.set_ylim(min(Iout_arr) - 5, max(Iout_arr) + 5)
    if panel == 'MPT4.8-75(4-panels)':
        ax.plot(trimmed_datetime_arr, Iout_arr, color=default_purple, marker='o', linestyle=':', linewidth=1, markersize=4, zorder=2)
    elif panel == 'MPT4.8-75(2-panels)':
        ax.plot(trimmed_datetime_arr[1::2], Iout_arr[1::2], color=default_purple, marker='o', linestyle=':', linewidth=1, markersize=4, zorder=2)
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.set_ylabel('mA', color=default_purple)
    ax.tick_params(axis='y', labelcolor=default_purple)
    ax.yaxis.set_ticks_position('right')

# legend
if panel == 'MPT6-75(4-panels)':
    ax1.legend([Line2D([0], [0], color=default_blue, marker='o', linewidth=2), Line2D([0], [0], color=default_orange, marker='o', linestyle='--', linewidth=1, markersize=4), Line2D([0], [0], color=default_purple, marker='o', linestyle=':', linewidth=1, markersize=4)], ['Battery voltage (V)', r'Light intensity ($\times10^3$ lux)', 'Charging current (mA)'], loc='lower left', bbox_to_anchor=(0.105, -0.01))
else:
    ax.legend([Line2D([0], [0], color=default_blue, marker='o', linewidth=2), Line2D([0], [0], color=default_orange, marker='o', linestyle='--', linewidth=1, markersize=4), Line2D([0], [0], color=default_purple, marker='o', linestyle=':', linewidth=1, markersize=4)], ['Battery voltage (V)', r'Light intensity ($\times10^3$ lux)', 'Charging current (mA)'], loc='upper left')
print('Average light intensity is: {}'.format(np.average(lux_arr)))
print('Maximum light intensity is: {}'.format(max(lux_arr)))
print('Average efficiency is: {}%'.format(100*np.average(efficiency_arr)))
# save plot
plt.savefig('../../img/charging-curve.eps', bbox_inches='tight')
print('Saved ../../img/charging-curve.eps')
plt.savefig('../../img/charging-curve.pdf', bbox_inches='tight')
print('Saved ../../img/charging-curve.pdf')
plt.savefig('../../img/charging-curve.png')
print('Saved ../../img/charging-curve.png')


# Efficiency plot
# Read efficiency data from all files
fig2 = plt.figure(2, figsize=set_size('ieee-columnwidth'))
ax2 = fig2.add_subplot(1,1,1)
efficiency_arr = []
lux_arr = []
for datafile in os.listdir(datadir):
    if os.path.isfile(datadir + datafile):
        data = pd.read_csv(datadir + datafile)
        data = data.astype({'Lux': 'Int64', 'Iin (mA)': 'Float64', 'Vin': 'Float64', 'Iout (mA)': 'Float64', 'Vout': 'Float64', 'Notes': 'string', 'Date': 'string', 'Time': 'string', 'Efficiency': 'float'})
        # Remove the open circuit readings (for plotting current, efficiency)
        trimmed_data = data.loc[data.get('Notes') != 'Open circuit']
        lux_arr.extend(list(trimmed_data.get('Lux')))
        efficiency_arr.extend(list(trimmed_data.get('Efficiency')))
efficiency_arr = np.asarray(efficiency_arr)
lux_arr = np.asarray(lux_arr)

ax2.plot(lux_arr, efficiency_arr, 'o', markersize=3)
ax2.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax2.set_xlabel('Light intensity (lux)')
ax2.set_ylabel('Efficiency')
ax2.grid()
ax2.set_ylim(0, 1)
#plt.subplots_adjust(bottom=0.18, left=0.18)

plt.savefig('../../img/efficiency.eps', bbox_inches='tight')
print('Saved ../../img/efficiency.eps')
plt.savefig('../../img/efficiency.pdf', bbox_inches='tight')
print('Saved ../../img/efficiency.pdf')
plt.savefig('../../img/efficiency.png')
print('Saved ../../img/efficiency.png')

# Average efficiency for indoor charge
for datafile in os.listdir(datadir + 'inside'):
    data = pd.read_csv(datadir + 'inside/' + datafile)
    data = data.astype({'Lux': 'Int64', 'Iin (mA)': 'Float64', 'Vin': 'Float64', 'Iout (mA)': 'Float64', 'Vout': 'Float64', 'Notes': 'string', 'Date': 'string', 'Time': 'string', 'Efficiency': 'float'})
    # Remove the open circuit readings (for plotting current, efficiency)
    trimmed_data = data.loc[data.get('Notes') != 'Open circuit']
    print("{}: avg efficiency is {}%".format(datadir+'inside/'+datafile, np.average(np.asarray(trimmed_data.get('Efficiency')))*100))
