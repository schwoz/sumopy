import os 
import numpy as np            
from collections import OrderedDict
#import  matplotlib as mpl 
#from matplotlib.patches import Arrow,Circle, Wedge, Polygon,FancyArrow
#from matplotlib.collections import PatchCollection
#import matplotlib.colors as colors
#import matplotlib.cm as cmx
#import matplotlib.pyplot as plt
#import matplotlib.image as image

from coremodules.misc.matplottools import *

import agilepy.lib_base.classman as cm
import agilepy.lib_base.arrayman as am
from agilepy.lib_base.geometry import *
from agilepy.lib_base.processes import Process

class Resultplotter(PlotoptionsMixin, Process):
    def __init__(self, results, name= 'Plot results with Matplotlib', 
                    info = "Creates plots of different results using matplotlib",  
                    logger = None, **kwargs):
        
        self._init_common('resultplotter', parent = results, name = name, 
                            info = info, logger = logger)
        
        #print 'Resultplotter.__init__',results,self.parent
        attrsman = self.get_attrsman()
        
        # edgeresultes....
        attrnames_edgeresults = OrderedDict()
        edgeresultattrconfigs = self.parent.edgeresults.get_group_attrs('results')
        edgeresultattrnames = edgeresultattrconfigs.keys()
        #edgeresultattrnames.sort()
        for attrname in edgeresultattrnames:
            attrconfig = edgeresultattrconfigs[attrname]
            
            attrnames_edgeresults[attrconfig.format_symbol()] = attrconfig.attrname
        
        #attrnames_edgeresults = {'Entered':'entered'}
        self.edgeattrname = attrsman.add(cm.AttrConf(  'edgeattrname', kwargs.get('edgeattrname','entered'),
                                        choices = attrnames_edgeresults,
                                        groupnames = ['options'], 
                                        name = 'Edge Quantity', 
                                        info = 'The edge related quantity to be plotted.',
                                        ))
        
        self.add_plotoptions(**kwargs)
        

    def show(self):
        #print 'show',self.edgeattrname
        #if self.axis  is None:
        axis = init_plot()
        if (self.edgeattrname is not  ""):
            resultattrconf = getattr(self.parent.edgeresults, self.edgeattrname)
            ids = self.parent.edgeresults.get_ids()
            title = resultattrconf.get_info()#+resultattrconf.format_unit(show_parentesis=True)#format_symbol()
            self.plot_results_on_map(axis, ids, resultattrconf[ids] , 
                                    title = title, 
                                    valuelabel = resultattrconf.format_symbol())
        
        
        show_plot()
    
        
                
    def do(self):
        #print 'do',self.edgeattrname
        self.show()

    def get_scenario(self):
        return self._scenario
        
        
        
class ElectricalEnergyResultsPlotter(PlotoptionsMixin,Process):
    def __init__(self, results, name= 'Electrical energy plotter', 
                    info = "Plot electrical energy results using matplotlib",  
                    logger = None, **kwargs):
        
        self._init_common('electricalenergyresultsplotter', parent = results, name = name, 
                            info = info, logger = logger)
        
        print 'ElectricalEnergyResultsPlotter.__init__',results,self.parent,len(self.get_eneryresults())
        attrsman = self.get_attrsman()
        
        
        self.add_plotoptions_lineplot(**kwargs)
        self.add_save_options(**kwargs)
        
        
        
       
        
    
    def get_eneryresults(self):
        return self.parent.electricenergy_vehicleresults
    
    def show(self):
        eneryresults = self.get_eneryresults()
        print 'show',eneryresults
        #print '  dir(vehicleman)',dir(vehicleman)
        
        print '  len(eneryresults)',len(eneryresults)
        if len(eneryresults)>0:
                plt.close("all")
                self.plot_power()
                
                
         
    
    
    def plot_power(self):
        print 'plot_power'
        eneryresults = self.get_eneryresults()
        
        times = eneryresults.times.get_value()
        if len(times) < 2: return
        ax = init_plot()
        
        dt = times[1]-times[0]
        times_scaled = (times-times[0])/60.0
        energies = eneryresults.energies.get_value()
        powers = energies/dt*3600.0 # W energy is in Wh
        powers_av = np.mean(powers)
        ax.plot(times_scaled,powers/1000.0,
                label = 'Power over time',
                color = self.color_line, 
                linestyle='-', linewidth = self.width_line, 
                #marker = 'o', markersize = self.size_marker, 
                alpha = self.alpha_results
                )
        ax.plot([times_scaled[0],times_scaled[-1]],[powers_av/1000.0, powers_av/1000.0],
                label = 'Average power = %.2fKW'%(powers_av/1000),
                color = 'r', 
                linestyle='-', linewidth = self.width_line+1.0, 
                #marker = 'o', markersize = self.size_marker, 
                )
        
       
                    
        ax.legend(loc='best',shadow=True, fontsize=self.size_labelfont)
        ax.grid(self.is_grid)
        if self.is_show_title:
            ax.set_title('Vehicle power over time', fontsize=self.size_titlefont)
        ax.set_xlabel('Time [min]', fontsize=self.size_labelfont)
        ax.set_ylabel('Power [KW]', fontsize=self.size_labelfont)
        ax.tick_params(axis='x', labelsize=int(0.8*self.size_labelfont))
        ax.tick_params(axis='y', labelsize=int(0.8*self.size_labelfont))
        
        # self.set_axisborder(ax)
        
        if self.is_save:
            plt.subplots_adjust(left=0.12, bottom=0.1, right=0.86, top=0.9, wspace=0.2, hspace=0.2)
            self.save_fig('power')
        else:
            show_plot()
