import os 
import numpy as np    
import agilepy.lib_base.classman as cm
import agilepy.lib_base.arrayman as am
import  matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patche
from coremodules import demand
from coremodules.demand.origin_to_destination import OdIntervals
from coremodules.misc.matplottools import *
import agilepy.lib_base.xmlman as xm

from agilepy.lib_base.processes import Process


 
class OdPlots(PlotoptionsMixin,Process):
    def __init__(self, ident, demand, logger = None, **kwargs):
        print 'VpCreator.__init__'
        self._init_common(  ident, 
                            parent = demand,
                            name = 'Od plots', 
                            logger = logger,
                            info ='Plot od data.',
                            )      
        attrsman = self.set_attrsman(cm.Attrsman(self))
        
        self.is_plot_reallocation = attrsman.add(cm.AttrConf('is_plot_reallocation', kwargs.get('is_plot_reallocation',True),
                                        groupnames = ['options'], 
                                        name = 'Plot re-allocation', 
                                        info = 'Plot re-allocation.',
                                        )) 
        self.is_plot_trip_density = attrsman.add(cm.AttrConf('is_plot_trip_density', kwargs.get('is_plot_trip_density',True),
                                        groupnames = ['options'], 
                                        name = 'Plot trips density', 
                                        info = 'Plot rtrips density.',
                                        ))                          
        self.is_net = attrsman.add(cm.AttrConf('is_net', kwargs.get('is_net',True),
                                        groupnames = ['options'], 
                                        name = 'Plot net', 
                                        info = 'Plot net.',
                                        ))
        self.is_save = attrsman.add(cm.AttrConf('is_save', kwargs.get('is_save',False),
                                        groupnames = ['options'], 
                                        name = 'Save plots', 
                                        info = 'Save plots.',
                                        ))       
##        scenario = self.parent.get_scenario()
##        print scenario.demand.odintervals.get_ids()
        self.id_interval = attrsman.add(cm.AttrConf('id_interval', kwargs.get('interval',1),
                                        groupnames = ['options'], 
##                                        choices = scenario.demand.odintervals.ids,
                                        name = 'interval', 
                                        info = 'interval.',
                                        ))                                     
##        vtypes = scenario.demand.vtypes   

        self.id_odmode = attrsman.add(cm.AttrConf('id_odmode', kwargs.get('id_odmodes',1),
                                        groupnames = ['options'], 
                                        name = 'id_odmodes',
##                                        choices = vtypes.get_modechoices(),
                                        info = 'id_odmodes.',
                                        ))                                    
    def show(self):
        #print 'show',self.edgeattrname
        #if self.axis  is None:
        self.init_figures()
        
        # plt.rc('axes', prop_cycle=(cycler('color', ['r', 'g', 'b', 'y']) +
        #                    cycler('linestyle', ['-', '--', ':', '-.'])))
        if self.is_plot_reallocation:
                self.plot_reallocation_needs()
        if self.is_plot_trip_density:
                self.plot_trip_density()
             
        if not self.is_save:
            show_plot() 
            
    def plot_reallocation_needs(self, **kwargs):
        """
        Plot od data.
        """
        logger = self.get_logger()
        scenario = self.parent.get_scenario()
        zones = scenario.landuse.zones
        ids_zone = zones.get_ids()
        n_zones = len(ids_zone)

        od_matrix = scenario.demand.odintervals.get_od_matrix(self.id_interval, self.id_odmode,ids_zone)
        n_trip = np.sum(od_matrix[:,:])
        print 'n trip', n_trip
        generated = np.zeros(len(od_matrix[0,:]))
        attracted  = np.zeros(len(od_matrix[:,0])) 
        for zone_orig in range(len(od_matrix[0,:])):
            generated[zone_orig] = np.sum(od_matrix[zone_orig,:])
            attracted[zone_orig] = np.sum(od_matrix[:,zone_orig])
        re_allocates = attracted - generated 
        print generated, attracted, re_allocates
        
        zones = scenario.landuse.zones
        net = scenario.net
        print 'plot zone'
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ids_zone = zones.get_ids()
        for id_zone, re_allocate in zip(ids_zone, re_allocates):  
            zone_shape = zones.shapes[id_zone]
            verts = np.array(zone_shape)[:,:2].tolist()
            verts.append([0,0])
            codes = [Path.MOVETO]
            for i in range(len(verts)-2):
                codes.append(Path.LINETO)
            codes.append(Path.CLOSEPOLY)
            path = Path(verts, codes)
            
            
            if re_allocate < 0.:
                facecolor = 'brown'
            elif re_allocate > 0. and re_allocate < 200.:
                facecolor = 'red'
            elif re_allocate > 200. and re_allocate < 400.:
                facecolor = 'orangered'    
            elif re_allocate > 400. and re_allocate < 600.:
                facecolor = 'darkorange'   
            elif re_allocate > 600. and re_allocate < 800.:
                facecolor = 'yellow'     
            elif re_allocate > 800. and re_allocate < 1000.:
                facecolor = 'yellowgreen'
            else:
                facecolor = 'green'
            
            
##            
##            if re_allocate/(n_trip)*10000.0 < -1:
##                facecolor = 'coral'
##            elif re_allocate/(n_trip)*10000.0 > 1:
##                facecolor = 'lightyellow'
##            else:
##                facecolor = 'greenyellow'
                
            patch = patche.PathPatch(path, facecolor = facecolor, lw=4, alpha = 0.3)
            ax.add_patch(patch)
            
            text = re_allocate
            plt.text(zones.coords[id_zone][0],zones.coords[id_zone][1],"%d "%(text))
      
        if self.is_net:    
            print 'plot net'
            plot_net(ax, net, color_edge = "gray", width_edge = 2, color_node = None,
                alpha = 0.5)

        return True

    def plot_trip_density(self, **kwargs):
        """
        Plot od data.
        """
        logger = self.get_logger()
        scenario = self.parent.get_scenario()
        zones = scenario.landuse.zones
        ids_zone = zones.get_ids()
        n_zones = len(ids_zone)

        od_matrix = scenario.demand.odintervals.get_od_matrix(self.id_interval, self.id_odmode,ids_zone)
        n_trip = np.sum(od_matrix[:,:])
        print 'n trip', n_trip
        generated = np.zeros(len(od_matrix[0,:]))
        attracted  = np.zeros(len(od_matrix[:,0])) 
        for zone_orig in range(len(od_matrix[0,:])):
            generated[zone_orig] = np.sum(od_matrix[zone_orig,:])
            attracted[zone_orig] = np.sum(od_matrix[:,zone_orig])
        re_allocates = attracted - generated 
        print generated, attracted, re_allocates
        
        zones = scenario.landuse.zones
        net = scenario.net
        print 'plot zone'
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ids_zone = zones.get_ids()
        for id_zone, gener, attr in zip(ids_zone, generated, attracted):  
            zone_shape = zones.shapes[id_zone]
            verts = np.array(zone_shape)[:,:2].tolist()
            verts.append([0,0])
            codes = [Path.MOVETO]
            for i in range(len(verts)-2):
                codes.append(Path.LINETO)
            codes.append(Path.CLOSEPOLY)
            path = Path(verts, codes)
            movements = (gener + attr)/2.
            if movements < 5000.:
                facecolor = 'brown'
            elif movements > 5000. and movements < 10000.:
                facecolor = 'red'
            elif movements > 10000. and movements < 15000.:
                facecolor = 'orangered'    
            elif movements > 15000. and movements < 20000.:
                facecolor = 'darkorange'   
            elif movements > 20000. and movements < 25000.:
                facecolor = 'yellow'     
            elif movements > 25000. and movements < 30000.:
                facecolor = 'yellowgreen'
            else:
                facecolor = 'green'
                
            patch = patche.PathPatch(path, facecolor = facecolor, lw=4, alpha = 0.3)
            ax.add_patch(patch)
            
##            text = re_allocate/(n_trip)*10000.0
##            plt.text(zones.coords[id_zone][0],zones.coords[id_zone][1],"%d "%(text))
      
        if self.is_net:    
            print 'plot net'
            plot_net(ax, net, color_edge = "gray", width_edge = 2, color_node = None,
                alpha = 0.5)

        return True