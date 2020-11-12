
import os, sys, string, types
from xml.sax import saxutils, parse, handler#, make_parser
from collections import OrderedDict
import numpy as np            



from coremodules.modules_common import *

import agilepy.lib_base.classman as cm
import agilepy.lib_base.arrayman as am
import agilepy.lib_base.xmlman as xm
from agilepy.lib_base.geometry import *

from agilepy.lib_base.processes import Process,CmlMixin,ff,call,P
from coremodules.network.network import SumoIdsConf

    
def load_results(filepath, parent = None, logger = None):
    # typically parent is the scenario
    results = cm.load_obj(filepath, parent=parent)
    if logger  is not None:
        results.set_logger(logger)
    return results


                       
class Tripresults(am.ArrayObjman):
    def __init__(self, ident, parent, trips, edges,# datapathkey = 'tripdatapath',
                             is_add_default=True,
                             name = 'Trip results', 
                             info = 'Table with simulation results for each trip made.',
                             **kwargs):
        
        self._init_objman(  ident = ident, 
                            parent = parent, # main results object
                            info = info, 
                            name = name, 
                            **kwargs)
        
        
        #self.add(cm.AttrConf(  'datapathkey',datapathkey,
        #                        groupnames = ['_private'], 
        #                        name = 'data pathkey',
        #                        info = "key of data path",
        #                        ))
                                
        self.add_col(am.IdsArrayConf( 'ids_trip', trips, 
                                            groupnames = ['state'], 
                                            is_index = True,
                                            name = 'ID trip', 
                                            info = 'ID of trip.',
                                            ))
        attrinfos = OrderedDict([\
                ('duration', {'name':'Duration', 'xmltag':'duration',    'unit':'s',     'default':0, 'info':'Trip duration','groupnames':['tripdata']}),
                ('depart',   {'name':'Dep. time', 'xmltag':'depart',   'unit':'s',     'default':0, 'info':'Departure time','groupnames':['tripdata'],'is_average' : True}),
                ('arrival',   {'name':'Arr. time', 'xmltag':'arrival',   'unit':'s',    'default':0, 'info':'Arrival time','groupnames':['tripdata'],'is_average' : True}),
                ('routeLength',   {'name':'Length','xmltag':'routeLength',    'unit':'m',    'default':0.0, 'info':'Route length','groupnames':['tripdata']}),
                ('departdelays',   {'name':'Dep. delay', 'xmltag':'departDelay',   'unit':'s',    'default':0, 'info':'The time the vehicle had to wait before it could start his journey','groupnames':['tripdata'],'is_average' : True}),
                ('waittimes',   {'name':'Wait time', 'xmltag':'waitingTime',   'unit':'s',    'default':0, 'info':'The time in which the vehicle speed was below 0.1m/s (scheduled stops do not count) ','groupnames':['tripdata'],'is_average' : True}),
                ('stoptimes',   {'name':'Stop time', 'xmltag':'stopTime',   'unit':'s',    'default':0, 'info':'The time in which the vehicle was taking a planned stop','groupnames':['tripdata'],'is_average' : True}),
                ('timelosses',   {'name':'Timeloss', 'xmltag':'timeLoss',   'unit':'s',    'default':0, 'info':'The time lost due to driving below the ideal speed. (ideal speed includes the individual speedFactor; slowdowns due to intersections etc. will incur timeLoss, scheduled stops do not count)','groupnames':['tripdata'],'is_average' : True}),
                ('departPos',   {'name':'depart pos', 'xmltag':'departPos',   'unit':'m',    'default':0.0, 'info':'depart position','groupnames':['tripdata'],'is_average' : True}),
                ('arrivalPos',   {'name':'arrival pos','xmltag':'arrivalPos',    'unit':'m',    'default':0.0, 'info':'arrival position','groupnames':['tripdata'],'is_average' : True}),
                ('speedfactors',   {'name':'Speedfactor', 'xmltag':'speedFactor',    'default':0.0, 'info':'The individual speed factor of the vehicle (possibly drawn from a speed distribution at the start of the simulation)','groupnames':['tripdata'],}),
                ('are_vaporized',   {'name':'vaporized', 'xmltag':'vaporized',    'default':False, 'info':'Whether the vehicle was removed from the simulation before reaching its destination','groupnames':['tripdata'],}),
                ('waitSteps',   {'name':'wait steps', 'xmltag':'waitingCount',   'unit':None,    'default':0, 'info':'Count of time steps, the vehicle has been waiting during its trip','groupnames':['tripdata']}),
                ('rerouteNo',   {'name':'reroute No', 'xmltag':'rerouteNo',   'unit':None,    'default':0, 'info':'Number of re-routes','groupnames':['tripdata']}),
                ('waitSteps',   {'name':'wait steps', 'xmltag':'waitSteps',   'unit':None,    'default':0, 'info':'Time steps, the vehicle has been waiting during its trip','groupnames':['tripdata']}),
                ('consumptions', {'name':'Consumption', 'xmltag':'Consum',    'unit':'Ws',     'default':0.0, 'info':'Electrical energy consumption','groupnames':['electricenergydata']}),
                #('speeds_av',   {'name':'Average speeds', 'xmltag':'speed',   'unit':'m/s',     'default':0, 'info':'Average speed','groupnames':['tripdata'],'is_average' : True}),
                ])
                
        for attrname, kwargs in attrinfos.iteritems():
            self.add_resultattr(attrname, **kwargs)
        
        # this is special for route info
        self.add_col(am.IdlistsArrayConf( 'ids_edges', edges,
                                            name = 'Edge IDs', 
                                            groupnames = ['routeinfo'],
                                            info = 'List of edge IDs constituting the actually taken route.', 
                                            xmltag = 'edges',  
                                            ))  
    def get_trips(self):
        return self.ids_trip.get_linktab()
                                                        
    def add_resultattr(self, attrname, **kwargs):
        
        # default cannot be kwarg
        default =  kwargs['default']
        del kwargs['default']
        if kwargs.has_key('groupnames'):
            kwargs['groupnames'].append('results')
        else:
            kwargs['groupnames'] = ['results']
        
        self.add_col(am.ArrayConf(  attrname, default,**kwargs))
    
    #def import_routesdata(self, filepath):
    #    # TODO
    #    pass
    
    #def import_tripdata(self, filepath):
    #    #print 'import_tripdata',filepath,self.get_group('tripdata')
    #    self.import_sumoxml(filepath,self.get_group('tripdata'))
    
    def import_xml(self,sumo, datapaths):
        print 'Tripresults.import_xml datapaths',datapaths
        datapathkey = 'tripdatapath'
        if datapaths.has_key(datapathkey):
            self.import_tripdata_sumoxml(datapaths[datapathkey],sumo)
        
        #datapathkey = 'electricenergypath'
        #if datapaths.has_key(datapathkey):
        #    self.import_electricenergy_sumoxml(datapaths[datapathkey],sumo)
        
    def import_electricenergy_sumoxml_broke(self,filepath,sumo):    
        element = 'vehicle'
        print 'Tripresults.import_electricenergy_sumoxml',self.get_trips().ident, element,filepath
        #id_type = 'edge',
        #reader = 'interval',
        attrconfigs = self.get_group('electricenergydata')
        #print 'import_sumoxml',element
        #id_type = 'edge',
        #reader = 'interval',
        ids_sumo, results, interval = read_interval2(\
                                            filepath,sumo,element, attrconfigs)
        #print '  ids_sumo',ids_sumo
        #print '  results.keys()',results.keys()
        #print '  results',results
        # create ids for all colums
        #if fileinfo['id_type']=='edge':
            
        # this procedure is necessary to create new result ids only
        # for edges that are not yet in the database
        ids_sumotrip = self.ids_trip.get_linktab().ids_sumo
        n=len(ids_sumo)
        #print '  n',n
        ind_range = np.arange(n, dtype=np.int32)
        ids = np.zeros(n, dtype=np.int32)
        for i in ind_range:
            id_trip = ids_sumotrip.get_id_from_index(ids_sumo[i])
            if self.ids_trip.has_index(id_trip):
                ids[i] =  self.ids_trip.get_id_from_index(id_edge)
            else:
                ids[i] =  self.add_row(ids_trip = id_edge)
                   
        #ids = self.add_row()# here the ids_sumo can be strings too
        #elif fileinfo['id_type']=='trip':
        #    ids = self.tripresults.add_rows_keyrecycle(keys = ids_sumo)#
        #print '  ids=',ids    
        
        
        for attrconfig in attrconfigs: 
            
            attrname = attrconfig.attrname
            
            default = attrconfig.get_default()
            if type(default) in (types.IntType, types.LongType):
                conversion = 'i'#int
                values_attr = np.zeros(n,int)
            elif type(default) in (types.FloatType,types.ComplexType):
                conversion = 'f'#float
                values_attr = np.zeros(n,float)
            else:
                conversion = 's'#str
                values_attr = np.zeros(n,obj)
            
            is_average = False
            if hasattr(attrconfig,'is_average'):
                is_average = attrconfig.is_average
            #print ' copy',attrname,'is_average',is_average
            # this is a tricky way to read the data stored in
            # dictionarie into array tructures as used in results
            # problem is that not all dictionaries have all ids    
            for i in ind_range:
                if is_average:
                    valcum, num = results[attrname].get(ids_sumo[i],(default,1))
                    val = valcum/float(num) # average over measurements!
                else:
                    val = results[attrname].get(ids_sumo[i],default)
                    
                if conversion=='i':
                    val=int(val)
                #else:
                #    values_attr[i]=val
                #print '   attrname',attrname,conversion,val,is_average,type(val)
                values_attr[i]=val

            #print '  attrname',attrname
            #print '  ids',type(ids),ids
            #print '  values_attr',type(values_attr),values_attr
            attrconfig.set(ids, values_attr)
                
    def import_tripdata_sumoxml(self,filepath,sumo):    
        element = 'tripinfo'
        print 'Tripresults.import_tripdata_sumoxml',self.get_trips().ident,'element', element,filepath
        #id_type = 'edge',
        #reader = 'interval',
        attrconfigs = self.get_group('tripdata')
        ids_raw, results  = read_tripresult(filepath,sumo, self.get_trips(), element, attrconfigs)
                                            

        #print '  ids_raw',ids_raw
        #print '  results.keys()',results.keys()
        #print '  results',results
            
        # this procedure is necessary to create new result ids only
        # for trips that are not yet in the database
        n=len(ids_raw)
        #print '  number of rows',n
        ind_range = np.arange(n, dtype=np.int32)
        ids = np.zeros(n, dtype=np.int32)
        for i in ind_range:
            
            
            id_trip = int(ids_raw[i])
            if self.ids_trip.has_index(id_trip):
                ids[i] =  self.ids_trip.get_id_from_index(id_trip)
            else:
                ids[i] =  self.add_row(ids_trip = id_trip)
                   
        
        for attrconfig in attrconfigs: 
            attrname = attrconfig.attrname
            default = attrconfig.get_default()
            if type(default) in (types.IntType, types.LongType):
                conversion = 'i'#int
                values_attr = np.zeros(n,int)
            elif type(default) in (types.FloatType,types.ComplexType):
                conversion = 'f'#float
                values_attr = np.zeros(n,dtype = np.float32)
            if type(default) in (types.BooleanType,):
                conversion = 'b'#str
                values_attr = np.zeros(n,dtype = np.bool)
            else:
                conversion = 's'#str
                values_attr = np.zeros(n,dtype = np.object)
            
            is_average = False
            if hasattr(attrconfig,'is_average'):
                is_average = attrconfig.is_average
            # this is a tricky way to read the data stored in
            # dictionarie into array tructures as used in results
            # problem is that not all dictionaries have all ids    
            for i in ind_range:
                #print '  check',ids_raw[i],results[attrname].get(ids_raw[i],'No data')
                if is_average:
                    valcum, num = results[attrname].get(ids_raw[i],(default,1))
                    val = valcum/float(num) # average!
                else:
                    val = results[attrname].get(ids_raw[i],default)
                    
                if conversion=='i':
                    val=int(val)
                else:
                    values_attr[i]=val
                #print '   ',i,ids[i],attrname,conversion,val,type(val),is_average
                values_attr[i]=val

            #print '  attrname',attrname
            #print '  ids',type(ids),ids
            #print '  values_attr',type(values_attr),values_attr
            attrconfig.set(ids, values_attr)
            
                                        
class Edgeresults(am.ArrayObjman):
    def __init__(self, parent, edges, is_add_default=True, **kwargs):
        
        self._init_objman(  ident='edgeresults', 
                            parent = parent, # main results object
                            name = 'Edge results', 
                            info = 'Table with simulation results for each network edge.', 
                            #xmltag = ('vtypes','vtype','ids_sumo'),
                            **kwargs)
                            
        self.add_col(am.IdsArrayConf( 'ids_edge', edges, 
                                            groupnames = ['state'], 
                                            is_index = True,
                                            name = 'ID edge', 
                                            info = 'ID of edge.',
                                            ))
        self._init_attributes()

        
    def _init_attributes(self):
        #print 'Edgeresults._init_attributes'
        #print '  ',self,id(self),hasattr(self,'import_marouterxml')
        
        
        attrinfos = OrderedDict([\
                ('entered',  {'name':'Entered',      'unit':None,    'default':0, 'info':'Entered number of vehicles','xmltag':'entered','groupnames':['edgedata']}),
                ('entered_est',{'name':'Entered est',                'default':0, 'info':'Estimated number of entered vehicles.','groupnames':['analysis'],}),
                ('left',     {'name':'Left',         'unit':None,    'default':0, 'info':'Left number of vehicles','xmltag':'left','groupnames':['edgedata']}),
                ('arrived',  {'name':'Arrived',      'unit':None,    'default':0, 'info':'Arrived number of vehicles','xmltag':'arrived','groupnames':['edgedata']}),
                ('departed', {'name':'Departed',     'unit':None,    'default':0, 'info':'Departed number of vehicles','xmltag':'departed','groupnames':['edgedata']}),
                ('traveltime',{'name':'Av. times',   'unit':'s',     'default':0.0, 'info':'Av. Travel times','xmltag':'traveltime','groupnames':['edgedata'], 'is_average' : True}),
                ('density',  {'name':'Av. Densities','unit':'veh/km','default':0.0, 'info':'Av. Density in vehicles of vehicles on this Edge/Lane','xmltag':'density','groupnames':['edgedata'], 'is_average' : True}),
                ('waitingTime',{'name':'Av. waits',  'unit':'s',     'default':0.0, 'info':'Av. Waiting times of vehicles on this Edge/Lane','xmltag':'waitingTime','groupnames':['edgedata'], 'is_average' : True}),
                ('speed',    {'name':'Av. speeds',   'unit':'m/s',   'default':0.0, 'info':'Av. velocity of vehicles on this Edge/Lane','xmltag':'speed','groupnames':['edgedata'], 'is_average' : True}),
                ('fuel_abs', {'name':'Abs. Fuel',    'unit':'ml',    'default':0.0, 'info':'Absolute fuel consumption of vehicles on this Edge/Lane','xmltag':'fuel_abs','groupnames':['edgeemissions']}),
                ('CO_abs',   {'name':'Abs. CO',      'unit':'mg',    'default':0.0, 'info':'Absolute CO emission of vehicles on this Edge/Lane','xmltag':'CO_abs','groupnames':['edgeemissions']}),
                ('CO2_abs',  {'name':'Abs. CO2',     'unit':'mg',    'default':0.0, 'info':'Absolute CO2 emission of vehicles on this Edge/Lane','xmltag':'CO2_abs','groupnames':['edgeemissions']}),
                ('NOx_abs',  {'name':'Abs. NOx',     'unit':'mg',    'default':0.0, 'info':'Absolute NOx emission of vehicles on this Edge/Lane','xmltag':'NOx_abs','groupnames':['edgeemissions']}),
                ('PMx_abs',  {'name':'Abs. PMx',     'unit':'mg',    'default':0.0, 'info':'Absolute PMx  emission (Particle matter, all sizes) of vehicles on this Edge/Lane','xmltag':'PMx_abs','groupnames':['edgeemissions']}),
                ('fuel_normed',{'name':'Specific fuel',       'unit':'l/km/h','default':0.0, 'info':'Specific fuel consumption of vehicles on this Edge/Lane','xmltag':'fuel_normed','groupnames':['edgeemissions'], 'is_average' : True}),
                ('CO_normed',{'name':'Specific CO',           'unit':'g/km/h','default':0.0, 'info':'Normalized CO emission of vehicles on this Edge/Lane','xmltag':'CO_normed','groupnames':['edgeemissions'], 'is_average' : True}),
                ('CO2_normed',{'name':'Specific CO2',         'unit':'g/km/h','default':0.0, 'info':'Normalized CO2 emission of vehicles on this Edge/Lane','xmltag':'CO2_normed','groupnames':['edgeemissions'], 'is_average' : True}),
                ('NOx_normed',{'name':'Specific NOx',         'unit':'g/km/h','default':0.0, 'info':'Normalized NOx emission of vehicles on this Edge/Lane','xmltag':'NOx_normed','groupnames':['edgeemissions'], 'is_average' : True}),
                ('PMx_normed',{'name':'Specific PMx',         'unit':'g/km/h','default':0.0, 'info':'Normalized PMx emission of vehicles on this Edge/Lane','xmltag':'PMx_normed','groupnames':['edgeemissions'], 'is_average' : True}),
                ('fuel_perVeh',{'name':'Fuel per veh.',       'unit':'ml/veh','default':0.0, 'info':'Absolute fuel consumption of vehicles on this Edge/Lane','xmltag':'fuel_perVeh','groupnames':['edgeemissions'], 'is_average' : True}),
                ('CO_perVeh',{'name':'CO per veh.',           'unit':'mg/veh','default':0.0, 'info':'CO emission per vehicle on this Edge/Lane','xmltag':'CO_perVeh','groupnames':['edgeemissions'], 'is_average' : True}),
                ('CO2_perVeh',{'name':'CO2 per veh.',         'unit':'mg/veh','default':0.0, 'info':'CO2 emission per vehicle on this Edge/Lane','xmltag':'CO2_perVeh','groupnames':['edgeemissions'], 'is_average' : True}),
                ('NOx_perVeh',{'name':'NOx per veh.',         'unit':'mg/veh','default':0.0, 'info':'NOx emission per vehicle on this Edge/Lane','xmltag':'NOx_perVeh','groupnames':['edgeemissions'], 'is_average' : True}),
                ('PMx_perVeh',{'name':'PMx per veh.',         'unit':'mg/veh','default':0.0, 'info':'PMx emission per vehicle on this Edge/Lane','xmltag':'PMx_perVeh','groupnames':['edgeemissions'], 'is_average' : True}),
                ('noise',    {'name':'Noise',         'unit':'dB',   'default':0.0, 'info':'Noise of vehicles on this Edge/Lane','xmltag':'noise','groupnames':['edgenoise'], 'is_average' : True}),
                #
                ])
        
      
        for attrname, kwargs in attrinfos.iteritems():
            self.add_resultattr(attrname, **kwargs)
            
                                                     
    def add_resultattr(self, attrname, **kwargs):
        
        # default cannot be kwarg
        default =  kwargs['default']
        del kwargs['default']
        if kwargs.has_key('groupnames'):
            kwargs['groupnames'].append('results')
        else:
            kwargs['groupnames'] = ['results']
            
        self.add_col(am.ArrayConf(  attrname, default,**kwargs))
    
    def add_edgelength(self):
        edges = self.parent.get_scenario().net.edges
        self.add_col(am.ArrayConf(  'lengths',0.0,
                                    groupnames=[], 
                                    perm = 'r',
                                    unit = 'm', 
                                    name = 'Edge length',
                                    info = 'Edge length.'))
        ids = self.get_ids()
        self.lengths[ids] = edges.lengths[self.ids_edge[ids]]
        
    
    def add_entered_est(self, ids_edge, entered_vec):
        self.entered_est.reset()
        ids_results = np.zeros(len(ids_edge), dtype=np.int32)
        i = 0
        for id_edge, entered in zip(ids_edge, entered_vec):
            if self.ids_edge.has_index(id_edge):
                id_res = self.ids_edge.get_id_from_index(id_edge)
                self.entered_est[id_res] = entered
            else:
                id_res =  self.add_row(ids_edge = id_edge, entered_est = entered)
            ids_results[i] = id_res
            i += 1
            
        return ids_results
                                            
    def import_edgedata(self,sumo,  filepath):
        print 'import_edgedata',filepath
        #print '  group',self.get_group('edgedata')
        #attrnames_data = ['entered','left','arrived','departed']
        #attrnames_averaged = ['traveltime','density','waitingTime','speed',]
        self.import_sumoxml(filepath,sumo,  self.get_group('edgedata'))
    
    def import_edgenoise(self,sumo,  filepath):
        print 'import_edgenoise',filepath
        self.import_sumoxml(filepath,sumo, self.get_group('edgenoise'))
    
    
    def import_edgeemissions(self, sumo, filepath):
        print 'import_edgeemissions',filepath
        #attrnames_data = ['fuel_abs','CO_abs','CO2_abs','NOx_abs','PMx_abs']
        #attrnames_averaged = ['fuel_normed','CO_normed','CO2_normed',]
        self.import_sumoxml(filepath,sumo, self.get_group('edgeemissions'))
    
    
           
    def import_sumoxml(self,filepath,sumo, attrconfigs):    
        element = 'edge'
        #print 'import_sumoxml',element
        #id_type = 'edge',
        #reader = 'interval',
        ids_sumo, results, interval = read_interval2(\
                                            filepath,sumo,element, attrconfigs)
        #print '  ids_sumo',ids_sumo
        #print '  results.keys()',results.keys()
        #print '  results',results
        # create ids for all colums
        #if fileinfo['id_type']=='edge':
            
        # this procedure is necessary to create new result ids only
        # for edges that are not yet in the database
        ids_sumoedge = self.ids_edge.get_linktab().ids_sumo
        n=len(ids_sumo)
        #print '  n',n
        ind_range = np.arange(n, dtype=np.int32)
        ids = np.zeros(n, dtype=np.int32)
        for i in ind_range:
            id_edge = ids_sumoedge.get_id_from_index(ids_sumo[i])
            if self.ids_edge.has_index(id_edge):
                ids[i] =  self.ids_edge.get_id_from_index(id_edge)
            else:
                ids[i] =  self.add_row(ids_edge = id_edge)
                   
        #ids = self.add_row()# here the ids_sumo can be strings too
        #elif fileinfo['id_type']=='trip':
        #    ids = self.tripresults.add_rows_keyrecycle(keys = ids_sumo)#
        #print '  ids=',ids    
        
        
        for attrconfig in attrconfigs: 
            
            attrname = attrconfig.attrname
            
            default = attrconfig.get_default()
            if type(default) in (types.IntType, types.LongType):
                conversion = 'i'#int
                values_attr = np.zeros(n,int)
            elif type(default) in (types.FloatType,types.ComplexType):
                conversion = 'f'#float
                values_attr = np.zeros(n,float)
            else:
                conversion = 's'#str
                values_attr = np.zeros(n,obj)
            
            is_average = False
            if hasattr(attrconfig,'is_average'):
                is_average = attrconfig.is_average
            #print ' copy',attrname,'is_average',is_average
            # this is a tricky way to read the data stored in
            # dictionarie into array tructures as used in results
            # problem is that not all dictionaries have all ids    
            for i in ind_range:
                if is_average:
                    valcum, num = results[attrname].get(ids_sumo[i],(default,1))
                    val = valcum/float(num) # average over measurements!
                else:
                    val = results[attrname].get(ids_sumo[i],default)
                    
                if conversion=='i':
                    val=int(val)
                #else:
                #    values_attr[i]=val
                #print '   attrname',attrname,conversion,val,is_average,type(val)
                values_attr[i]=val

            #print '  attrname',attrname
            #print '  ids',type(ids),ids
            #print '  values_attr',type(values_attr),values_attr
            attrconfig.set(ids, values_attr)

    def import_marouterxml(self, filepath, marouter):
            
            if not self.has_attrname('entered_mar'):
                # add marouter result attributes
                # traveltime="14.01" speed="5.56" entered="0.00" flowCapacityRatio="0.00"/>        
                attrinfos = OrderedDict([\
                    ('entered_mar',  {  'name':'Entered Marouter',
                                        #'symbol':'F_{MA}',
                                        'unit':None,    
                                        'default':0, 
                                        'info':'Entered number of vehicles',
                                        'xmltag':'entered',
                                        'groupnames':['marouter']
                                        }),
                    ('speeds_mar',    { 'name':'Av. speeds Marouter',   
                                        'unit':'m/s',   
                                        'default':0.0, 
                                        'info':'Av. velocity of vehicles on this Edge',
                                        'xmltag':'speed',
                                        'groupnames':['marouter'],
                                        'is_average' : True
                                        }),
                    ('flow_capacity_ratios', {  'name':'Saturation', 
                                                'default':0.0, 
                                                'unit':'%',   
                                                'info':'Ratio between simulated flows and edge capacity determined by marouter.',
                                                'xmltag':'flowCapacityRatio',
                                                'groupnames':['marouter']
                                                }),
                    ])             
                        
                for attrname, kwargs in attrinfos.iteritems():
                    self.add_resultattr(attrname, **kwargs)
            
            attrconfigs = self.get_group('marouter')
            
            self.import_sumoxml(filepath, marouter, attrconfigs)
            
         
class ElectricEnergyVehicleResults(am.ArrayObjman):
    """Collects electric energy results for all vehicles with a battery device."""
    def __init__(self,  parent,  datapathkey = 'electricenergypath',
                             is_add_default=True,
                             name = 'Electric energy vehicle results', 
                             info = 'Table with electric energy consumption data for each vehicle with a battery device.',
                             **kwargs):
        
        self._init_objman(  ident = 'electricenergy_vehicleresults', 
                            parent = parent, # main results object
                            info = info, 
                            name = name, 
                            **kwargs)
        
        
        self.add(cm.AttrConf(  'datapathkey',datapathkey,
                                groupnames = ['_private'], 
                                name = 'data pathkey',
                                info = "key of data path",
                                ))
        
        self.add(cm.AttrConf(  'times',np.array([],dtype = np.float32),
                                groupnames = ['_private'], 
                                name = 'Times',
                                info = "Times steps for energy measurements",
                                ))
        
        self.add(cm.AttrConf(  'energies',np.array([],dtype = np.float32),
                                groupnames = ['_private'], 
                                name = 'Energies',
                                info = "Energy consumptions of all vehicled during each time step",
                                ))
                                
        self.add(cm.FuncConf(  'energy_total','on_energy_total', 0.0,
                                        groupnames = ['summary'], 
                                        name = 'Total energy consumption', 
                                        unit = 'KWh',
                                        info = 'Total electrical energy consumpton of all vehicles.',
                                        ))
        
        self.add_col(SumoIdsConf(   'vehicle', 
                                    #name ='SUMO vehicle ID',
                                    info = 'SUMO vehicle ID, as used in route files.',
                                    perm = 'r'))
                                

        attrinfos = OrderedDict([\
                ('consumptions', {'name':'Consumption', 'xmltag':'energyConsumed',    'unit':'Ws',     'default':0.0, 'info':'Total electrical energy consumption.','groupnames':['electricenergydata']}),
                ('charges_station', {'name':'Charged at station', 'xmltag':'energyCharged',    'unit':'Ws',     'default':0.0, 'info':'Total electrical energy charged at charging stations.','groupnames':['electricenergydata']}),
                ('charges_av',   {'name':'Average charge', 'xmltag':'actualBatteryCapacity',   'unit':'Ws',     'default':0.0, 'info':'Average level of battery charge','groupnames':['electricenergydata'],'is_average' : True}),
                ('speeds_av',   {'name':'Average speeds', 'xmltag':'speed',   'unit':'m/s',     'default':0.0, 'info':'Average speed','groupnames':['electricenergydata'],'is_average' : True}),
                ])
                
        for attrname, kwargs in attrinfos.iteritems():
            self.add_resultattr(attrname, **kwargs)
        

    def on_energy_total(self):
        """Returns total energy consumption"""
        return np.sum(self.consumptions.get_value())/10.0**3
                                                
    def add_resultattr(self, attrname, **kwargs):
        
        # default cannot be kwarg
        default =  kwargs['default']
        del kwargs['default']
        if kwargs.has_key('groupnames'):
            kwargs['groupnames'].append('results')
        else:
            kwargs['groupnames'] = ['results']
        
        self.add_col(am.ArrayConf(  attrname, default,**kwargs))
    
    #def import_routesdata(self, filepath):
    #    # TODO
    #    pass
    
    #def import_tripdata(self, filepath):
    #    #print 'import_tripdata',filepath,self.get_group('tripdata')
    #    self.import_sumoxml(filepath,self.get_group('tripdata'))
    
    def import_xml(self,sumo, datapaths):
        datapathkey = self.datapathkey.get_value()
        if datapaths.has_key(datapathkey):
            self.import_electricenergy_sumoxml(datapaths[datapathkey],sumo)
        
    def import_electricenergy_sumoxml(self,filepath,sumo):    
        element = 'vehicle'
        print 'ElectricEnergyresults.import_electricenergy_sumoxml',element,filepath
        #id_type = 'edge',
        #reader = 'interval',
        attrconfigs = self.get_group('electricenergydata')
        #print 'import_sumoxml',element
        #id_type = 'edge',
        #reader = 'interval',
        ids_sumo, results, interval, times, energies  = read_electrical_energy(\
                                            filepath,sumo,element, attrconfigs)
        
        self.times.set_value(times)
        self.energies.set_value(energies)
        
        print '  times=\n',self.times.get_value()
        print '  energies=\n',self.energies.get_value()
        
        #print '  ids_sumo',ids_sumo
        #print '  results.keys()',results.keys()
        #print '  results',results
        # create ids for all colums
        #if fileinfo['id_type']=='edge':
            
        # this procedure is necessary to create new result ids only
        # for edges that are not yet in the database
        #ids_sumotrip = self.ids_trip.get_linktab().ids_sumo
        n=len(ids_sumo)
        ids = self.add_rows(n=n, ids_sumo = ids_sumo)
        print '  n',n
        ind_range = np.arange(n, dtype=np.int32)
        
        #ids = np.zeros(n, dtype=np.int32)
        #for i in ind_range:
        #    id_trip = ids_sumotrip.get_id_from_index(ids_sumo[i])
        #    if self.ids_trip.has_index(id_trip):
        #        ids[i] =  self.ids_trip.get_id_from_index(id_edge)
        #    else:
        #        ids[i] =  self.add_row(ids_trip = id_edge)
                   
        #ids = self.add_row()# here the ids_sumo can be strings too
        #elif fileinfo['id_type']=='trip':
        #    ids = self.tripresults.add_rows_keyrecycle(keys = ids_sumo)#
        #print '  ids=',ids    
        
        
        for attrconfig in attrconfigs: 
            
            attrname = attrconfig.attrname
            
            default = attrconfig.get_default()
            if type(default) in (types.IntType, types.LongType):
                conversion = 'i'#int
                values_attr = np.zeros(n,int)
            elif type(default) in (types.FloatType,types.ComplexType):
                conversion = 'f'#float
                values_attr = np.zeros(n,float)
            else:
                conversion = 's'#str
                values_attr = np.zeros(n,obj)
            
            is_average = False
            if hasattr(attrconfig,'is_average'):
                is_average = attrconfig.is_average
            #print ' copy',attrname,'is_average',is_average
            # this is a tricky way to read the data stored in
            # dictionarie into array tructures as used in results
            # problem is that not all dictionaries have all ids    
            for i in ind_range:
                if is_average:
                    valcum, num = results[attrname].get(ids_sumo[i],(default,1))
                    val = valcum/float(num) # average over measurements!
                else:
                    val = results[attrname].get(ids_sumo[i],default)
                    
                if conversion=='i':
                    val=int(val)
                #else:
                #    values_attr[i]=val
                #print '   attrname',attrname,conversion,val,is_average,type(val)
                values_attr[i]=val

            #print '  attrname',attrname
            #print '  ids',type(ids),ids
            #print '  values_attr',type(values_attr),values_attr
            attrconfig.set(ids, values_attr)
                   
            
                                        
class Simresults(cm.BaseObjman):
        def __init__(self, ident= 'simresults', parent = None, 
                        name = 'Simulation results', 
                        info ='Results of SUMO simulation run.', 
                        outfile_prefix = 'out',
                        scenario = None,
                        **kwargs):
            
            # either scenario must be provided or 
            # parent must provide method get_scenario
            if scenario is None:
                scenario =  parent.get_scenario()            
            #print 'Network.__init__',name,kwargs
            rootname = scenario.get_rootfilename()
            rootdirpath = scenario.get_workdirpath()
        
            self._init_objman(ident= ident, parent=parent, name = name, 
                                info = info, **kwargs)
            attrsman = self.set_attrsman(cm.Attrsman(self))
            
            self._init_attributes()
        
        
        def _init_attributes(self):
            attrsman = self.get_attrsman()
            scenario = self.get_scenario()
            self.edgeresults = attrsman.add(cm.ObjConf( Edgeresults(self, scenario.net.edges),
                                                        groupnames = ['Edge results'],
                                                        ))
            
            # add trip results from all demand objects
            print 'Simresults._init_attributes'
            print '  scenario.demand.get_demandobjects()',scenario.demand.get_demandobjects()
            for demandobj in scenario.demand.get_demandobjects():
                demandobj.config_results(self)
                
            for simobj in self.parent.get_simobjects():
                simobj.config_simresults(self)
                
            self.electricenergy_vehicleresults = attrsman.add(cm.ObjConf( ElectricEnergyVehicleResults(self),
                                                        groupnames =['Results'],
                                                        ))
            
            
            
        
        def clear_results(self):
            for resultobj in self.get_attrsman().get_group('Results'):
                resultobj.clear()
            
        def get_resultobj(self, ident):
            #print 'get_resultobj',hasattr(self,ident)
            if hasattr(self,ident):
                return getattr(self,ident)
                
            else:
                return None
            
        def add_resultobj(self, resultobj, **kwargs):
            #print 'RESULTS:add_resultobj',resultobj.ident
            # attention: need to check whether already set
            # because setattr is set explicitely after add
            if  hasattr(self, resultobj.get_ident()):
                #self.get_attrsman().delete(resultobj.get_ident())
                getattr(self,resultobj.get_ident()).clear()
                
            if not hasattr(self, resultobj.get_ident()):
                if kwargs.has_key('groupnames'):
                    kwargs['groupnames'].append('Results')
                else:
                    kwargs['groupnames'] = ['Results']
                attrsman = self.get_attrsman()
                attrsman.add(cm.ObjConf(  resultobj, **kwargs)) 
                setattr(self,resultobj.get_ident(), resultobj)
            
            #for resultobj in self.get_attrsman().get_group_attrs('Results').values():
            #    print '  check resultobject',resultobj.get_ident_abs()
                
        
        #def import_xml(self, edgedatapath=None, edgenoisepath=None, edgeemissionspath = None, routesdatapath=None, tripdatapath=None):
        
        #def get_path(self, datapath):
        #    #edgedatapath=None, edgenoisepath=None, edgeemissionspath = None, routesdatapath=None, tripdatapath=None
             
        def import_xml(self, sumo, **datapaths):
            print 'Simresults.import_xml',self.get_ident_abs()
            print '  datapaths',datapaths
            ## import first all edge oriented results for the whole net
            if datapaths.has_key('edgedatapath'):
                self.edgeresults.import_edgedata(sumo, datapaths['edgedatapath'])
            
            if datapaths.has_key('edgenoisepath'):
                self.edgeresults.import_edgenoise(sumo,datapaths['edgenoisepath'])
                
            if datapaths.has_key('edgeemissionspath'):
                self.edgeresults.import_edgeemissions(sumo,datapaths['edgeemissionspath'])
            
            ## import all other resultobjects
            for resultobj in self.get_attrsman().get_group_attrs('Results').values():
                print '  import other resultobject',resultobj.ident
                resultobj.import_xml(sumo,datapaths)
                

        #def process(self, process = None):
        #    print 'Simresults.process'
        #    for demandobj in self.parent.demand.get_demandobjects():
        #        print '  process_results',demandobj
        #        demandobj.process_results(self, process)
            
        def get_tripresults(self):
            return self.get_attrsman().get_group_attrs('Trip results').values()
        
        
        #def import_routesdata(self, routesdatapath):
        #    for tripresult in self.get_tripresults():
        #        tripresult.import_routesdata(routesdatapath)
                
        #def import_tripdata(self, tripdatapath):
        #    for tripresult in self.get_tripresults():
        #        tripresult.import_tripdata(tripdatapath)
           
                
        def save(self, filepath = None, is_not_save_parent=True):
            if filepath  is None:
                self.get_scenario().get_rootfilepath()+'.res.obj'
            cm.save_obj(self, filepath, is_not_save_parent = is_not_save_parent)
                                              
        def get_scenario(self):
            return self.parent.parent
        

class MarouterLoadReader(handler.ContentHandler):
    """
    Reads edge based load results of Marouter.
       
    """

    def __init__(self, marouter, attrsconfigs_cumulative, attrsconfigs_average):
        self._marouter = marouter
        self._attrconfigs = attrconfigs
        self._element = 'edge'
        self._time_begin = None
        self._time_inter_begin = 0.0
        self._time_inter_end = 0.0
        self._time_tot = 0.0
        self._n_inter = 0
        self._values= {}
        self._ids = []
        
    def startElement(self, name, attrs):
        # <edge id="-120634989" traveltime="6.74" speed="13.89" entered="0.00" flowCapacityRatio="0.00"/>
        #if attrs.has_key('id'):
        #print 'startElement',name,name == self._element,self._element
        if name == 'interval':
            time_inter_begin = float(attrs['begin'])
            #print 79*'-'
            #print 'startElement  interval',self.is_inter_valid,' time_inter_begin',time_inter_begin,'is_valid',time_inter_begin >= self._sumo.time_warmup
            self.is_inter_valid = True
            time_inter_end = float(attrs['end'])
            
            self._time_inter = int(time_inter_end)-int(time_inter_begin)
            # here we just take the start and end time ofthe whole
            # measurement period
            if self._time_begin is None:# take very first time only
                self._time_begin = int(time_inter_begin)
            self._time_end = int(time_inter_end)
            self._time_tot += self._time_inter
            self._n_inter += 1
           
            
        if name == self._element:
            if not self.is_inter_valid: return # no interval initialized
            
            id_elem  = attrs.get('id', None)
            #print 'startElement  ---id_elem',id_elem
            if id_elem is None: return # id did not fit requested trip type
            
            
            if id_elem not in self._ids:
                self._ids.append(id_elem)
            
            # no arrival data availlable if trip has not been finished!!
            for attrsconfig in self._attrsconfigs_cumulative:
                xmltag = attrsconfig.xmltag
                attrname = attrsconfig.attrname
                
                if attrs.has_key(xmltag):
                    #print '  attrname cum',attrname,attrs.has_key(attrname),'*'+attrs[attrname]+'*'
                    a = attrs[xmltag]
                    
                    if a.strip()!='':
                        if self._values[attrname].has_key(id_elem):
                            self._values[attrname][id_elem] += float(a)
                            #print '    added val',xmltag,attrname,self._values[attrname][id_elem],'val',float(a)
                        else:
                            self._values[attrname][id_elem] = float(a)
                            #print '    set val',xmltag,attrname,self._values[attrname][id_elem],'val',float(a)
                        
                    #if (id in ('1/0to1/1','1/0to2/0')) & (attrname == 'entered'):
                    #    self.n_test+=int(attrs[attrname])
                    #    print '  -read ',id,attrname,attrs[attrname],self.n_test,self._values[attrname][id]
                    #    
                    #if (id in ('0/0to1/0')) & (attrname == 'left'):
                    #    self.n_test2+=int(attrs[attrname])
                    #    print '  +read ',id,attrname,attrs[attrname],self.n_test2,self._values[attrname][id]   
                        
            for attrsconfig in self._attrsconfigs_average:
                xmltag = attrsconfig.xmltag
                attrname = attrsconfig.attrname
                if attrs.has_key(xmltag):
                    #print '  attrname',attrname,attrs.has_key(attrname),'*'+attrs[attrname]+'*'
                    #n=float(self.n_inter)
                    a = attrs[xmltag]
                    if a.strip()!='':
                        if self._values[attrname].has_key(id_elem):
                            valcum, n = self._values[attrname][id_elem]
                            valcum += float(a)
                            n += 1
                            #self._values[attrname][id_elem] = ( (n-1)*self._values[attrname][id_elem] + float(a))/n
                            #self._values[attrname][id] += float(a)/self._time_inter
                            #self._n_values[attrname][id] += 1
                        else:
                            valcum = float(a)
                            n = 1
                            #self._values[attrname][id_elem] = float(a)
                            #self._values[attrname][id_elem] = float(a)/self._time_inter
                            #self._n_values[attrname][id] = 1
                        #print '    added cumval',xmltag,attrname,valcum,'val',float(a)
                        self._values[attrname][id_elem] = (valcum, n)
                                            


                
class IntervalAvReader2(handler.ContentHandler):
    """
    Reads edge or lane based intervals
    and returns time averaged values for each attribute name.
       
    """

    def __init__(self, element,sumo,  attrsconfigs_cumulative, attrsconfigs_average):
        """
        element is "lane" or "edge" or "tripinfo"
        attrnames is a list of attribute names to read.
        """
        print 'IntervalAvReader2',element
        #print '  attrsconfigs_cumulative'
        #for attrconfig in attrsconfigs_cumulative: print '    ',attrconfig.attrname
        
        #print '  attrsconfigs_average'
        #for attrconfig in attrsconfigs_average: print '    ',attrconfig.attrname
        self._element = element
        self._sumo = sumo # the sumo process generating the data
        self._time_start_recording = sumo.simtime_start + sumo.time_warmup
        self._attrsconfigs_cumulative = attrsconfigs_cumulative
        self._attrsconfigs_average = attrsconfigs_average
        self._time_begin = None
        self._time_end = None
        self._values= {}
        self._ids = []
        #self._n_values= {}
        self.is_inter_valid = False
        self.n_inter = 0
        self.n_test = 0
        self.n_test2 = 0
        
        # TODO: if we knew here all ids then we 
        # could create a numeric array per attribute
        # idea: pass ids as input arg
        for  attrsconfig in attrsconfigs_cumulative+attrsconfigs_average:
            self._values[attrsconfig.attrname]={}
            #print '  init',attrsconfig.attrname
            #self._n_values= {}
            
    
    def get_id_elem(self, attrs):
        """
        Returns the trip ID as integer if the desired trip type has been read.
        Otherwise -1 is returned. 
        """
        return attrs['id']
            
            
    def startElement(self, name, attrs):
        #if attrs.has_key('id'):
        #    print '  parse',name,self._element,name == self._element,self.is_inter_valid, 'id=',attrs.get('id','-')
        #print 'startElement',name,name == self._element,self._element
        
        #if name == 'timestep':
            
            
            
        if name == 'interval':
            time_inter_begin = float(attrs['begin'])
            #print 79*'-'
            #print 'startElement  interval',self.is_inter_valid,' time_inter_begin',time_inter_begin,'is_valid',time_inter_begin >= self._sumo.time_warmup
            if time_inter_begin >= self._time_start_recording:
                self.is_inter_valid = True
                time_inter_end = float(attrs['end'])
                
                self._time_inter = int(time_inter_end)-int(time_inter_begin)
                # here we just take the start and end time ofthe whole
                # measurement period
                if self._time_begin is None:# take very first time only
                    self._time_begin = int(time_inter_begin)
                self._time_end = int(time_inter_end)
                self.n_inter += 1
            else:
               self.is_inter_valid = False 
            
        if name == self._element:
            if not self.is_inter_valid: return # no interval initialized
            
            id_elem  = self.get_id_elem(attrs)
            #print 'startElement  ---id_elem',id_elem
            if id_elem == -1: return # id did not fit requested trip type
            
            
            if id_elem not in self._ids:
                self._ids.append(id_elem)
            
            # no arrival data availlable if trip has not been finished!!
            for attrsconfig in self._attrsconfigs_cumulative:
                xmltag = attrsconfig.xmltag
                attrname = attrsconfig.attrname
                
                if attrs.has_key(xmltag):
                    #print '  attrname cum',attrname,attrs.has_key(attrname),'*'+attrs[attrname]+'*'
                    a = attrs[xmltag]
                    
                    if a.strip()!='':
                        if self._values[attrname].has_key(id_elem):
                            self._values[attrname][id_elem] += float(a)
                            #print '    added val',xmltag,attrname,self._values[attrname][id_elem],'val',float(a)
                        else:
                            self._values[attrname][id_elem] = float(a)
                            #print '    set val',xmltag,attrname,self._values[attrname][id_elem],'val',float(a)
                        
                    #if (id in ('1/0to1/1','1/0to2/0')) & (attrname == 'entered'):
                    #    self.n_test+=int(attrs[attrname])
                    #    print '  -read ',id,attrname,attrs[attrname],self.n_test,self._values[attrname][id]
                    #    
                    #if (id in ('0/0to1/0')) & (attrname == 'left'):
                    #    self.n_test2+=int(attrs[attrname])
                    #    print '  +read ',id,attrname,attrs[attrname],self.n_test2,self._values[attrname][id]   
                        
            for attrsconfig in self._attrsconfigs_average:
                xmltag = attrsconfig.xmltag
                attrname = attrsconfig.attrname
                if attrs.has_key(xmltag):
                    #print '  attrname',attrname,attrs.has_key(attrname),'*'+attrs[attrname]+'*'
                    #n=float(self.n_inter)
                    a = attrs[xmltag]
                    if a.strip()!='':
                        if self._values[attrname].has_key(id_elem):
                            valcum, n = self._values[attrname][id_elem]
                            valcum += float(a)
                            n += 1
                            #self._values[attrname][id_elem] = ( (n-1)*self._values[attrname][id_elem] + float(a))/n
                            #self._values[attrname][id] += float(a)/self._time_inter
                            #self._n_values[attrname][id] += 1
                        else:
                            valcum = float(a)
                            n = 1
                            #self._values[attrname][id_elem] = float(a)
                            #self._values[attrname][id_elem] = float(a)/self._time_inter
                            #self._n_values[attrname][id] = 1
                        #print '    added cumval',xmltag,attrname,valcum,'val',float(a)
                        self._values[attrname][id_elem] = (valcum, n)

    def get_data(self):
        return self._values
    
    def get_interval(self):
        # returns time interval between first and last measurement
        return (self._time_begin,self._time_end)
        
    def get_ids(self):
        return self._ids


class ElectricalEnergyReader(IntervalAvReader2):
    """
    Reads intervals of the electrcal energy file and cumulates data.
    """
    def __init__(self, element,sumo,  attrsconfigs_cumulative, attrsconfigs_average):
        """
        element is "lane" or "edge" or "tripinfo"
        attrnames is a list of attribute names to read.
        """
        print 'ElectricalEnergyReader',element
        #print '  attrsconfigs_cumulative',attrsconfigs_cumulative
        #print '  attrsconfigs_average',attrsconfigs_average
        IntervalAvReader2.__init__(self, element,sumo,  attrsconfigs_cumulative, attrsconfigs_average)
        self.time_lastint = -1.0
        
        self.times = []
        self.energies = []
        self._energy_step = 0.0 # energy os all vehicles during last step
        self._consumptionsname = "consumptions"
    
    def startElement(self, name, attrs):
        #print 'startElement',name,name == self._element,'time_lastint', self.time_lastint,'is_inter_valid',self.is_inter_valid,'e=',self._energy_step
        
        if name == 'timestep':
            if self.time_lastint < 0:
                #print '  set time_lastint to ',float(attrs['time'])
                self.time_lastint = float(attrs['time'])
                self.is_inter_valid = False
            else:
                
                time_inter_begin = self.time_lastint
                #print 79*'-'
                #print '   time_inter_begin',time_inter_begin,'is_valid',time_inter_begin >= self._sumo.time_warmup
                if time_inter_begin >= self._sumo.time_warmup:
                    self.is_inter_valid = True
                    time_inter_end = float(attrs['time'])
                    self.times.append(time_inter_end)
                    self.energies.append(self._energy_step)
                    self._energy_step = 0.0
                    
                    self._time_inter = int(time_inter_end)-int(time_inter_begin)
                    # here we just take the start and end time ofthe whole
                    # measurement period
                    if self._time_begin is None:# take very first time only
                        self._time_begin = int(time_inter_begin)
                    self._time_end = int(time_inter_end)
                    self.n_inter += 1
                else:
                   self.is_inter_valid = False 
            
        if name == self._element:
            if not self.is_inter_valid: return # no interval initialized
            
            id_elem  = self.get_id_elem(attrs)
            #print '  ---id_veh_sumo',id_elem
            if id_elem == -1: return # id did not fit requested trip type
            
            
            if id_elem not in self._ids:
                self._ids.append(id_elem)
            
            for attrsconfig in self._attrsconfigs_cumulative:
                xmltag = attrsconfig.xmltag
                attrname = attrsconfig.attrname
                #print '    attrname (cum)',attrname,xmltag,attrs.has_key(xmltag)
                if attrs.has_key(xmltag):
                    
                    a = attrs[xmltag]
                    
                    if a.strip()!='':
                        a = float(a)
                        if self._values[attrname].has_key(id_elem):
                            self._values[attrname][id_elem] += a
                            #print '      added val',xmltag,attrname,self._values[attrname][id_elem],'val',float(a)
                        else:
                            self._values[attrname][id_elem] = a
                            #print '    set val',xmltag,attrname,self._values[attrname][id_elem],'val',float(a)
                            
                        if attrname == self._consumptionsname:
                            self._energy_step += a

            for attrsconfig in self._attrsconfigs_average:
                xmltag = attrsconfig.xmltag
                attrname = attrsconfig.attrname
                #print '    attrname (av)',attrname,xmltag,attrs.has_key(xmltag)
                if attrs.has_key(xmltag):
                    
                    a = attrs[xmltag]
                    if a.strip()!='':
                        a = float(a)
                        if self._values[attrname].has_key(id_elem):
                            valcum, n = self._values[attrname][id_elem]
                            #print '    add val', float(a),'to',valcum
                            valcum += a
                            n += 1
                        else:
                            valcum = a
                            n = 1
                            #print '    set val',valcum
                        #print '      added cumval',xmltag,attrname,valcum,'val',float(a)
                        self._values[attrname][id_elem] = (valcum, n)
                        
    def get_times(self):
            return np.array(self.times, dtype = np.float32) 
        
    def get_energies(self):
            return np.array(self.energies, dtype = np.float32) 
  
    
class TripresultReader(handler.ContentHandler):
    def __init__(self, trips, element, sumo, attrsconfigs_cumulative, attrsconfigs_average):
        """
        element is "lane" or "edge" or "tripinfo" or "personinfo"
        attrnames is a list of attribute names to read.
        
        """
        self._trips = trips
        #IntervalAvReader2.__init__(self, element,sumo,  attrsconfigs_cumulative, attrsconfigs_average)
        self._element = element
        self._sumo = sumo # the sumo process generating the data
        self._attrsconfigs_cumulative = attrsconfigs_cumulative
        self._attrsconfigs_average = attrsconfigs_average
        #self._time_begin = None
        #self._time_end = None
        self._values= {}
        self._ids = []
        #self._n_values= {}
        #self.is_inter_valid = False
        #self.n_inter = 0
        #self.n_test = 0
        #self.n_test2 = 0
        
        # TODO: if we knew here all ids then we 
        # could create a numeric array per attribute
        # idea: pass ids as input arg
        for  attrsconfig in attrsconfigs_cumulative+attrsconfigs_average:
            self._values[attrsconfig.attrname]={}
            #print '  init',attrsconfig.attrname
            #self._n_values= {}
            
    def get_id_elem(self, attrs):
        """
        Returns the trip ID as integer if the desired trip type has been read.
        Otherwise -1 is returned. 
        """
        print 'get_id_elem check id=',attrs['id'],self._trips,id(self._trips)
        return self._trips.get_id_from_id_sumo(attrs['id'])
    
    def startElement(self, name, attrs):
        if attrs.has_key('id'):
            print '  parse',name,self._element,name == self._element,'id=',attrs.get('id','-')
        
        
            
        if name == self._element:

            id_elem  = self.get_id_elem(attrs)
            print '  ---id_elem',id_elem
            if id_elem == -1: return # id did not fit requested trip type
            
            
            if id_elem not in self._ids:
                self._ids.append(id_elem)
            
            # no arrival data availlable if trip has not been finished!!
            for attrsconfig in self._attrsconfigs_cumulative:
                xmltag = attrsconfig.xmltag
                attrname = attrsconfig.attrname
                
                if attrs.has_key(xmltag):
                    print '  attrname',attrname,attrs.has_key(attrname)
                    if attrs.has_key(attrname):
                    
                        print '   val *'+attrs[xmltag]+'*'
                        a = attrs[xmltag]
                        
                        if a.strip()!='':
                            if self._values[attrname].has_key(id_elem):
                                self._values[attrname][id_elem] += float(a)
                            else:
                                self._values[attrname][id_elem] = float(a)
                            
                    #if (id in ('1/0to1/1','1/0to2/0')) & (attrname == 'entered'):
                    #    self.n_test+=int(attrs[attrname])
                    #    print '  -read ',id,attrname,attrs[attrname],self.n_test,self._values[attrname][id]
                    #    
                    #if (id in ('0/0to1/0')) & (attrname == 'left'):
                    #    self.n_test2+=int(attrs[attrname])
                    #    print '  +read ',id,attrname,attrs[attrname],self.n_test2,self._values[attrname][id]   
                        
            for attrsconfig in self._attrsconfigs_average:
                xmltag = attrsconfig.xmltag
                attrname = attrsconfig.attrname
                if attrs.has_key(xmltag):
                    #n=float(self.n_inter)
                    a = attrs[xmltag]
                    if a.strip()!='':
                        if self._values[attrname].has_key(id_elem):
                            valcum, n = self._values[attrname][id_elem]
                            valcum += float(a)
                            n += 1
                            #self._values[attrname][id_elem] = ( (n-1)*self._values[attrname][id_elem] + float(a))/n
                            #self._values[attrname][id] += float(a)/self._time_inter
                            #self._n_values[attrname][id] += 1
                        else:
                            valcum = float(a)
                            n = 1
                            #self._values[attrname][id_elem] = float(a)
                            #self._values[attrname][id_elem] = float(a)/self._time_inter
                            #self._n_values[attrname][id] = 1
                        self._values[attrname][id_elem] = (valcum, n)

    def get_data(self):
        return self._values
    

    def get_ids(self):
        return self._ids
   
def read_electrical_energy(filepath, sumo,  element, attrsconfigs):
    print 'read_electrical_energy'
    attrsconfigs_cumulative = []
    attrsconfigs_average = []
    for attrsconfig in attrsconfigs:
        #print '  check',attrsconfig.attrname
        if hasattr(attrsconfig,'is_average'):
            if attrsconfig.is_average:
                attrsconfigs_average.append(attrsconfig)
            else:
                attrsconfigs_cumulative.append(attrsconfig)
        else:
            attrsconfigs_cumulative.append(attrsconfig)
    
    
    reader = ElectricalEnergyReader(element,sumo,  attrsconfigs_cumulative, attrsconfigs_average)
    parse(filepath, reader)
    return reader.get_ids(), reader.get_data(),reader.get_interval(), reader.get_times(), reader.get_energies() 

                 
def read_interval2(filepath, sumo,  element, attrsconfigs):
    #print 'read_interval2'
    attrsconfigs_cumulative = []
    attrsconfigs_average = []
    for attrsconfig in attrsconfigs:
        #print '  check',attrsconfig.attrname
        if hasattr(attrsconfig,'is_average'):
            if attrsconfig.is_average:
                attrsconfigs_average.append(attrsconfig)
            else:
                attrsconfigs_cumulative.append(attrsconfig)
        else:
            attrsconfigs_cumulative.append(attrsconfig)
    
    
    reader = IntervalAvReader2(element,sumo,  attrsconfigs_cumulative, attrsconfigs_average)
    #parser = make_parser()
    #parser.setContentHandler(reader)
    #fn = '"'+filepath+'"'
    #print 'read_interval >'+fn+'<'
    #print '     >'+filepath+'<'
    #parser.parse(filepath)
    parse(filepath, reader)
    return reader.get_ids(), reader.get_data(),reader.get_interval()   


def read_tripresult(filepath,sumo,  trips, element, attrsconfigs):
    print 'read_tripresult',filepath,trips.ident,'element',element
    attrsconfigs_cumulative = []
    attrsconfigs_average = []
    for attrsconfig in attrsconfigs:
        #print '  check',attrsconfig.attrname
        if hasattr(attrsconfig,'is_average'):
            if attrsconfig.is_average:
                attrsconfigs_average.append(attrsconfig)
            else:
                attrsconfigs_cumulative.append(attrsconfig)
        else:
            attrsconfigs_cumulative.append(attrsconfig)
    
    
    reader = TripresultReader(trips, element,sumo,  attrsconfigs_cumulative, attrsconfigs_average)
    #parser = make_parser()
    #parser.setContentHandler(reader)
    #fn = '"'+filepath+'"'
    #print 'read_interval >'+fn+'<'
    #print '    start parse >'+filepath+'<'
    #parser.parse(filepath)
    parse(filepath, reader)
    #print '  end',len(reader._ids)
    return reader.get_ids(), reader.get_data()
