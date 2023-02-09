import os, string, sys
from collections import OrderedDict
import numpy as np  
from numpy import random   
from copy import copy
       
import agilepy.lib_base.classman as cm
import agilepy.lib_base.arrayman as am
import agilepy.lib_base.xmlman as xm
from  agilepy.lib_base.geometry import *
#from coremodules.modules_common import *
from coremodules.network.network import SumoIdsConf, MODES
from agilepy.lib_base.processes import Process,P,call,CmlMixin
from coremodules.misc.shapeformat import ShapefileImporter


import matplotlib as mpl
import matplotlib.pyplot as plt
        
class Detectorflows(cm.BaseObjman):
        def __init__(self, ident = 'detectorflows', demand=None,  name = 'Detector flows', 
                        info ='Flows measured by detectors, which can be used to generate vehicle routes using the DFRouter.',
                         **kwargs):
            #print 'Detectorflows.__init__',name,kwargs


            self._init_objman(  ident = ident, 
                                parent=demand, 
                                name = name, 
                                info = info, 
                                **kwargs )
                        
            attrsman = self.set_attrsman(cm.Attrsman(self))                    
            self._init_attributes()
            self._init_constants()


        def _init_attributes(self):
            attrsman = self.get_attrsman()

            self.detectors = attrsman.add( cm.ObjConf( Detectors('detectors',self),
                                                            groupnames = ['parameters'] )
                                                )      
                                                
            self.flowmeasurements = attrsman.add( cm.ObjConf( Flowmeasurements('flowmeasurements',self),
                                                            groupnames = ['parameters'] )
                                                )         
    
        
        def get_scenario(self):
            return self.parent.get_scenario()  
            
        def add_flows_to_edgeresultsevolution(self, edgeresults):
            print 'add_flows_to_edgeresultsevolution'
            attrname_detectorflows = 'detectorflows'
            if not edgeresults.has_attrname(attrname_detectorflows):
                # add detector result attributes
     
                attrinfos = OrderedDict([\
                        (attrname_detectorflows,  {  'name':'Detector flows',
                                        #'symbol':'F_{MA}',
                                        'unit':None,    
                                        'default':0, 
                                        'info':'Flows measured by detectors.',
                                        'xmltag':'detectorFlows',
                                        'groupnames':['Detector flows']
                                        }),
                        # more result attributes can be added ex. heavy duty flows
                        ])
                

                
                for attrname, kwargs in attrinfos.iteritems():
                    edgeresults.add_resultattr(attrname, **kwargs)
            

            
            # add flow measurements
            detectors = self.detectors
            flowmeasurements = self.flowmeasurements
            if (len(detectors) == 0) & (len(flowmeasurements) == 0):
                # nothing to be copied
                return True
                
            net = self.get_scenario().net
            ids_flow = flowmeasurements.get_ids()
            ids_detectors = detectors.get_ids()
            # prepare edgeresults
            time_start = np.min(flowmeasurements.timeperiods[ids_flow])
            periods = list(set(flowmeasurements.timeperiods[ids_flow].tolist()))
            periods.sort()
            if len(periods)>0:
                time_interval = periods[1] - periods[0] 
            else:
                time_interval = 3600.0
            time_end = np.max(flowmeasurements.timeperiods[ids_flow]) + time_interval
            
            i_start, i_end = edgeresults.adapt_intervals(time_start, len(periods), time_interval)
            
            # reset Detector flow attributes
            for attrconf in edgeresults.get_group('Detector flows'):
                attrconf.reset()
                
            for id_flow, id_detector, period, flow_pax, flow_heavyduty in zip(\
                            ids_flow,
                            flowmeasurements.ids_detector[ids_flow],
                            flowmeasurements.timeperiods[ids_flow],
                            flowmeasurements.flows_passenger[ids_flow],
                            flowmeasurements.flows_heavyduty[ids_flow],):
               print '  id_detector',id_detector,len(detectors),'id_flow',id_flow
               
               # some detectors may have been outside the network
               # TODO: eliminate flow imports when no associate detector is found
               if id_detector in ids_detectors: 
                        
                       if detectors.reliabilities[id_detector] > 0.8:
                           if (flow_pax > 0)|(flow_heavyduty > 0):
                               flow = 0.0
                               if (flow_pax > 0):
                                   flow += flow_pax
                               if (flow_heavyduty > 0):
                                   flow += flow_heavyduty
                                    
                               ids_lane = detectors.ids_lanes[id_detector]
                               if ids_lane is not None: # happens if no lanes could be matched
                                   if len(ids_lane)>0:
                                        edgeresults.add_edgevalue(net.lanes.ids_edge[ids_lane[0]], attrname_detectorflows, period, flow)
                                                                    
        def add_flows_to_edgeresults(self, edgeresults):
            if not edgeresults.has_attrname('detectorflows'):
                # add detector result attributes
     
                attrinfos = OrderedDict([\
                        ('detectorflows',  {  'name':'Detector flows',
                                        #'symbol':'F_{MA}',
                                        'unit':None,    
                                        'default':0, 
                                        'info':'Flows measured by detectors.',
                                        'xmltag':'detectorFlows',
                                        'groupnames':['detectorflows']
                                        }),
                        # more result attributes can be added ex. heavy duty flows
                        ])
                

                
                for attrname, kwargs in attrinfos.iteritems():
                    edgeresults.add_resultattr(attrname, **kwargs)
            
            # reset Detector flow attributes
            for attrconf in edgeresults.get_group('Detector flows'):
                attrconf.detectorflows.reset()
            
            # add flow measurements
            detectors = self.detectors
            flowmeasurements = self.flowmeasurements
            net = self.get_scenario().net
            ids_flow = flowmeasurements.get_ids()
            for id_detector, period, flow_pax, flow_heavyduty in zip(\
                            flowmeasurements.ids_detector[ids_flow],
                            flowmeasurements.timeperiods[ids_flow],
                            flowmeasurements.flows_passenger[ids_flow],
                            flowmeasurements.flows_heavyduty[ids_flow],):
                
               if detectors.reliabilities[id_detector] > 0.8:
                   if (flow_pax > 0)|(flow_heavyduty > 0):
                       flow = 0.0
                       if (flow_pax > 0):
                           flow += flow_pax
                       if (flow_heavyduty > 0):
                           flow += flow_heavyduty
                            
                       ids_lane = detectors.ids_lanes[id_detector]
                       if ids_lane is not None: # happens if no lenes could be matched
                           if len(ids_lane)>0:
                                id_edge = net.lanes.ids_edge[ids_lane[0]]
                                if edgeresults.ids_edge.has_index(id_edge):
                                   id_edgeres = edgeresults.ids_edge.get_id_from_index(id_edge)
                                   edgeresults.detectorflows[id_edgeres] += flow
                                
                                else:
                                    edgeresults.add_row(    ids_edge = id_edge,
                                                            detectorflows = flow
                                                            )
                       
                                    
                                
class Detectors(am.ArrayObjman):
    def __init__(self, ident,detectorflows,**kwargs):
            self._init_objman(  ident, parent = detectorflows,
                                name = 'Detectors',
                                info = 'Contains detector data.',
                                xmltag = ('detectors','detectorDefinition','ids_sumo'),
                                **kwargs)
            
            self._init_attributes()
            self._init_constants()

    
    def _init_attributes(self):
            self.add_col(SumoIdsConf('Detector', xmltag = 'id'))
            
            
            self.add_col(am.IdlistsArrayConf('ids_lanes', self.get_scenario().net.lanes, 
                                    name = 'IDs Lane', 
                                    info = """Lane IDs where detector is located. 
                                    Single or multiple lanes must be from the same egde.
                                    In case of multiple lanes the measured flows are distributed on the lanes using some heuristics.""",
                                    ))
                                    
            if hasattr(self,'ids_lane'):
                self.delete('ids_lane')
            
            self.add_col(am.ArrayConf( 'names', "",
                                    dtype = np.object,
                                    perm='rw', 
                                    name = 'Name',
                                    info = 'Human readable detector name. Can be used to indicate detector location.',
                                    ))
                                    
            self.add_col(am.ArrayConf( 'positions', 0.0,
                                    perm='r', 
                                    name = 'Position',
                                    unit = 'm',
                                    xmltag = 'pos',
                                    info = 'Position on edge where detector is located.',
                                    ))
            
            
            self.add_col(am.ArrayConf( 'directions', 0.0,
                                    perm='rw', 
                                    name = 'direction',
                                    unit = 'DEG',
                                    info = 'Direction of detector in degrees. North is zero degree.',
                                    ))
                                                                                    
            self.add_col(am.ArrayConf( 'coords',  np.zeros(3, dtype=np.float32),
                                        groupnames = ['state'],
                                        perm='r', 
                                        name = 'Coords',
                                        unit = 'm',
                                        info = 'Dedector coordinate.',
                                        is_plugin = True,
                                        ))
            
    
            self.add_col(am.ArrayConf( 'reliabilities', 1.0,
                                    perm='rw', 
                                    name = 'Reliability',
                                    info = 'Reliability of detector: 0 = broken, 1 = fully reliable. Some detectors provide this information which can help to eliminate unreliable flow measurements.',
                                    ))
                                    
    def get_scenario(self):
        return self.parent.parent.get_scenario()
    
    def match_detectors_to_lane(self, modename = 'passenger', 
                                    is_edgedetectors = True, is_check_direction = True, 
                                    n_targetedge=5, d_max = 50.0, 
                                    phidelta_max = 10.0/180*np.pi):
        net = self.get_scenario().net
        lanes = net.lanes
        edges = net.edges
        id_mode = net.modes.get_id_mode(modename)
        accesslevels = edges.get_accesslevels(net.modes.get_id_mode(modename = modename))
        
        get_ids_edge_from_inds_seg = edges.get_ids_edge_from_inds_seg
        get_dist_point_to_edge = edges.get_dist_point_to_edge
        get_closest_edge = edges.get_closest_edge
        
        ids = self.get_ids()
        for id_detect, point, phi_deg in zip(ids,self.coords[ids],self.directions[ids]):
            #/180.0*np.pi+np.pi/2.0
            if phi_deg > 180:
                phi = (phi_deg-270)/180.0*np.pi
            else:
                phi = (phi_deg+90)/180.0*np.pi
            print '  Detector id_detect',id_detect#,'point',point,'phi_deg',phi_deg,'phi',phi
            
            ids_edge_target, dists = get_closest_edge( point,  n_best = n_targetedge, 
                                                    d_max = d_max,
                                                    is_ending = True, 
                                                    is_detect_initial = False, 
                                                    is_detect_final = False,
                                                    accesslevels = accesslevels
                                                    )
                                                    
            print '    ids_edge_target',ids_edge_target
            #print '    dists',dists
            n = len(ids_edge_target)
            if is_check_direction & (n > 0):
                #print '    type(dists[0])',type(dists[0]),dists[0]
                costs = np.zeros(n, dtype = np.float32)
                for i, id_edge_target, dist in zip(xrange(n), ids_edge_target, dists):
                    dist_point_edge, segment = get_dist_point_to_edge(point, id_edge_target, 
                                                is_ending=True,
                                                is_detect_initial = False,
                                                is_detect_final = False,
                                                is_return_segment = True,
                                                )
                    x1,y1,x2,y2 = segment
                    phi_seg =  np.arctan2(y2-y1, x2-x1)
                    phi_delta = np.abs(anglediff(phi, phi_seg))
                    if phi_delta>phidelta_max:
                        phi_delta = 1000.0 # very high, but not infinity, so that distance decides if all out of range
                    costs[i] = dist_point_edge * phi_delta
                    #print '      check id_edge',id_edge_target, 'dist',dist_point_edge
                    #print '        phi_seg_deg',phi_seg*180/np.pi-90,'phi_seg',phi_seg,'phi_delta',phi_delta,'cost',costs[i]
                
                print '    >>matched id_edge',   ids_edge_target[np.argmin(costs)]
                id_edge_found = ids_edge_target[np.argmin(costs)]
                
                        
                    
            elif n > 0:
                id_edge_found =   ids_edge_target[0]
            else:
                id_edge_found = -1
            
            if id_edge_found > -1:
                # select lane
                ids_lane = edges.ids_lanes[id_edge_found]
                #print '  id_edge_found',id_edge_found,'ids_lane',edges.ids_lanes[id_edge_found]
                ids_lane_access = ids_lane[lanes.get_laneindexes_allowed(ids_lane, id_mode)]
                #print '  ids_lane_access',ids_lane_access
                
                if len(ids_lane_access)>0:
                    if is_edgedetectors:
                        # associate all lanes with detector 
                        self.ids_lanes[id_detect] = ids_lane_access
                    
                    else:
                        # coose closest lane....TODO
                        self.ids_lanes[id_detect] = ids_lane_access
                    
        
    def write_xml(self, fd=None, indent = 0):
        #<detectors>
        #    <detectorDefinition id="<DETECTOR_ID>" lane="<LANE_ID>" pos="<POS>"/>
        #    ... further detectors ...
        #</detectors>
        print 'Detectors.write_xml'
        fd.write(xm.begin('detectors',indent))
        
        ids = self.get_ids()
        scenario = self.get_scenario()
        get_sumoinfo_from_id_lane = scenario.net.lanes.get_sumoinfo_from_id_lane
        for id_detector, ids_lane, pos  in zip(\
                                                ids,
                                                self.ids_lanes[ids],
                                                self.positions[ids],
                                                ):
            
            print '  write id_detector',id_detector,'ids_lane',ids_lane
            if ids_lane is not None:
                ind_lane = 0
                for id_lane in ids_lane:
                    fd.write(xm.start('detectorDefinition',indent=indent+2))
                    fd.write(xm.num('id', self.get_id_xml_detector(id_detector, ind_lane)))
                    fd.write(xm.num('lane', get_sumoinfo_from_id_lane(id_lane)))
                    fd.write(xm.num('pos', pos))
    
                    fd.write(xm.stopit())# ends detector defs
                    ind_lane += 1
        fd.write(xm.end('detectors',indent))
    
    def get_id_xml_detector(self, id_detector, ind_lane):
        return   self.ids_sumo[id_detector]+'/'+str(ind_lane)     
    
    def get_id_detector_ind_lane(self, id_xml):
        if id_xml.count('/')>0:
            elements = id_xml.split('/')
            id_sumo = string.join(elements[:-1],'/')
            return self.ids_sumo.get_index(id_sumo), int(elements[-1])
        else:
            return self.ids_sumo.get_index(id_xml), 0
        
    
    def export_sumoxml(self, filepath):
        xm.write_obj_to_xml(self, filepath)
    
class Flowmeasurements(am.ArrayObjman):
    def __init__(self, ident,detectorflows,**kwargs):
            self._init_objman(  ident, parent = detectorflows,
                                name = 'Flow measurements',
                                info = 'Flow measurements at detectors.',
                                #xmltag = ('detectors','detectorDefinition','ids_sumo'),
                                **kwargs)
            
            self._init_attributes()
            self._init_constants()


    def _init_attributes(self):
            """
            Detector;Time;qPKW;qLKW;vPKW;vLKW
            myDet1;0;10;2;100;80
            ... further entries ...
            
            This means the first time has to name the entries (columns). Their order is not of importance, but at least the following columns must be included:
            
                Detector: A string holding the id of the detector this line describes; should be one of the ids used in <DETECTOR_FILE>
                Time: The time period begin that this entry describes (in minutes)
                qPKW: The number of passenger cars that drove over the detector within this time period
                vPKW: The average speed of passenger cars that drove over the detector within this time period in km/h
            
            The following columns may optionally be included:
            
                qLKW: The number of transport vehicles that drove over the detector within this time period
                vLKW: The average speed of transport vehicles that drove over the detector within this time period in km/h
            """
            
     
            self.add_col(am.IdsArrayConf('ids_detector', self.parent.detectors, 
                                    name = 'ID Detector', 
                                    info = 'Detector ID which measured this flow.',
                                    ))
            
            self.add_col(am.ArrayConf( 'timeperiods', 0.0,
                                    perm='rw', 
                                    name = 'Time period',
                                    unit = 's',
                                    info = 'Time period of flow measurement.',
                                    ))
            self.add_col(am.ArrayConf( 'flows_passenger', 0.0,
                                    perm='rw', 
                                    name = 'Passenger car flow',
                                    info = 'Number of passenger cars detected during the corrisponding time period.',
                                    ))                        
            
            
            self.add_col(am.ArrayConf( 'flows_heavyduty', 0.0,
                                    perm='rw', 
                                    name = 'Heavy duty vehicle flow',
                                    info = 'Number of heavy duty vehicles detected during the corrisponding time period.',
                                    ))
                                    
            
            self.add_col(am.ArrayConf( 'speeds_passenger', 0.0,
                                    perm='rw', 
                                    name = 'Passenger car speed',
                                    unit = 'm/s',
                                    info = 'Average velocity of passenger cars, detected during the corrisponding time period.',
                                    )) 
            
            self.add_col(am.ArrayConf( 'speeds_heavyduty', 0.0,
                                    perm='rw', 
                                    name = 'Heavy duty vehicle speed',
                                    unit = 'm/s',
                                    info = 'Average velocity of heavy duty vehicles, detected during the corrisponding time period.',
                                    )) 
                                                                                   
            #self.add_col(am.ArrayConf( 'types', '',
            #                        perm='rw',
            #                        choices = ["source", "sink", "between", "discarded", ""]
            #                        name = 'Type',
            #                        xmltag = 'type',
            #                        info = 'Detector type.',
            #                        ))
                                               
    def get_demand(self):
        return self.parent.parent
    
    def get_scenario(self):
        return self.parent.parent.parent
        
    
    def add_flow(   self, id_detector, timeperiod, flow_passenger, 
                    flow_heavyduty = 0.0, speed_passenger=-1.0,speed_heavyduty=-1.0):
                        
        if id_detector in self.parent.ids_sumo.get_value():
             id_flow = self.add_row(    ids_detector = id_detector,
                                        timeperiods = timeperiod,
                                        flows_passenger = flow_passenger,
                                        flows_heavyduty = flow_heavyduty,
                                        speeds_passenger = speed_passenger,
                                        speeds_heavyduty = speed_heavyduty,
                                        )
        else:
            id_flow = -1
            
        return id_flow
                 
    
    def export_csv(self, filepath, t_offset = 0, sep = ";"):
        """Export of flows to CVS file compatible with the DFrouter.
        """
        net = self.parent.parent.get_net()
        detectors = self.parent.detectors
        ids_sumo_detector = detectors.ids_sumo
        get_id_xml_detector = detectors.get_id_xml_detector

                
        f=open(filepath,'w')
        
        f.write('Detector'+sep+'Time'+sep+'qPKW'+sep+'qLKW'+sep+'vPKW'+sep+'vLKW'+'\n')
        #ids_flow = self.select_ids(self.flows_passenger.get_value()>=0)
        print '  flows_passenger',self.flows_passenger.get_value()
        ids_flow = self.get_ids()
        for id_detector,t, flow_passenger,flow_heavyduty,speed_passenger,speed_heavyduty in \
                    zip(\
                        self.ids_detector[ids_flow],
                        self.timeperiods[ids_flow],
                        self.flows_passenger[ids_flow],
                        self.flows_heavyduty[ids_flow],
                        self.speeds_passenger[ids_flow],
                        self.speeds_heavyduty[ids_flow]):
                    
                    
                    ids_lane = detectors.ids_lanes[id_detector]
                    if (ids_lane is not None)&(flow_passenger>=0):
                        print '  id_detector',id_detector,'t',t,'flow_passenger',flow_passenger,len(ids_lane)
                      
                        
                        n_lane = len(ids_lane)
                        for ind_lane, passengerflow_lane, heavyflow_lane in\
                            zip(    xrange(n_lane), 
                                    self.distribute_passengerflow_over_lanes(ids_lane, flow_passenger),
                                    self.distribute_heavyflow_over_lanes(ids_lane, flow_heavyduty)
                                    ):
                            
                            f.write(get_id_xml_detector(id_detector, ind_lane))
                            f.write(sep+str(t))
                            f.write(sep+str(passengerflow_lane))       
                            
                            if flow_heavyduty>=0:
                              f.write(sep+str(heavyflow_lane))
                            
                            if speed_passenger>=0:
                                f.write(sep+str(speed_passenger))
                                
                            if speed_heavyduty>=0:
                                f.write(sep+str(speed_heavyduty))
                        
                            f.write("\n")
        
        # format from 
        # https://sumo.dlr.de/wiki/Demand/Routes_from_Observation_Points
        #Detector;Time;qPKW;qLKW;vPKW;vLKW
        #myDet1;0;10;2;100;80
        #... further entries ...
        f.close()
    
    def distribute_heavyflow_over_lanes(self, ids_lane, flow, flow_max = 600):
        """
        Distribute measured edge traffic flow of lorries over the given lanes.
        """
        n_lane = len(ids_lane)
        flows_lane = np.zeros(n_lane, dtype = np.float32)
        
        if n_lane <= 2:
            flows_lane[0] = flow
        
        else:
            flows_lane[0:2] = [0.95*flow,0.05*flow] 
        return  np.array(flows_lane+0.5,dtype = np.int32)
        
    def distribute_passengerflow_over_lanes(self, ids_lane, flow, flow_max = 600):
        """
        Distribute measured edge traffic flow of passenger cars over the given lanes.
        """
        n_lane = len(ids_lane)
        flows_lane = np.zeros(n_lane, dtype = np.float32)
        
        if n_lane == 1:
            flows_lane[0] = flow
        
        elif n_lane == 2:
            if flow/2 > flow_max:
                flows_lane[0:2] = flow/2
                
            elif flow > flow_max:
                flows_lane[0:2] = [flow_max,flow-flow_max] 
            
            else:
                flows_lane[0:2] = [0.8*flow,0.2*flow] 
        
        elif n_lane == 3:
            if flow/3 > flow_max:
                flows_lane[0:3] = flow/3
            
            elif flow/2 > flow_max:
                flows_lane[0:3] = [flow_max,flow_max,flow-2*flow_max]
                
            elif flow > flow_max:
                flows_lane[0:3] = [0.5*(flow-flow_max),flow_max,0.5*(flow-flow_max)]
                
            else:
                flows_lane[0:3] = [0.2*flow,0.7*flow,0.1*flow] 
                
        
        elif n_lane == 4:
            if flow/4 > flow_max:
                flows_lane[0:4] = flow/4
            
            elif flow/3 > flow_max:
                flows_lane[0:4] = [flow_max,flow_max,flow_max,flow-3*flow_max]
            
            elif flow/2 > flow_max:
                flows_lane[0:4] = [0.5*(flow-2*flow_max),flow_max,flow_max,0.5*(flow-2*flow_max)]
                    
            elif flow > flow_max:
                flows_lane[0:4] = [1.0/3.0*(flow-flow_max),flow_max,1.0/3.0*(flow-flow_max),1.0/3.0*(flow-flow_max)]
                
            else:
                flows_lane[0:4] = [0.2*flow,0.5*flow,0.2*flow,0.1*flow] 
                
        else:
            flows_lane[0:4] = 1.0*flow/n_lane   
            
        return  np.array(flows_lane+0.5,dtype = np.int32)
                                
            
    def import_csv(self, filepath, t_offset = 0, t_start = 0, t_end = 24*3600, sep = ";"):
        net = self.parent.parent.get_net()
        detectors = self.parent.detectors
        ids_sumo = detectors.ids_sumo
        
        ids_detector = []
        times = []
        flows_passenger = []
        flows_heavyduty = []
        speeds_passenger = []
        speeds_heavyduty = []
                
        f=open(filepath,'r')
        
        
        
        # format from 
        # https://sumo.dlr.de/wiki/Demand/Routes_from_Observation_Points
        #Detector;Time;qPKW;qLKW;vPKW;vLKW
        #myDet1;0;10;2;100;80
        #... further entries ...
        
  
        
        print 'import_csv',filepath
        ind_col = 0
        cols = f.readline().strip()
        ind_col = 0
        ind_detector = -1
        ind_time = -1
        ind_flow_passenger = -1
        ind_flow_heavyduty = -1
        ind_speed_passenger = -1
        ind_speed_heavyduty = -1
        if len(cols)>=3:
            for col in cols.split(sep):
                if col == 'Detector':
                    ind_detector = ind_col
                elif col == 'Time':
                    ind_time = ind_col
                elif col == 'qPKW':
                    ind_flow_passenger = ind_col
                elif col == 'qLKW':
                    ind_flow_heavyduty = ind_col
                elif col == 'vPKW':
                    ind_speed_passenger = ind_col
                elif col == 'vLKW':
                    ind_speed_heavyduty = ind_col
                ind_col += 1
        else:
            return False
        
        for line in f.readlines():
            cols = line.split(sep)
            #print '    cols=',cols
            if len(cols)>=3:
                ind_col = 0
                is_valid = True
                t = 0.0
                flow_passenger = -1
                flow_heavyduty = -1
                speed_passenger = -1
                speed_heavyduty = -1
                
                for col_raw in cols:
                    col = col_raw.strip()
                    if ind_col == ind_detector:
                        if ids_sumo.has_index(col):
                            id_sumo_detector = col
                        else:
                            is_valid = False
                                
                    elif col.isdigit() & is_valid:
                        num = int(col)
                        if ind_col == ind_time:
                            t = num
                            
                        elif ind_col == ind_flow_passenger:
                            flow_passenger = num
                            
                        elif ind_col == ind_flow_heavyduty:
                            flow_heavyduty = num
                            
                        elif ind_col == ind_speed_passenger:
                            speed_passenger = num
                            
                        elif ind_col == ind_speed_heavyduty:
                            speed_heavyduty = num
                    else:
                        # invalid value
                        is_valid = False
                        
                    ind_col += 1
               
                if is_valid:
                    #print '  t',t,t_start,t_end,t+t_offset>=t_start,t+t_offset<t_end
                    if (t+t_offset>=t_start) & (t+t_offset<t_end):
                        ids_detector.append(ids_sumo.get_id_from_index(id_sumo_detector))
                        times.append(t)
                        flows_passenger.append(flow_passenger)
                        flows_heavyduty.append(flow_heavyduty)
                        speeds_passenger.append(speed_passenger)
                        speeds_heavyduty.append(speed_heavyduty)
            
                
        # insert in database
        ids_measure = self.add_rows( 
                    ids_detector = ids_detector,
                    timeperiods = times,
                    flows_passenger = flows_passenger,
                    flows_heavyduty = flows_heavyduty,
                    speeds_passenger = speeds_passenger,
                    speeds_heavyduty = speeds_heavyduty,
                    )            
              
        f.close()
        
        return ids_measure
    
    
    def import_csv_alt(self, filepath, t_offset = 0, t_start = 0, t_end = 24*3600, t_period = 3600, share_heavyduty = 0.05, sep = ","):
        # reads flows from the following format from 
        #
        #data    giorno_settimana    tipo_giorno    VIA_SPIRA    TRA VIA    E VIA    DIREZIONE    selezionato    Micro    Codice     0- 1     1- 2     2- 3     3- 4     4- 5     5- 6     6- 7     7- 8     8- 9     9- 10     10- 11     11- 12     12- 13     13- 14     14- 15     15- 16     16- 17     17- 18     18- 19     19- 20     20- 21     21- 22     22- 23     23- 24    tot    Acc. %
        # 0            1                        2          3                  4            5                6             7        8     9 ....
        print 'import_csv_alt',filepath
        net = self.parent.parent.get_net()
        #detectors = self.parent.detectors
        detectors = self.get_demand().detectorflows.detectors
        ids_sumo = detectors.ids_sumo
        
        ids_detector = []
        times = []
        flows_passenger = []
        flows_heavyduty = []
        speeds_passenger = []
        speeds_heavyduty = []
                
        f=open(filepath,'r')
        
        print 'import_csv_alt',filepath
        ind_col = 0
        # read first line (not used)
        cols = f.readline().strip()
        ind_detector = 9
        ind_flows_base = 10
        ids_measure = []
        
        for line in f.readlines():
            cols = line.split(sep)
            #print '    cols=',len(cols)
            if len(cols)>=ind_flows_base+24:
                id_sumo_detector = cols[ind_detector].strip()
                print '    id_sumo_detector',id_sumo_detector,ids_sumo.has_index(id_sumo_detector)
                if ids_sumo.has_index(id_sumo_detector):
                        
                        # go through time columns
                        ind_col = 0
                        for col_raw in cols[ind_flows_base:ind_flows_base+24]:
                            col = col_raw.strip()
                            if col == '':
                                flow = 0
                            else:
                                flow = int(col)
                            time_from = t_offset + ind_col * t_period
                            time_to = t_offset + (ind_col + 1) * t_period
                            if (time_from >= t_start) & (time_to <= t_end):
                                    # insert in database
                                    id_measure = self.add_row( 
                                            ids_detector = ids_sumo.get_id_from_index(id_sumo_detector),
                                            timeperiods = time_from,
                                            flows_passenger = int((1.0-share_heavyduty)*flow+0.5),
                                            flows_heavyduty = int(share_heavyduty * flow+0.5),
                                            speeds_passenger = -1,
                                            speeds_heavyduty = -1,
                                            ) 
                                    ids_measure.append(id_measure)
                            ind_col += 1
               
               
                   
              
        f.close()
        
        return ids_measure
        
        
    def detectorflows_to_routes(self, is_clear_trips = True, is_export_network = True, 
                                is_make_probabilities = True, cmloptions = None,):
        """NOT YET IMPLEMENTED"""
        
        #  jtrrouter --flow-files=<FLOW_DEFS> 
        # --turn-ratio-files=<TURN_DEFINITIONS> --net-file=<SUMO_NET> \
        # --output-file=MySUMORoutes.rou.xml --begin <UINT> --end <UINT>
        
        if is_make_probabilities:
            self.normalize_turnprobabilities()
        
        scenario = self.parent.get_scenario()
        if cmloptions is None:
            cmloptions = '-v --max-edges-factor 1  --seed 23423 --repair --ignore-vclasses false --ignore-errors --turn-defaults 5,90,5'
        
        trips = scenario.demand.trips
        if is_clear_trips:
            # clear all current trips = routes
            trips.clear_trips()
        
    
        
        rootfilepath = scenario.get_rootfilepath()
        netfilepath = scenario.net.get_filepath()
        flowfilepath = rootfilepath+'.flow.xml'
        turnfilepath = rootfilepath+'.turn.xml'
        
        routefilepath = trips.get_routefilepath()
        
        # first generate xml for net
        scenario.net.export_netxml()
        
        ids_mode = self.get_modes()
        print 'turnflows_to_routes', ids_mode #scenario.net.modes.get_ids()
        print '  cmloptions',cmloptions
        
        # route for all modes and read in routes 
        for id_mode in  ids_mode:
            # write flow and turns xml file for this mode
            time_start, time_end = self.export_flows_and_turns(flowfilepath, turnfilepath, id_mode)
            print '  time_start, time_end =',time_start, time_end
            if time_end>time_start:# means there exist some flows for this mode
                cmd = 'jtrrouter --route-files=%s --turn-ratio-files=%s --net-file=%s --output-file=%s --begin %s --end %s %s'\
                    %(  P+flowfilepath+P, 
                        P+turnfilepath+P, 
                        P+netfilepath+P,
                        P+routefilepath+P,
                        time_start,
                        time_end,
                        cmloptions,
                        )
                #print '\n Starting command:',cmd
                if call(cmd):
                    if os.path.isfile(routefilepath): 
                        trips.import_routes_xml(routefilepath, is_generate_ids = True)
                        os.remove(routefilepath)
                
            else:
                print 'jtrroute: no flows generated for id_mode',id_mode 
        
        
        #self.simfiles.set_modified_data('rou',True)
        #self.simfiles.set_modified_data('trip',True)
        # trips and routes are not yet saved!!

class DetectorMatcher(Process):
    def __init__(self, ident = 'detectormatcher', detectors = None,  logger = None, **kwargs):
        print 'DetectorMatcher.__init__'
        
        # TODO: let this be independent, link to it or child??
        
           
        self._init_common(  ident, 
                            parent = detectors,
                            name = 'Detector Matcher', 
                            logger = logger,
                            info ='Match detectors to lanes.',
                            )
        
        
        attrsman = self.set_attrsman(cm.Attrsman(self))
        
        
         
        net = detectors.get_scenario().net      
                         
        self.modename = attrsman.add(cm.AttrConf( 'modename',kwargs.get('modename','passenger'),
                            groupnames = ['options'], 
                            choices = net.modes.names.get_indexmap().keys(),
                            name = 'Mode name', 
                            info = 'Matched lanes must be accessible at least for this mode.',
                            ))
        
        print 'net.modes.names.get_indexmap().keys()',net.modes.names.get_indexmap().keys(),  self.modename        
        
        self.is_edgedetectors = attrsman.add(cm.AttrConf( 'is_edgedetectors',kwargs.get('is_edgedetectors',False),
                            groupnames = ['options'], 
                            name = 'One detector per edge', 
                            info = """If True, it is assumed that there is only one detector per edge
                            and detected edge flows will be distributed accross accessible lanes according to some heuristics.
                            If False then each detector is matched to one lane. This is somewhat risky and requires a good 
                            geometrical coincidence between detector position and lane. 
                            """,
                            ))
        
        
        self.is_check_direction = attrsman.add(cm.AttrConf( 'is_check_direction',kwargs.get('is_check_direction',False),
                            groupnames = ['options'], 
                            name = 'Use detector direction', 
                            info = """If True, use director direction information to improve matching.
                            """,
                            ))
        self.phidelta_max = attrsman.add(cm.AttrConf( 'phidelta_max',kwargs.get('phidelta_max',10.0),
                            groupnames = ['options'], 
                            name = 'Max. angle diff.', 
                            unit = 'deg',
                            info = """Maximum difference of angels between detector and nearest edge segment in degrees.
                            To be used in conjunction with "Use detector direction" """,
                            ))
        
        self.d_max = attrsman.add(cm.AttrConf( 'd_max',kwargs.get('d_max',20.0),
                            groupnames = ['options'], 
                            name = 'Maximum search dist.', 
                            unit = 'm',
                            info = """Maximum search distance around detectors.""",
                            ))
                            
        self.n_targetedge = attrsman.add(cm.AttrConf( 'n_targetedge',kwargs.get('n_targetedge',5),
                            groupnames = ['options'], 
                            name = 'Number of target edges', 
                            info = """Maximum number of considered target edges when searching for the nearest edge.
                            """,
                            ))
                                                                                        
        
        
        
                            
    
    def do(self):
        print 'DetectorMatcher.do'
        self.parent.match_detectors_to_lane(modename = self.modename, 
                                            is_edgedetectors = self.is_edgedetectors, 
                                            is_check_direction = self.is_check_direction, 
                                            n_targetedge = self.n_targetedge, 
                                            d_max = self.d_max, 
                                            phidelta_max = self.phidelta_max/180.0*np.pi)
        return True
        
class DFRouter(CmlMixin,Process):
    def __init__(self, detectorflows, logger = None,**kwargs):
        
        self._init_common(  'detectorflowrouter', name = 'Detectorflow Router', 
                            parent = detectorflows,
                            logger = logger,
                            info ='Generates routes from measured flows at detectors using the DFrouter.',
                            )
         
        self.init_cml('dfrouter')# pass  no commad to generate options only
        
        
        attrsman = self.get_attrsman()
        
        
                                    
        self.add_option('timestep', kwargs.get('timestep',3600),
                        groupnames = ['options','processing'],# 
                        cml = '--time-step',
                        name = 'Time step', 
                        info = 'Expected distance between two successive data sets.',
                        untit = 's',
                        )
        
        self.add_option('is_respect_concurrent_inflows', kwargs.get('is_respect_concurrent_inflows',False),
                        groupnames = ['options','processing'],# 
                        cml = '--respect-concurrent-inflows',
                        name = 'Respect concurrent inflows', 
                        info = 'Try to determine further inflows to an inbetween detector when computing split probabilities.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
                                        
        self.add_option('is_routes_for_all', kwargs.get('is_routes_for_all',False),
                        groupnames = ['options','processing'],# 
                        cml = '--routes-for-all',
                        name = 'Routes for inbetween detectors', 
                        info = 'Forces DFROUTER to compute routes for in-between detectors.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
                        
        #self.add_option('is_guess_empty_flows', kwargs.get('is_guess_empty_flows',False),
        #                groupnames = ['processing'],# 
        #                cml = '--guess-empty-flows',
        #                name = 'Guess empty flows', 
        #                info = 'Derive missing flow values from upstream or downstream (not working!)',
        #                #is_enabled = lambda self: self.width_sublanes > 0,
        #                )
        
        #self.add_option('is_ignore_invalid_detectors', kwargs.get('is_ignore_invalid_detectors',False),
        #                groupnames = ['processing',],# 
        #                cml = '--ignore-invalid-detectors',
        #                name = 'Ignore invalid detectors', 
        #                info = 'Only warn about unparseable detectors.',
        #                #is_enabled = lambda self: self.width_sublanes > 0,
        #                )
        
        self.add_option('is_keep_unfinished_routes', kwargs.get('is_keep_unfinished_routes',False),
                        groupnames = ['options','processing'],# 
                        cml = '--keep-unfinished-routes',
                        name = 'Keep unfinished routes', 
                        info = 'Keeps routes even if they have exhausted max-search-depth.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
       
        self.add_option('is_keep_longer_routes', kwargs.get('is_keep_longer_routes',False),
                        groupnames = ['options','processing'],# 
                        cml = '--keep-longer-routes',
                        name = 'Keep longer routes', 
                        info = 'eeps routes even if a shorter one exists.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )                 
        
        self.add_option('n_max_search_depth', kwargs.get('n_max_search_depth',30),
                        groupnames = ['options','processing'],# 
                        cml = '--max-search-depth',
                        name = 'Max. search depth', 
                        info = 'Number of edges to follow a route without passing a detector.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        ) 
        
        self.add_option('is_keep_turnarounds', kwargs.get('is_keep_turnarounds',False),
                        groupnames = ['options','processing'],# 
                        cml = '--keep-turnarounds',
                        name = 'keep turnarounds', 
                        info = 'Allow turnarounds as route continuations.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
        
        self.add_option('length_min_route', kwargs.get('length_min_route',500.0),
                        groupnames = ['options','processing'],# 
                        cml = '--min-route-length',
                        name = 'Min route length', 
                        info = 'Minimum distance in meters between start and end node of every route.',
                        unit = 'm',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
                        
        
        
        self.add_option('is_randomize_flows', kwargs.get('is_randomize_flows',False),
                        groupnames = ['options','processing'],# 
                        cml = '--randomize-flows',
                        name = 'Randomize flows', 
                        info = 'Generate random departure times for emitted vehicles.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
                                        
        
        self.add_option('c_flows', kwargs.get('c_flows',1.0),
                        groupnames = ['options','processing'],# 
                        cml = '--scale',
                        name = 'Flow scale factor', 
                        info = 'Scale factor for flows.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
                                        
        self.add_option('c_time', kwargs.get('c_time',1.0),
                        groupnames = ['options','processing'],# 
                        cml = '--time-factor',
                        name = 'Time factor', 
                        info = 'Multiply flow times with TIME to get seconds.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
        
        self.add_option('time_offset', kwargs.get('time_offset',0),
                        groupnames = ['options','processing'],# 
                        cml = '--time-offset',
                        name = 'Time offset', 
                        info = 'Multiply flow times with TIME to get seconds.',
                        #is_enabled = lambda self: self.width_sublanes > 0,
                        )
        
        
        self.add_option('seed', 1234,
                        groupnames = ['options','processing'],# 
                        cml = '--seed',
                        name = 'Random seed', 
                        info = 'Initialises the random number generator with the given value.',
                        )
                        
        self.is_export_network = attrsman.add(am.AttrConf(  'is_export_network', True,
                                    groupnames = ['options',],
                                    perm='rw', 
                                    name = 'Export network', 
                                    info = 'Export network before routing.',
                                    ))
        
                                                                             
        self.is_clear_trips = attrsman.add(am.AttrConf(  'is_clear_trips', True,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Clear trips', 
                                    info = 'Clear all trips in current trips database before routing.',
                                    ))
                                    
        #self.add_option('turnratiofilepath', turnratiofilepath,
        #                groupnames = ['_private'],# 
        #                cml = '--turn-ratio-files',
        #                perm='r', 
        #                name = 'Net file', 
        #                wildcards = 'Net XML files (*.net.xml)|*.net.xml',
        #                metatype = 'filepath',
        #                info = 'SUMO Net file in XML format.',
        #                )
        
    def do(self):
        cmloptions = self.get_cml()
        scenario = self.parent.get_scenario()
        trips = scenario.demand.trips
        if self.is_clear_trips:
            # clear all current trips = routes
            trips.clear_trips()
        
    
        
        rootfilepath = scenario.get_rootfilepath()
        netfilepath = scenario.net.get_filepath()
        measuresfilepath = rootfilepath+'.measure.csv'
        detectorsfilepath = rootfilepath+'.detect.xml'
        emittersfilepath = rootfilepath+'.emitter.xml'
        
        self.parent.flowmeasurements.export_csv(measuresfilepath)
        self.parent.detectors.export_sumoxml(detectorsfilepath)
        
        routefilepath = trips.get_routefilepath()
        
        # first generate xml for net
        if self.is_export_network:
            scenario.net.export_netxml()
        
        print 'DFRouter.do'
        print '  cmloptions',cmloptions
        
        #dfrouter --net-file bonet190614_ms_dflows.net --routes-output bonet190614_ms_dflows.rou.xml --emitters-output vehicles.xml --detector-files detectors.xml --measure-files bonet190614_ms_dflows.dflows2.csv
        cmd = cmloptions + ' --net-file %s --detector-files %s --measure-files %s --routes-output %s --emitters-output %s'\
            %(  P+netfilepath+P, 
                P+detectorsfilepath+P, 
                P+measuresfilepath+P,
                P+routefilepath+P,
                P+emittersfilepath+P,
                )
        #print '\n Starting command:',cmd
        if call(cmd):
            if os.path.isfile(routefilepath): 
                scenario.demand.trips.import_routes_xml(routefilepath)
                os.remove(routefilepath)
                return True
            else:
                return False    
        else:
            return False                
        
   
        
        

class FlowsImporter(Process):
    def __init__(self, ident='flowsimporter', flows = None, 
                    name = 'Flows Importer',
                    info ='Reads and imports flow measurements from detectors.',
                    filepath = '',logger=None, **kwargs):
        demand = flows.parent.parent
        
        

        
        self._init_common(  ident, name = name, 
                            parent = flows,
                            logger = logger,
                            info = info,
                            )
        
        
                 
        attrsman = self.get_attrsman()
        
        self.t_start = attrsman.add(am.AttrConf(  't_start', 0,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Start time', 
                                    unit = 's',
                                    info = 'Start reading detector data at this time.',
                                    ))
            
        self.t_end = attrsman.add(am.AttrConf('t_end', 24*3600,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'End time', 
                                    unit = 's',
                                    info = 'Stop reading detector data at this time.',
                                    ))
        
        
        self.t_offset = attrsman.add(am.AttrConf('t_offset', 0,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Time offset', 
                                    unit = 's',
                                    info = 'Time offset added to the time of the measurement values prior to the verification of the time window.',
                                    ))
                                    

                                           
        self.filepath = attrsman.add(am.AttrConf('filepath',filepath,
                                            groupnames = ['options'],# this will make it show up in the dialog
                                            perm='rw', 
                                            name = 'Flow file', 
                                            wildcards = "Flow CSV files (*.csv)|*.csv|CSV files (*.txt)|*.txt|All files (*.*)|*.*",
                                            metatype = 'filepath',
                                            info = 'CSV file with flow measurements from detectors for the specific mode and time interval.',
                                            ))

        
        
    
    def update_params(self):
        """
        Make all parameters consistent.
        example: used by import OSM to calculate/update number of tiles
        from process dialog
        """
        pass
        #self.workdirpath = os.path.dirname(self.netfilepath)
        #bn =  os.path.basename(self.netfilepath).split('.')
        #if len(bn)>0:
        #    self.rootname = bn[0]
    
    def do(self):
        #self.update_params()
        if os.path.isfile(self.filepath):
            ids_measure = self.parent.import_csv(  self.filepath, 
                                            t_offset = self.t_offset, 
                                            t_start = self.t_start, 
                                            t_end = self.t_end, 
                                            sep = ";")
            return True
        else:
            return False
        
        
class FlowsImporterAlt(Process):
    def __init__(self, ident='flowsimporter_alt', flows = None, 
                    name = 'Alternative flows Importer',
                    info ='Reads and imports flow measurements from detectors in a specific format.',
                    filepath = '',logger=None, **kwargs):
        demand = flows.parent.parent
        
        

        
        self._init_common(  ident, name = name, 
                            parent = flows,
                            logger = logger,
                            info = info,
                            )
        
        
                 
        attrsman = self.get_attrsman()
        
        self.t_start = attrsman.add(am.AttrConf(  't_start', 0,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Start time', 
                                    unit = 's',
                                    info = 'Start reading detector data at this time.',
                                    ))
            
        self.t_end = attrsman.add(am.AttrConf('t_end', 24*3600,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'End time', 
                                    unit = 's',
                                    info = 'Stop reading detector data at this time.',
                                    ))
        
        
        
        
        self.t_offset = attrsman.add(am.AttrConf('t_offset', 0,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Time offset', 
                                    unit = 's',
                                    info = 'Time offset added to the time of the measurement values prior to the verification of the time window.',
                                    ))
                                    
        self.share_heavyduty = attrsman.add(am.AttrConf('share_heavyduty', 0.05,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Share of heavy duty vehicles', 
                                    info = 'Estimated share of heavy duty vehicles of measured flows.',
                                    ))                            
                                    


                                                                               
        self.filepath = attrsman.add(am.AttrConf('filepath',filepath,
                                            groupnames = ['options'],# this will make it show up in the dialog
                                            perm='rw', 
                                            name = 'Flow file', 
                                            wildcards = "Flow CSV files (*.csv)|*.csv|CSV files (*.txt)|*.txt|All files (*.*)|*.*",
                                            metatype = 'filepath',
                                            info = 'CSV file with flow measurements from detectors for the specific mode and time interval.',
                                            ))

        
        
    
    def update_params(self):
        """
        Make all parameters consistent.
        example: used by import OSM to calculate/update number of tiles
        from process dialog
        """
        pass
        #self.workdirpath = os.path.dirname(self.netfilepath)
        #bn =  os.path.basename(self.netfilepath).split('.')
        #if len(bn)>0:
        #    self.rootname = bn[0]
    
    def do(self):
        #self.update_params()
        if os.path.isfile(self.filepath):
            ids_measure = self.parent.import_csv_alt(  self.filepath, 
                                            t_offset = self.t_offset, 
                                            t_start = self.t_start, 
                                            t_end = self.t_end, 
                                            share_heavyduty = self.share_heavyduty,
                                            sep = ",",
                                            )
            return True
        else:
            return False
     
    
    
class DetectorsFromShapeImporter(ShapefileImporter):
    def __init__(self, ident='detectorsfromshapeimporter', detectors = None, 
                    name = 'Detectors from Shapefile importer',
                    filepath = '',logger=None, **kwargs):
        
        net = detectors.parent.parent.get_net()
        ShapefileImporter.__init__( self, ident, detectors,
                                    name = name,
                                    filepath = filepath, 
                                    coordsattr = 'coords', 
                                    attrnames_to_shapeattrs = { 'ids_sumo':'ID',
                                                                'directions':'',
                                                                'names':'',
                                                                },
                                    projparams_target = net.get_projparams(),
                                    offset = net.get_offset(),
                                    boundaries = net.get_boundaries(is_netboundaries = True),
                                    logger = logger,
                                    **kwargs)
                                    
     
class UpdateDeparturesFromDetectorflows(Process):
    def __init__(self, ident = 'update_departures_from_detectorflows', detectorflows = None,  logger = None, **kwargs):
        print 'UpdateDeparturesFromDetectorflows.__init__'
        
        self._init_common(  ident, 
                            parent = detectorflows,
                            name = 'Updates times of trips and activities from detectorflows', 
                            logger = logger,
                            info ='Update times of trips and activities of the virtual population from the temporal distribution of detector flows.',
                            )
        
        attrsman = self.set_attrsman(cm.Attrsman(self))
        
        
        #~ PopFromOdfGenerator.__init__(self, ident, virtualpop,  logger = None, **kwargs)
        
        self.is_update_activities = attrsman.add(cm.AttrConf( 'is_update_activities',kwargs.get('is_update_activities',True),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    name = 'Update activities', 
                                    info = """Update times of hxh daily activities of the virtual population trying to match the detected flows.
                                              Note that this option requires a regeneration of the plans of the virtual population. 
                                                """,
                                    ))  
        
        self.is_update_plans = attrsman.add(cm.AttrConf( 'is_update_plans',kwargs.get('is_update_plans',False),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    name = 'Update plans', 
                                    info = """Update times of existing plans of the virtual population trying to match the detected flows.
                                        Note that this option requires that the plans are already generated.
                                    """,
                                    ))  
                                    
        self.is_update_trips = attrsman.add(cm.AttrConf( 'is_update_trips',kwargs.get('is_update_trips',True),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    name = 'Update trips', 
                                    info = 'Update the departure time of trips trying to match the detected flows.',
                                    ))  
                                    
                                    
                                    
        self.is_add_returntrips = attrsman.add(cm.AttrConf( 'is_add_returntrips',kwargs.get('is_add_returntrips',True),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    name = 'Add return trips', 
                                    info = 'Add return trips before updating departure time of trips to match the detected flows.',
                                    ))                            
                                    
                                    
        self.max_departure_hour = attrsman.add(cm.AttrConf( 'max_departure_hour',kwargs.get('max_departure_hour',16.),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    name = 'Latest departure', 
                                    info = 'Maximum departing hour for home to work trips.',
                                    ))
                                            
        self.min_return_hour = attrsman.add(cm.AttrConf( 'min_return_hour',kwargs.get('min_return_hour',10.),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    name = 'Earliest return', 
                                    info = 'Minimum return hour for home to work trips.',
                                    ))
                                    
        self.av_dtd_time_trips = attrsman.add(cm.AttrConf( 'av_dtd_time_trips',kwargs.get('av_dtd_time_trips',1800.),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    unit = 's',
                                    name = 'Av travel time trips', 
                                    info = 'Average door-to-door travel time for deamnd.trips, indipendently by the mean of transportation.',
                                    ))
                                    
                                    
        self.av_dtd_time_vp = attrsman.add(cm.AttrConf( 'av_dtd_time_vp',kwargs.get('av_dtd_time_vp',1800.),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    unit = 's',
                                    name = 'Av travel time VP', 
                                    info = 'Average door-to-door travel time for trips of the virtual population, indipendently by the mean of transportation.',
                                    ))
                                    
        self.is_plot_flows = attrsman.add(cm.AttrConf( 'is_plot_flows',kwargs.get('is_plot_flows',True),
                                    groupnames = ['options'], 
                                    perm='rw', 
                                    name = 'Plot flows', 
                                    info = 'Plot the detector flows over time; this will allow to control the correctness of data.',
                                    ))    
                                                                    
    def do(self):
        print 'UpdateDeparturesFromDetectorflows.do'

        '''
        Update departure times to reproduce detector flows distribution
        Currently update times for demand.trips or/and for h-x-h
        activities of the virtual population, before running the planner

        '''
#............Preparation
        demand = self.parent.parent
        virtualpop = demand.virtualpop
        detector_flows = self.parent.flowmeasurements
        ids_detflow = detector_flows.get_ids()
        det_hours = detector_flows.timeperiods[ids_detflow]
        det_flows = detector_flows.flows_passenger[ids_detflow] + detector_flows.flows_heavyduty[ids_detflow]
        step_hours = np.sort(np.unique(det_hours))
        interval_time = step_hours[1]-step_hours[0]
        
        time_interval_half = 0.5*interval_time
        is_randomize = 0.0
        
        step_hours+=interval_time/2.
        det_hours+=interval_time/2.

        step_flows0 = []
        step_flows_dep0 = []
        step_flows_arr0 = []
        
        
        if self.is_update_activities | self.is_add_returntrips:
                
        #............Split flows in departure and return
            for step_hour in step_hours:
                step_flow = np.sum(det_flows[(det_hours == step_hour)])
                step_flows0.append(step_flow)
                if step_hour/3600. <= self.max_departure_hour and step_hour/3600. <= self.min_return_hour:
                    step_flows_dep0.append(step_flow)
                    step_flows_arr0.append(0.)
                elif step_hour/3600. < self.max_departure_hour and step_hour/3600. > self.min_return_hour:
                    step_flows_arr0.append((step_hour/3600.-self.min_return_hour)/(self.max_departure_hour-self.min_return_hour)*step_flow)
                    step_flows_dep0.append((1-(step_hour/3600.-self.min_return_hour)/(self.max_departure_hour-self.min_return_hour))*step_flow)
                elif step_hour/3600. >= self.max_departure_hour and step_hour/3600. >= self.min_return_hour:
                    step_flows_dep0.append(0.)
                    step_flows_arr0.append(step_flow)
                    
        #............Plot
            # ~ if self.is_plot_flows:
                # ~ fig, ax = plt.subplots() 
                # ~ ax.plot(step_hours/3600., step_flows, label = 'Total flows')
                # ~ ax.plot(step_hours/3600., step_flows_dep, label = 'Departure flows')
                # ~ ax.plot(step_hours/3600., step_flows_arr, label = 'Arrival flows') 
                # ~ ax.legend()
                # ~ ax.set_xlabel('Hour')
                # ~ ax.set_ylabel('Total flow')
                # ~ ax.set_title('Total flow distribution - Initial ')
                # ~ plt.show()
            
        #............Smooth the curve to make the total number of departures equal to the total number of arrival
            sum_step_flows_dep = np.sum(step_flows_dep0)
            sum_step_flows_arr = np.sum(step_flows_arr0)
            arr_minus_dep = sum_step_flows_arr-sum_step_flows_dep
            n_intermediate_steps = len(step_hours[(step_hours/3600. < self.max_departure_hour)&(step_hours/3600. > self.min_return_hour)])
            shares = []
            for intermediate_step in range(n_intermediate_steps):
                shares.append(float(n_intermediate_steps+1)/2.-abs((float(n_intermediate_steps+1)/2-intermediate_step-1.))-0.5)        
            i = 0
            for step_hour, j in zip(step_hours, range(len(step_hours))):
                if step_hour/3600. < self.max_departure_hour and step_hour/3600. > self.min_return_hour:
                    step_flows_arr0[j] -= arr_minus_dep*shares[i]/np.sum(shares)/2.
                    step_flows_dep0[j] += arr_minus_dep*shares[i]/np.sum(shares)/2.
                    i+=1
                    if step_flows_arr0[j] < 0 or step_flows_dep0[j] < 0:
                        print 'WARNING, negative flow. Change parameters and plot to check.'
                    
            sum_step_flows_dep = np.sum(step_flows_dep0)
            sum_step_flows_arr = np.sum(step_flows_arr0)
    
                #............Plot
            if self.is_plot_flows:
                fig, ax = plt.subplots() 
                ax.plot(step_hours/3600., step_flows0, label = 'Total flows')
                ax.plot(step_hours/3600., step_flows_dep0, label = 'Departure flows')
                ax.plot(step_hours/3600., step_flows_arr0, label = 'Arrival flows') 
                ax.legend()
                ax.set_xlabel('Hour')
                ax.set_ylabel('Total flow')
                ax.set_title('Total flow distribution')
                plt.show()
                
                #............Preparation
            step_flows_dep_prob = step_flows_dep0/sum_step_flows_dep
            step_flows_arr_prob = step_flows_arr0/sum_step_flows_arr
            
        if self.is_update_activities:
                #............Update times of activities
            step_flows = copy(step_flows0)
            step_flows_dep = copy(step_flows_dep0)
            step_flows_arr = copy(step_flows_arr0)
            
            ids_vp = virtualpop.get_ids()
            
            plans =  virtualpop.get_plans()

            activities = virtualpop.get_activities()
            steps = range(len(step_hours))
            choices = []
            for step, step_hour in zip(steps, step_hours):
                choices.append([step_hour,step])
            unit = np.sum(step_flows_dep+step_flows_arr)/(len(ids_vp)*2.)
            
            convergenze = False
            while convergenze == False:
                convergenze = True
                for id_vp, ids_activity, id_plan in zip(\
                                        ids_vp, 
                                        virtualpop.activitypatterns[ids_vp], 
                                        virtualpop.ids_plan[ids_vp],
                                        ):
                    id_first_activity = ids_activity[0]
                    id_intermediate_act = ids_activity[1]
                    
                    print '-'*70
                    print '  id_vp',id_vp,'id_plan',id_plan,'ids_activity',ids_activity
                        #............Extract departure and return time
                    #Firstly assign intermediate departure times between 
                    #earliest arrival and latest departure in order to achieve convergenze
                    sum_prob_int_depart = 0.
                    sum_prob_int_arr = 0.
                    for step_hour, i in zip(step_hours, range(len(step_hours))):
                        if step_hour >= self.min_return_hour*3600.:
                            sum_prob_int_depart+=step_flows_dep[i]
                        if step_hour <= self.max_departure_hour*3600.:
                            sum_prob_int_arr+=step_flows_arr[i]
                    if sum_prob_int_depart > 0:
                        for step_hour, i in zip(step_hours, range(len(step_hours))):
                            if step_hour < self.min_return_hour*3600.:
                                step_flows_dep_prob[i] = 0
                        step_flows_dep_prob = step_flows_dep_prob/np.sum(step_flows_dep_prob)
                    elif  sum_prob_int_arr > 0:
                        for step_hour, i in zip(step_hours, range(len(step_hours))):
                            if step_hour > self.max_departure_hour*3600.:
                                step_flows_arr_prob[i] = 0
                        step_flows_arr_prob = step_flows_arr_prob/np.sum(step_flows_arr_prob)
                    step = np.random.choice(steps, p = step_flows_dep_prob)
                    choice_dep = choices[step]
                    step = np.random.choice(steps, p = step_flows_arr_prob)
                    choice_ret = choices[step]
                    tentative = 0
                    stop_criteria = False
                    
                        #............If return is before departure
                    while choice_ret[0]/3600. < (choice_dep[0]/3600. + self.av_dtd_time_vp/3600. + interval_time/7200.):
                        tentative += 1
                        step = np.random.choice(steps, p = step_flows_dep_prob)
                        choice_dep = choices[step]
                        step = np.random.choice(steps, p = step_flows_arr_prob)
                        choice_ret = choices[step]
                        
                        #............If the convergence is not achieved, redo the process: it might happens
                        if tentative > 1000:
                            convergenze = False
                            stop_criteria = True
                            choice_ret[0] = (choice_dep[0] + self.av_dtd_time_vp + interval_time) +1
                            print 'WARNING: convergenze not found, a new attempt will be processed. However, try to change parameters'
    
                        #............Update probabilities to force obtaining the imposed trend
                    
                    t_dep = int(choice_dep[0]+is_randomize*np.random.uniform(-time_interval_half,time_interval_half)) #max(0, int(choice_dep[0]))
                    t_ret = int(choice_ret[0]+is_randomize*np.random.uniform(-time_interval_half,time_interval_half)) #max(0, int(choice_ret[0]))
                    print '      desired: t_dep %.2f'%(float(t_dep)/3600),'t_ret %.2f'%(float(t_ret)/3600)
                    
                    if (self.is_update_plans)&(id_plan > -1):# make shure there is a valid plan
                        # travel times list, marking start end end of activities
                        
                        stagelist = plans.stagelists[id_plan]
                        tt = []
                        for stage, id_stage in stagelist:
                                if stage.ident == 'activities':
                                        print '      id_act %d: t_dep %.2f'%(id_stage, stage.times_start[id_stage]),'t_ret %.2f'%(stage.times_start[id_stage] + stage.durations[id_stage])
                                        tt += [stage.times_start[id_stage] , stage.times_start[id_stage] + stage.durations[id_stage]]
                                # break after first 3 activities have been processed
                                if len(tt) == 6:
                                        break
                        
                        if len(tt) == 6:
                                delta = [t_dep-0.5*(tt[1]+tt[2]), t_ret-0.5*(tt[3]+tt[4]) ]
                              
                                
                                # be sure there is positive time for activity 2
                                is_ok1 = tt[2] + delta[0] < tt[3] + delta[1]
                                
                                print '      delta[0]',delta[0]/3600., 'delta[1]',delta[1]/3600.,'is_ok1',is_ok1,'dur2=',(tt[3] +  delta[1] - tt[2] + delta[0])/3600
                                if is_ok1:
                                        i_act = -1
                                        for stage, id_stage in stagelist:
                                                if stage.ident == 'activities': # activity stage
                                                        time_start = stage.times_start[id_stage]
                                                        i_act += 1
                                                        
                                                        if i_act == 0:# activity stage
                                                                # adjust first activity
                                                                # only extend duration
                                                                stage.durations[id_stage] += delta[0] 
                                                                
                                                                
                                                                
                                                        elif i_act == 1:
                                                                # adjust second activity
                                                                stage.durations[id_stage] = tt[3] + delta[0] - tt[2] -  delta[1]  
                                                                stage.times_start[id_stage] += delta[0]
                                                                
                                                        else:
                                                                # for all other stages, just shift start time
                                                                stage.times_start[id_stage] += delta[1]
                                                        
                                                else: # transport stage
                                                        if  i_act in [0,1]:
                                                                stage.times_start[id_stage] += delta[i_act]
                                                        else:   
                                                                # just shift all times by the last delta
                                                                stage.times_start[id_stage] += delta[1]    
                                        
                        # debug:
                        for stage, id_stage in stagelist:
                            print '      Control stage: stage',stage.get_ident(),'id_stage',id_stage,'times_start',stage.times_start[id_stage]
                            if stage.get_ident() != 'activities':
                                if stage.times_start[id_stage] < 0:
                                    print 'ERROR: negative start time!!'
                                    #sys.exit()

                    
                    det_depart = choice_dep[0]/3600.
                    det_return = choice_ret[0]/3600.
                    step_flows_dep[choice_dep[1]] -= unit
                    step_flows_arr[choice_ret[1]] -= unit
                    if step_flows_dep[choice_dep[1]] < 0:
                        step_flows_dep[choice_dep[1]] = 0.
                    if step_flows_arr[choice_ret[1]] < 0:
                        step_flows_arr[choice_ret[1]] = 0.
                    step_flows_dep_prob = step_flows_dep/np.sum(step_flows_dep)
                    step_flows_arr_prob = step_flows_arr/np.sum(step_flows_arr)
                    
                        #............Update times of activities
                    
                    # means sleeping starts at midnight, no negative times are allowed!!
                    # anyway, sleeping will not be simulated, only stages after the first activity
                    activities.hours_begin_earliest[id_first_activity] = 0.
                    activities.hours_begin_latest[id_first_activity] = 0.05
                    
                    t_min = det_depart-self.av_dtd_time_vp/7200.-interval_time/7200.+is_randomize*np.random.uniform(-time_interval_half,time_interval_half)/3600.
                    if  t_min<= 0.:
                        activities.durations_min[id_first_activity] = 0.
                    else:
                        activities.durations_min[id_first_activity] = t_min
                
                    t_min =  det_depart-self.av_dtd_time_vp/7200.+interval_time/7200 +is_randomize*np.random.uniform(-time_interval_half,time_interval_half)/3600.
                    if t_min <= 0.:
                        activities.durations_max[id_first_activity] = 0.05
                    else:
                        activities.durations_max[id_first_activity] = t_min
                    activities.hours_begin_earliest[id_intermediate_act] = 0.
                    activities.hours_begin_latest[id_intermediate_act] = 0.
                    
                    
                    activities.durations_min[id_intermediate_act] = det_return-det_depart-self.av_dtd_time_vp/3600.-interval_time/7200.+is_randomize*np.random.uniform(-time_interval_half,time_interval_half)/3600.
                    activities.durations_max[id_intermediate_act] = det_return-det_depart-self.av_dtd_time_vp/3600.+interval_time/7200.+is_randomize*np.random.uniform(-time_interval_half,time_interval_half)/3600.
                    print '      Control act: id_first_activity',id_first_activity,'tbe=%d tbl=%d dmin =%d dmax =%d '%(activities.hours_begin_earliest[id_first_activity],activities.hours_begin_latest[id_first_activity], activities.durations_min[id_first_activity], activities.durations_max[id_first_activity] )
                    print '                   id_inter_activity',id_intermediate_act,'tbe=%d tbl=%d dmin =%d dmax =%d '%(activities.hours_begin_earliest[id_intermediate_act] , activities.hours_begin_latest[id_intermediate_act], activities.durations_min[id_intermediate_act], activities.durations_max[id_intermediate_act])
                    if activities.hours_begin_earliest[id_first_activity] + activities.durations_min[id_first_activity] < 0.0:
                        print 'ERROR: activity end time!!'
                        
                        #sys.exit()
        
        #............add return trips and Update times of trips 
        if self.is_add_returntrips & self.is_update_trips:
            step_flows = copy(step_flows0)
            step_flows_dep = copy(step_flows_dep0)
            step_flows_arr = copy(step_flows_arr0)
            
            trips = demand.trips
            ids_trips_dep = trips.get_ids()
            ids_trips_arr = trips.add_returntrips(0, ids_trip = ids_trips_dep)
            
            ids_trip = trips.get_ids() # all trips

            steps = range(len(step_hours))
            choices = []
            for step, step_hour in zip(steps, step_hours):
                choices.append([step_hour,step])
            unit = np.sum(step_flows_dep+step_flows_arr)/(len(ids_trip)*2.)
            
            for id_trip in ids_trips_dep:
                
                #............Extract departure and return time
                step_flows_prob = step_flows_dep/np.sum(step_flows_dep)
                step = np.random.choice(steps, p = step_flows_prob)
                choice = choices[step]
                
                #............Update probabilities to force obtaining the imposed trend
                step_flows_dep[choice[1]] -= unit
                if step_flows_dep[choice[1]] < 0:
                    step_flows_dep[choice[1]] = 0.
                step_flows_prob = step_flows_dep/np.sum(step_flows_dep)
                
                #............Update times of trips
                trips.times_depart[id_trip]    = (np.random.randint(choice[0]-interval_time/2.,choice[0]+interval_time/2.,1)-self.av_dtd_time_trips/2.)
                if trips.times_depart[id_trip] < 0:
                    trips.times_depart[id_trip] = 0.
                    
            for id_trip in ids_trips_arr:
                
                #............Extract departure and return time
                step_flows_prob = step_flows_arr/np.sum(step_flows_arr)
                step = np.random.choice(steps, p = step_flows_prob)
                choice = choices[step]
                
                #............Update probabilities to force obtaining the imposed trend
                step_flows_arr[choice[1]] -= unit
                if step_flows_arr[choice[1]] < 0:
                    step_flows_arr[choice[1]] = 0.
                step_flows_prob = step_flows_arr/np.sum(step_flows_arr)
                
                #............Update times of trips
                trips.times_depart[id_trip]    = (np.random.randint(choice[0]-interval_time/2.,choice[0]+interval_time/2.,1)-self.av_dtd_time_trips/2.)
                if trips.times_depart[id_trip] < 0:
                    trips.times_depart[id_trip] = 0.
                
                
                
        elif self.is_update_trips:
                #............Only Update times of existing trips
            trips = demand.trips
            ids_trip = trips.get_ids()
            
                #............Preparation
            step_flows = []
            for step_hour in step_hours:
                step_flow = np.sum(det_flows[(det_hours == step_hour)])
                step_flows.append(step_flow)
            steps = range(len(step_hours))
            choices = []
            for step, step_hour in zip(steps, step_hours):
                choices.append([step_hour,step])
            unit = np.sum(step_flows)/len(ids_trip)
            for id_trip in ids_trip:
                
                #............Extract departure and return time
                step_flows_prob = step_flows/np.sum(step_flows)
                step = np.random.choice(steps, p = step_flows_prob)
                choice = choices[step]
                
                #............Update probabilities to force obtaining the imposed trend
                step_flows[choice[1]] -= unit
                if step_flows[choice[1]] < 0:
                    step_flows[choice[1]] = 0.
                step_flows_prob = step_flows/np.sum(step_flows)
                
                #............Update times of trips
                trips.times_depart[id_trip]    = (np.random.randint(choice[0]-interval_time/2.,choice[0]+interval_time/2.,1)-self.av_dtd_time_trips/2.)
                if trips.times_depart[id_trip] < 0:
                    trips.times_depart[id_trip] = 0.



        return True
