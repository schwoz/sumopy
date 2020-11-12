from os import system 
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import PolyCollection


from mpl_toolkits.axes_grid import make_axes_locatable

##############################################################################
# matplotlib configuration

linewidth=2.0
fontsize =12


params = {#'backend': 'ps',
          'axes.labelsize': fontsize,
          'text.fontsize': fontsize,
          'legend.fontsize': 0.9*fontsize,
          'xtick.labelsize': 0.9*fontsize,
          'ytick.labelsize': 0.9*fontsize,
          'text.usetex': False,
          #'figure.figsize': fig_size
          }

matplotlib.rcParams.update(params)

markers=['o','s','^','d','v','*','h','<','>']
markersize=8
nodesize=1000
##############################################################################
def init_plot(is_tight_layout = False):
    plt.close("all")
    fig = plt.figure()
    ax = fig.add_subplot(111)
    if is_tight_layout:
        fig.tight_layout()
    return ax

def save_fig(figname):
  #ffigname = figname+".png"
  #plt.savefig(ffigname,format='PNG')
  
  ffigname = figname+".pdf"
  plt.savefig(figname+".pdf",format='PDF')
  #plt.savefig(figname+".eps",format='eps',transparent=True)
  #system("ps2pdf -dEPSCrop "+figname+".eps "+figname+".pdf")
  #system("rm "+figname+".eps")
  return ffigname
