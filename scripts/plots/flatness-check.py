import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import MultipleLocator
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


# read position data
datafile = '../../data/flatness-check/pos.csv'
with open(datafile) as filehandle:
    time_pos, x, y, z, checking_flatness = [], [], [], [], []
    csv_reader = csv.reader(filehandle)
    for line in csv_reader:
        time_pos.append(int(line[0]))
        x.append(float(line[1]))
        y.append(float(line[2]))
        z.append(float(line[3]))
        checking_flatness.append(line[-1] == "True")
x = np.asarray(x)
y = np.asarray(y)
z = np.asarray(z)

# offsets to align plot with image
xoffset = 0.07  # old was 0.04
yoffset = 0.28  # old was 0.07
beginning, end = 0, -200

# settings for all plots
size = 2
zmin = 0.27
zmax = 0.36
zorder= 3
# colormaps, colors
z_map = 'viridis'
intensity_map = 'gray'
ao_color = 'red'

# Colored plot
fig1 = plt.figure(1, figsize=set_size('ieee-textwidth', subplots=(2,4), fraction=0.95))
ax1 = fig1.add_subplot(fig1.add_gridspec(2,4)[:,2:4])
imagefile = '../../img/fc_complete.jpg'
image = ndimage.rotate(plt.imread(imagefile), -90)
x0, y0 = -0.1, -0.35
x1, y1 = 1.65, 0.65
ax1.imshow(image, extent=[x0, x1, y0, y1])  # left, right, bottom, top
ax1.scatter(x[beginning:end]+xoffset, y[beginning:end]+yoffset, marker='.', s=size, c=z[beginning:end], vmin=zmin, vmax=zmax, zorder=zorder, cmap=z_map)  # trajectory
ax1.scatter(x[beginning]+xoffset, y[beginning]+yoffset, marker='1', c='red', s=40, zorder=4)  # start point
ax1.scatter(x[end]+xoffset, y[end]+yoffset, marker='v', c='green', s=40, zorder=4)  # end point
ax1.set_xticklabels([])
ax1.set_yticklabels([])
ax1.xaxis.set_major_locator(MultipleLocator(1))
ax1.yaxis.set_major_locator(MultipleLocator(1))
ax1.xaxis.set_minor_locator(MultipleLocator(0.1))
ax1.yaxis.set_minor_locator(MultipleLocator(0.1))
ax1.grid(b=True, which='major', color='#CCCCCC')
ax1.grid(b=True, which='minor', color='#CCCCCC', linestyle='--', linewidth=0.5)
ax1.set_axisbelow(True)
ax1.set_aspect('equal', 'box')

# read light intensity data
datafile = '../../data/flatness-check/intensity.csv'
with open(datafile) as filehandle:
    time_i, intensity = [], []
    csv_reader = csv.reader(filehandle)
    for line in csv_reader:
        if int(line[0]) >= time_pos[beginning] and int(line[0]) <= time_pos[end]:
            time_i.append(int(line[0]))
            intensity.append(float(line[1]))
time_i = np.asarray(time_i)
intensity = np.asarray(intensity)
x_adj, y_adj = np.zeros(len(time_i)), np.zeros(len(time_i))
for i in range(len(time_i)):
    x_adj[i] = x[np.argmin(np.abs(time_pos-time_i[i]))]
    y_adj[i] = y[np.argmin(np.abs(time_pos-time_i[i]))]

# light intensity
light_thresh = 1000  # lux
ax1.scatter(x_adj+xoffset, y_adj+yoffset, marker='s', s=8, c=intensity>light_thresh, zorder=2, cmap=intensity_map)

# read obstacle avoidance data
dist_thresh = 120  # mm
datafile = '../../data/flatness-check/range.csv'
with open(datafile) as filehandle:
    time_r, range_left, range_front, range_right, range_back = [], [], [], [], []
    csv_reader = csv.reader(filehandle)
    for line in csv_reader:
        if float(line[1]) < dist_thresh or float(line[2]) < dist_thresh or float(line[3]) < dist_thresh or float(line[4]) < dist_thresh:
            time_r.append(int(line[0]))
            range_left.append(float(line[1]))
            range_front.append(float(line[2]))
            range_right.append(float(line[3]))
            range_back.append(float(line[4]))
time_r = np.asarray(time_r)
range_left, range_front, range_right, range_back = np.asarray(range_left), np.asarray(range_front), np.asarray(range_right), np.asarray(range_back)
x_adj, y_adj = np.zeros(len(time_r)), np.zeros(len(time_r))
for i in range(len(time_r)):
    x_adj[i] = x[np.argmin(np.abs(time_pos-time_r[i]))]
    y_adj[i] = y[np.argmin(np.abs(time_pos-time_r[i]))]

# obstacle avoidance
ax1.scatter(x_adj+xoffset, y_adj+yoffset, marker='s', s=15, c=ao_color, zorder=1)

# Text annotations for recorded standard deviations
blocks = np.split(np.where(np.diff(checking_flatness))[0] + 1, 2)
xs, ys = [0.8, 1.25], [0.68, 0.68]  # coordinates for the annotations
colors = ['red', 'green']
for block in blocks:
    std = np.std(z[block[0]:block[1]])
    ax1.text(xs.pop(0), ys.pop(0), r"$\sigma$={:.1f} mm".format(std*1000), fontsize='small', zorder=10, color=colors.pop(0), fontweight='bold')


## Flatness check on various surfaces
datadir = '../../data/flatness-check/'
fnames = ['pos_flat.csv', 'pos_grass.csv', 'pos_gravel.csv', 'pos_tiles.csv']
imgfnames = ['fc_flat.jpg', 'fc_grass.jpg', 'fc_gravel.jpg', 'fc_tiles.jpg']
legends = ['Flat', 'Grass', 'Gravel', 'Tiles']
subplot_poses = [1, 2, 5, 6]
txt_poses = [[-0.09,0.16], [1.05,0.21], [-0.11,0.11], [-0.34,0.13]]  # x, y
extents = [[-0.25,0.15,-0.25,0.15], [0.9,1.3,-0.2,0.2], [-0.25,0.15,-0.3,0.1], [-0.48,-0.05,-0.3,0.12]]  # left, right, bottom, top
# read data
for fname, imgfname, legend, subplot_pose, extent, txt_pose in zip(fnames, imgfnames, legends, subplot_poses, extents, txt_poses):
    with open(datadir+fname) as filehandle:
        time, x, y, z, = [], [], [], []
        csv_reader = csv.reader(filehandle)
        for line in csv_reader:
            # if line[-1] == 'True':
            time.append(int(line[0]))
            x.append(float(line[1]))
            y.append(float(line[2]))
            z.append(float(line[3]))
        time = np.asarray(time)
        x = np.asarray(x)
        y = np.asarray(y)
        z = np.asarray(z)
        ax2 = fig1.add_subplot(2,4, subplot_pose)
        imagefile = '../../img/' + imgfname
        image = plt.imread(imagefile)
        ax2.imshow(image, extent=[extent[0], extent[1], extent[2], extent[3]])  # left, right, bottom, top
        ax2.scatter(x, y, s=3, c=z, vmin=zmin, vmax=zmax, zorder=zorder, cmap=z_map)
        ax2.scatter(x[0], y[0], marker='1', c='red', s=40, zorder=4)  # start point
        ax2.scatter(x[-1], y[-1], marker='v', c='green', s=40, zorder=4)  # end point
        ax2.set_xticklabels([])
        ax2.set_yticklabels([])
        ax2.xaxis.set_major_locator(MultipleLocator(1))
        ax2.yaxis.set_major_locator(MultipleLocator(1))
        ax2.xaxis.set_minor_locator(MultipleLocator(0.1))
        ax2.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax2.grid(b=True, which='major', color='#CCCCCC')
        ax2.grid(b=True, which='minor', color='#CCCCCC', linestyle='--', linewidth=0.5)
        ax2.set_axisbelow(True)
        ax2.set_aspect('equal', 'box')
        ax2.set_title(r"$\sigma$={:.1f} mm".format(np.std(z)*1000), fontsize='small', zorder=10, color="green", fontweight='bold')

cmap = matplotlib.cm.ScalarMappable(norm=plt.Normalize(vmin=zmin, vmax=zmin), cmap=z_map)
cmap.set_array([])
plt.subplots_adjust(left=0.02, right=0.87, top=0.98, bottom=0.02, wspace=0.01, hspace=0.35)
cbaxes = fig1.add_axes([0.9, 0.02, 0.02, 0.95])
cb = plt.colorbar(cmap, cax=cbaxes)
cb.set_label(r'Height (m)')
plt.legend([Line2D([0],[0],color='red',lw=0,marker='1',markersize=np.sqrt(40)), Line2D([0],[0],color='green',lw=0,marker='v',markersize=np.sqrt(40))], ['Start', 'Finish'], ncol=2, loc='center', bbox_to_anchor=[-12,-0.01])


plt.savefig('../../img/flatness-check-colored.eps', bbox_inches='tight')
print('Saved ../../img/flatness-check-colored.eps')
plt.savefig('../../img/flatness-check-colored.png', bbox_inches='tight')
print('Saved ../../img/flatness-check-colored.png')
plt.savefig('../../img/flatness-check-colored.pdf', bbox_inches='tight')
print('Saved ../../img/flatness-check-colored.pdf')
