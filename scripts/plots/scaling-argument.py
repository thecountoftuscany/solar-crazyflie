import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


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

# read data, everything has been calculated in the spreadsheet
data = pd.read_excel("../../data/drone-data.ods", engine="odf", sheet_name="data")
name = np.asarray(data.get("name"))
m = np.asarray(data.get("m (g)"))
l = np.asarray(data.get("l (m)"))
e = np.asarray(data.get("e (J)"))
t = np.asarray(data.get("t (s)"))
p = np.asarray(data.get("p (W)"))
l_a = np.asarray(data.get("l_a (m)"))
eta_p= np.asarray(data.get("eta_p"))
print(data)

m_log = np.logspace(-1, 4.5, 100) # g
# next, find best fit for two quantities: 
# rho [g/m3]: density of robot  (which determines power needed using robot's characteristic length). assumes robot is a cube. air is ~1000
# gamma [g/m2]: that solves the relation m = gamma * la**2, which is how many grams can be hovered per square meter array 
# The power used to hover per unit mass is rho_p [W/g], which we assume is constant: 
# P [W] = rho_p * m
# equating solar power and flight power: 
# rho_a * la**2 = rho_p * m = rho_p * rho * l**3 
# this gives gamma = rho_a/rho_p [W/m2/(W/g)=g/m2]
# 1. find rho, where we assume it has the form m = rho * l**3 . fit it in a least squares sense    
rho_est = np.exp(np.sqrt(np.mean((np.log(m) - np.log(l**3))**2)))  # density [g/m3] of device assuming its shape is a cube 
# 2. find gamma, where we assume it has the form m = gamma * l**2 . fit it in a least squares sense
gamma_est = np.exp(np.sqrt(np.mean((np.log(m) - np.log(l_a**2))**2)))  # [g/m2]
# print((rho_est, gamma_est))
l_predicted = (m_log/rho_est)**(1/3.)
la_predicted = (m_log/gamma_est)**(1/2.)

# calculate power efficiency of robofly-expanded with perfect charge recover
# robofly_expanded at 510 mg lift, 230 mW is 22 mN/W no recovery, 
# jumps up to 45 mN/W with perfect charge recovery
# print(510e-6*9.81/(.230*25/45)) # multipllied by approximate efficiency factor for recovery

fig = plt.figure(1, figsize=set_size('ieee-columnwidth'))
ax1 = plt.gca()

# Best fit line for mass vs length
plt.loglog(m_log, l_predicted, color=default_orange, linewidth=2, label='Aircraft size')

# Best fit line for mass vs solar panel length
plt.loglog(m_log, la_predicted, default_blue, linewidth=2, label='PV cell size')
ax1.set_xlabel('aircraft mass $m$ (g)')
ax1.set_ylabel(r'characteristic length $\ell$ (m)')
ax1.legend()

# Print the point (length, metres) where the best fit lines for
# predicted characteristic length and predicted solar panel length meet
print("Best fit lines meet at: {} mm".format(1000*np.min(np.abs(l_predicted - la_predicted))))

# mass vs length
plt.loglog(m, l, 'x', color=default_orange, markersize=8, markeredgewidth=2)
plt.grid(True, which='major')
plt.ylim(.01, 10)
ax2 = ax1.twinx()

# mass vs solar panel length
ax2.loglog(m, l_a, '.', color=default_blue, markersize=12, markeredgewidth=2, markeredgecolor=default_blue)
ax2.set_yticks([])
ax2.set_ylim(.01, 10)
plt.xlim(10**-1, 10**4)
plt.tight_layout()

# labels for the drones
# robofly-expanded, nanohummingbird, crazyflie2, parrof anafi, asctechummingbird, asctecfirefly, altura zenith
xpose_offsets = np.array((0, 0, 8, 0, 8, 0, -3000))
yposes = [0.2, 0.8, 0.05, 0.13, 3, 0.08, 0.2]
for mass, name_txt, xpose_offset, ypos, l in zip(m, name, xpose_offsets, yposes, l_a):
    ax1.text(mass + xpose_offset, ypos, name_txt, horizontalalignment='center', verticalalignment='center', fontsize='xx-small')
    ax1.arrow(mass, ypos, 0, l-ypos, color='gray', linestyle='dotted')
# ax1.text(0.5, 0.1, 'robofly expanded', horizontalalignment='center', verticalalignment='center', fontsize='xx-small')

plt.savefig('../../img/mass_vs_array_scaling2.pdf', dpi=300, bbox_inches='tight')
print('Saved ../../img/mass_vs_array_scaling2.pdf')
plt.savefig('../../img/mass_vs_array_scaling2.eps', dpi=300, bbox_inches='tight')
print('Saved ../../img/mass_vs_array_scaling2.eps')
plt.savefig('../../img/mass_vs_array_scaling2.png', dpi=300, bbox_inches='tight')
print('Saved ../../img/mass_vs_array_scaling2.png')
