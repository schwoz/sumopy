
import numpy as np
from numpy import random
import agilepy.lib_base.classman as cm
import agilepy.lib_base.arrayman as am
import agilepy.lib_base.xmlman as xm
#from coremodules.modules_common import *
from coremodules.network.network import SumoIdsConf, MODES
from coremodules.network import routing
from agilepy.lib_base.processes import Process, CmlMixin
#import coremodules.demand.demand as dm
import demand as dm
import demandbase as db
#print 'dir(dm)',dir(dm)
#from demand import OPTIONMAP_POS_DEPARTURE
#OPTIONMAP_POS_ARRIVAL
#OPTIONMAP_SPEED_DEPARTURE
#OPTIONMAP_SPEED_ARRIVAL
#OPTIONMAP_LANE_DEPART
#OPTIONMAP_LANE_ARRIVAL


class SumoOdTripgenerator(Process):
    def __init__(self, odintervals, trips, logger=None, **kwargs):
        """
        CURRENTLY NOT IN USE!!
        """
        self._init_common('odtripgenerator', name='OD tripgenerator',
                          logger=logger,
                          info='Generates trips from OD demand .',
                          )
        self._odintervals = odintervals

        attrsman = self.get_attrsman()
        self.add_option('netfilepath', netfilepath,
                        # this will make it show up in the dialog
                        groupnames=['options'],
                        cml='--sumo-net-file',
                        perm='rw',
                        name='Net file',
                        wildcards='Net XML files (*.net.xml)|*.net.xml',
                        metatype='filepath',
                        info='SUMO Net file in XML format.',
                        )

        self.workdirpath = attrsman.add(cm.AttrConf('workdirpath', rootdirpath,
                                                    # ['options'],#['_private'],
                                                    groupnames=['_private'],
                                                    perm='r',
                                                    name='Workdir',
                                                    metatype='dirpath',
                                                    info='Working directory for this scenario.',
                                                    ))

        self.rootname = attrsman.add(cm.AttrConf('rootname', rootname,
                                                 groupnames=['_private'],
                                                 perm='r',
                                                 name='Scenario shortname',
                                                 info='Scenario shortname is also rootname of converted files.',
                                                 ))

        self.is_clean_nodes = attrsman.add(cm.AttrConf('is_clean_nodes', is_clean_nodes,
                                                       groupnames=['options'],
                                                       perm='rw',
                                                       name='Clean Nodes',
                                                       info='If set, then shapes around nodes are cleaned up.',
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
        self.update_params()
        cml = self.get_cml()+' --plain-output-prefix ' + \
            filepathlist_to_filepathstring(
                os.path.join(self.workdirpath, self.rootname))
        #print 'SumonetImporter.do',cml
        #import_xml(self, rootname, dirname, is_clean_nodes = True)
        self.run_cml(cml)
        if self.status == 'success':
            self._net.import_xml(
                self.rootname, self.workdirpath, is_clean_nodes=self.is_clean_nodes)
            return True
        else:
            return False
        #print 'do',self.newident
        #self._scenario = Scenario(  self.newident,
        #                                parent = None,
        #                                workdirpath = self.workdirpath,
        #                                logger = self.get_logger(),
        #                                )

    def get_net(self):
        return self._net


      
class OdFlowTable(am.ArrayObjman):
    def __init__(self, parent, modes, zones, activitytypes=None, **kwargs):
            self._init_objman(ident='odflowtab', parent=parent,
                              name='OD flows',
                              info='Table with intervals, modes, OD and respective number of trips.',
                              #xmltag = ('odtrips','odtrip',None),
                              **kwargs)

            self.add_col(am.ArrayConf('times_start', 0,
                                      groupnames=['parameters'],
                                      perm='r',
                                      name='Start time',
                                      unit='s',
                                      info='Start time of interval in seconds (no fractional seconds).',
                                      xmltag='t_start',
                                      ))

            self.add_col(am.ArrayConf('times_end', 3600,
                                      groupnames=['parameters'],
                                      perm='r',
                                      name='End time',
                                      unit='s',
                                      info='End time of interval in seconds (no fractional seconds).',
                                      xmltag='t_end',
                                      ))

            self.add_col(am.IdsArrayConf('ids_mode', modes,
                                         groupnames=['parameters'],
                                         perm='r',
                                         #choices = MODES,
                                         name='ID mode',
                                         xmltag='vClass',
                                         info='ID of transport mode.',
                                         ))

            self.add_col(am.IdsArrayConf('ids_orig', zones,
                                         groupnames=['parameters'],
                                         name='Orig.',
                                         perm='r',
                                         #choices =  zones.ids_sumo.get_indexmap(),
                                         info='traffic assignment zone of origin of trip.',
                                         xmltag='id_orig',
                                         ))

            self.add_col(am.IdsArrayConf('ids_dest', zones,
                                         groupnames=['parameters'],
                                         name='Dest.',
                                         perm='r',
                                         #choices =  zones.ids_sumo.get_indexmap(),
                                         info='ID of traffic assignment zone of destination of trip.',
                                         xmltag='id_dest',
                                         ))

            self.add_col(am.ArrayConf('tripnumbers', 0,
                                      groupnames=['state'],
                                      perm='rw',
                                      name='Trips',
                                      info='Number of trips from zone with ID Orig to zone with ID Dest.',
                                      xmltag='tripnumber',
                                      ))

            if activitytypes is not None:
                    self.add_col(am.IdsArrayConf('ids_activitytype_orig', activitytypes,
                                                 groupnames=['parameters'],
                                                 perm='rw',
                                                 #choices = activitytypes.names.get_indexmap(),
                                                 name='Activity type at orig.',
                                                 symbol='Act. orig.',
                                                 info='Type of activity performed at origin, before the trip.',
                                                 ))

                    self.add_col(am.IdsArrayConf('ids_activitytype_dest', activitytypes,
                                                 groupnames=['parameters'],
                                                 perm='rw',
                                                 #choices = activitytypes.names.get_indexmap(),
                                                 name='Activity type at dest.',
                                                 symbol='Act. dest.',
                                                 info='Type of activity performed at destination, after the trip.',
                                                 ))
            #self.add( cm.ObjConf( zones, is_child = False,groups = ['_private']))

    def add_flows(self,  time_start,
                  time_end,
                  id_mode,
                  ids_orig,
                  ids_dest,
                  tripnumbers,
                  id_activitytype_orig=1,
                  id_activitytype_dest=1,
                  ):
        n = len(tripnumbers)
        self.add_rows(n=n,
                      times_start=time_start*np.ones(n),
                      times_end=time_end*np.ones(n),
                      ids_mode=id_mode*np.ones(n),
                      ids_orig=ids_orig,
                      ids_dest=ids_dest,
                      tripnumbers=tripnumbers,
                      ids_activitytype_orig=id_activitytype_orig*np.ones(n),
                      ids_activitytype_dest=id_activitytype_dest*np.ones(n),
                      )


class OdTrips(am.ArrayObjman):
    def __init__(self, ident, parent, zones, **kwargs):
            self._init_objman(ident, parent=parent,
                              name='OD trips',
                              info='Contains the number of trips between an origin and a destination zone.',
                              version=0.2,
                              xmltag=('odtrips', 'odtrip', None), **kwargs)

            self._init_attributes(zones)

    def _init_attributes(self, zones=None):
            #print '_init_attributes',self.ident
            if not self.has_attrname('zones'):
                self.add(cm.ObjConf(
                    zones, is_child=False, groups=['_private']))
            else:
                # zones is already an attribute
                zones = self.zones.get_value()

            if self.get_version() < 0.1:
                # update attrs from previous
                # IdsArrayConf not yet modifiable interactively, despite perm = 'rw',!!!
                self.ids_orig.set_perm('rw')
                self.ids_dest.set_perm('rw')

            if hasattr(self, 'func_delete_row'):
                self.func_make_row._is_returnval = False
                self.func_delete_row._is_returnval = False

            self.add_col(am.IdsArrayConf('ids_orig', zones,
                                         groupnames=['state'],
                                         perm='rw',
                                         name='Orig.',
                                         #choices =  zones.ids_sumo.get_indexmap(),
                                         info='traffic assignment zone of origin of trip.',
                                         xmltag='id_orig',
                                         ))

            self.add_col(am.IdsArrayConf('ids_dest', zones,
                                         groupnames=['state'],
                                         perm='rw',
                                         name='Dest.',
                                         #choices =  zones.ids_sumo.get_indexmap(),
                                         info='ID of traffic assignment zone of destination of trip.',
                                         xmltag='id_dest',
                                         ))

            self.add_col(am.ArrayConf('tripnumbers', 0,
                                      groupnames=['state'],
                                      perm='rw',
                                      name='Trips',
                                      info='Number of trips from zone with ID Orig to zone with ID Dest.',
                                      xmltag='tripnumber',
                                      ))

            #print '  pre add func_make_row'
            self.add(cm.FuncConf('func_make_row', 'on_add_row', None,
                                 groupnames=['rowfunctions', '_private'],
                                 name='New OD flow.',
                                 info='Add a new OD flow.',
                                 is_returnval=False,
                                 ))
            #print '  post add func_make_row'
            self.add(cm.FuncConf('func_delete_row', 'on_del_row', None,
                                 groupnames=['rowfunctions', '_private'],
                                 name='Del OD flow',
                                 info='Delete OD flow.',
                                 is_returnval=False,
                                 ))

            #print '  _init_attributes done',self.ident

    def _init_constants(self):
        #self.edgeweights_orig = None
        #self.edgeweights_dest = None
        pass

    def on_del_row(self, id_row=None):
        if id_row is not None:
            #print 'on_del_row', id_row
            self.del_row(id_row)

    def on_add_row(self, id_row=None):
        print 'on_add_row'
        if len(self) > 0:

            # copy previous
            od_last = self.get_row(self.get_ids()[-1])
            #id_orig = self.odtab.ids_orig.get(id_last)
            #id_dest = self.odtab.ids_dest.get(id_last)
            #id = self.suggest_id()
            self.add_row(**od_last)
        else:
            self.add_row(self.suggest_id())

    def generate_odflows(self, odflowtab,  time_start, time_end, id_mode, **kwargs):
        """
        Insert all od flows in odflowtab.
        """
        #for id_od in self.get_ids():
        odflowtab.add_flows(time_start,
                            time_end,
                            id_mode,
                            self.ids_orig.get_value(),
                            self.ids_dest.get_value(),
                            self.tripnumbers.get_value(),
                            **kwargs
                            )

    def generate_trips(self, demand, time_start, time_end, id_mode_primary,
                       id_mode_fallback = -1,
                       pos_depart_default=db.OPTIONMAP_POS_DEPARTURE['random_free'],
                       #pos_arrival_default = db.OPTIONMAP_POS_ARRIVAL['max'],
                       pos_arrival_default=db.OPTIONMAP_POS_ARRIVAL['random'],
                       speed_depart_default=0.0,
                       speed_arrival_default=0.0,
                       # pedestrians always depart on lane 0
                       ind_lane_depart_default=db.OPTIONMAP_LANE_DEPART['allowed'],
                       # pedestrians always arrive on lane 0
                       ind_lane_arrival_default=db.OPTIONMAP_LANE_ARRIVAL['current'],
                       n_trials_connect=5,
                       is_make_route=True,
                       priority_max = 10,
                       speed_max = 14.0,
                       n_edges_min_length = 1,
                       n_edges_max_length = 500,
                       ):
        """
        Generates trips in demand.trip table.
        """
        print 'generate_trips', time_start, time_end, 'id_mode_primary',id_mode_primary,'id_mode_fallback',id_mode_fallback
        #MODES['passenger'],'ind_lane_arrival_default',ind_lane_arrival_default,'ind_lane_depart_default',ind_lane_depart_default
        id_mode_ped = MODES['pedestrian']
        #OPTIONMAP_POS_DEPARTURE = { -1:"random",-2:"free",-3:"random_free",-4:"base"}
        #OPTIONMAP_POS_ARRIVAL = { -1:"random",-2:"max"}
        #OPTIONMAP_SPEED_DEPARTURE = { -1:"random",-2:"max"}
        #OPTIONMAP_SPEED_ARRIVAL = { -1:"current"}
        #OPTIONMAP_LANE_DEPART = {-1:"random",-2:"free",-3:"departlane"}
        #OPTIONMAP_LANE_ARRIVAL = { -1:"current"}

        trips = demand.trips
        
        # define primary and secondary mode, if appropriate
        # in case there is a secondary mode, the secondary mode is chosen 
        ids_vtype_mode_primary, prob_vtype_mode_primary = demand.vtypes.select_by_mode(
            id_mode_primary, is_share = True)
        #print '  ids_vtype_mode', ids_vtype_mode
        n_vtypes_primary = len(ids_vtype_mode_primary)
        
        if (id_mode_primary == MODES['passenger']) & (id_mode_fallback not in  [-1,MODES['passenger']]):
            ids_vtype_mode_fallback, prob_vtype_mode_fallback = demand.vtypes.select_by_mode(
                id_mode_fallback, is_share = True)
            #print '  ids_vtype_mode_fallback', ids_vtype_mode_fallback
            n_vtypes_fallback = len(ids_vtype_mode_fallback)
            is_fallback = True
        else:
            ids_vtype_mode_fallback = []
            id_mode_fallback = -1
            is_fallback = False
        
        zones = self.zones.get_value()
        
        # update edge probabilities with suitable parameters
        # TODO: edge probabilities should no longer be an attribute
        # of zones but generate 
        for id_zone in zones.get_ids():
            zones.make_egdeprobs(id_zone, n_edges_min_length, n_edges_max_length, priority_max, speed_max)
            
        edges = zones.ids_edges_orig.get_linktab()
        edgelengths = edges.lengths

        if n_trials_connect > 0:
            # initialize routing to verify connection
            #print '  prepare routing'
            fstar = edges.get_fstar(is_ignor_connections=False)
            times_primary = edges.get_times(id_mode=id_mode_primary, is_check_lanes=True)
            times_fallback = edges.get_times(id_mode=id_mode_fallback, is_check_lanes=True)


        n_trips_generated = 0
        n_trips_failed = 0

        is_nocon = False
        route = []
        for id_od in self.get_ids():
            id_orig = self.ids_orig[id_od]
            id_dest = self.ids_dest[id_od]
            tripnumber = self.tripnumbers[id_od]
            print '  generate',tripnumber,' trips from id_zone',id_orig,'to id_zone',id_dest
            ids_edges_orig_raw = zones.ids_edges_orig[id_orig]
            ids_edges_dest_raw = zones.ids_edges_dest[id_dest]

            prob_edges_orig_raw = zones.probs_edges_orig[id_orig]
            prob_edges_dest_raw = zones.probs_edges_dest[id_dest]
            #print '    prob_edges_orig_raw',prob_edges_orig_raw
            #print '    prob_edges_dest_raw',prob_edges_dest_raw
            # check accessibility of origin edges
            ids_edges_orig = []
            prob_edges_orig = []
            inds_lane_orig = []
            are_fallback_orig = []
            for i in xrange(len(ids_edges_orig_raw)):
                id_edge = ids_edges_orig_raw[i]
                # if check accessibility...
                ind_lane_depart = edges.get_laneindex_allowed(id_edge, id_mode_primary)
                #print '    O get_laneindex_allowed id_mode_primary',id_mode_primary,id_edge,edges.ids_sumo[id_edge],'ind_lane',ind_lane_depart
                if ind_lane_depart >= 0:
                    ids_edges_orig.append(id_edge)
                    prob_edges_orig.append(prob_edges_orig_raw[i])
                    are_fallback_orig.append(False)
                    #print '    ind_lane_depart',ind_lane_depart,'ind_lane_depart_default',ind_lane_depart_default
                    if ind_lane_depart_default >= 0:
                        inds_lane_orig.append(ind_lane_depart)
                    else:
                        inds_lane_orig.append(ind_lane_depart_default)
                
                elif is_fallback:
                    #print '    !!access of primary mode failed, try fallback'
                    ind_lane_depart = edges.get_laneindex_allowed(id_edge, id_mode_fallback)
                    #print '    O get_laneindex_allowed id_mode_fallback',id_mode_fallback,id_edge,edges.ids_sumo[id_edge],'ind_lane',ind_lane_depart
                    if ind_lane_depart >= 0:
                        ids_edges_orig.append(id_edge)
                        prob_edges_orig.append(prob_edges_orig_raw[i])
                        are_fallback_orig.append(True)
                        #print '    ind_lane_depart',ind_lane_depart,'ind_lane_depart_default',ind_lane_depart_default
                        if ind_lane_depart_default >= 0:
                            inds_lane_orig.append(ind_lane_depart)
                        else:
                            inds_lane_orig.append(ind_lane_depart_default)

            # check accessibility of destination edges
            ids_edges_dest = []
            prob_edges_dest = []
            inds_lane_dest = []
            are_fallback_dest = []
            for i in xrange(len(ids_edges_dest_raw)):
                id_edge = ids_edges_dest_raw[i]
                # if check accessibility...
                ind_lane_arrival = edges.get_laneindex_allowed(
                    id_edge, id_mode_primary)
                #print '    D get_laneindex_allowed id_mode_primary',id_mode_primary,id_edge,edges.ids_sumo[id_edge],'ind_lane',ind_lane_arrival
                if ind_lane_arrival >= 0:
                    ids_edges_dest.append(id_edge)
                    are_fallback_dest.append(False)
                    prob_edges_dest.append(prob_edges_dest_raw[i])
                    #print '    ind_lane_arrival',ind_lane_arrival,'ind_lane_arrival_default',ind_lane_arrival_default
                    if ind_lane_arrival_default >= 0:
                        inds_lane_dest.append(ind_lane_arrival)
                    else:
                        inds_lane_dest.append(ind_lane_arrival_default)
                elif is_fallback:
                    #print '    !!access of primary mode failed, try fallback'
                    ind_lane_arrival = edges.get_laneindex_allowed(
                        id_edge, id_mode_fallback)
                    #print '    D get_laneindex_allowed id_mode_fallback',id_mode_primary,id_edge,edges.ids_sumo[id_edge],'ind_lane',ind_lane_arrival
                    if ind_lane_arrival >= 0:
                        ids_edges_dest.append(id_edge)
                        are_fallback_dest.append(True)
                        prob_edges_dest.append(prob_edges_dest_raw[i])
                        #print '    ind_lane_arrival',ind_lane_arrival,'ind_lane_arrival_default',ind_lane_arrival_default
                        if ind_lane_arrival_default >= 0:
                            inds_lane_dest.append(ind_lane_arrival)
                        else:
                            inds_lane_dest.append(ind_lane_arrival_default)
                        
            n_edges_orig = len(ids_edges_orig)
            n_edges_dest = len(ids_edges_dest)
            
            #print '\n    found',n_edges_orig,n_edges_dest,'edges'
            
            if (n_edges_orig > 0) & (n_edges_dest > 0) & (tripnumber > 0):
                # renormalize weights
                prob_edges_orig = np.array(prob_edges_orig, np.float)
                prob_edges_orig = prob_edges_orig/np.sum(prob_edges_orig)
                prob_edges_dest = np.array(prob_edges_dest, np.float)
                prob_edges_dest = prob_edges_dest/np.sum(prob_edges_dest)
                #print '    prob_edges_orig',prob_edges_orig
                #print '    prob_edges_dest',prob_edges_dest
            

                for d in xrange(int(tripnumber+0.5)):
                    #print '      ------------'
                    #print '      generte trip',d
                    time_depart = random.uniform(time_start, time_end)
                    
                    
                    

                    
                    if (n_trials_connect > 0) & (id_mode_primary != id_mode_ped):
                        # check if origin and destination edges are connected
                        n = n_trials_connect
                        is_nocon = True
                        is_force_fallback = False
                        
            
                        while (n > 0) & is_nocon:
                            # this algorithm can be improved by calculating
                            # the minimum cost tree and checking all destinations
                            i_orig = np.argmax(random.rand(
                                n_edges_orig)*prob_edges_orig)
                            id_edge_orig = ids_edges_orig[i_orig]
                            i_dest = np.argmax(random.rand(
                                n_edges_dest)*prob_edges_dest)
                            id_edge_dest = ids_edges_dest[i_dest]
                            
                        
                            if is_fallback & (is_force_fallback | are_fallback_orig[i_orig] | are_fallback_dest[i_dest]):
                                #print '        fallback to id_vtype',ids_vtype_mode_fallback,'is_force_fallback',is_force_fallback,'fallback_orig',are_fallback_orig[i_orig],'fallback_dest',are_fallback_dest[i_dest]
                                id_mode = id_mode_fallback
                                ids_vtype_mode =ids_vtype_mode_fallback
                                prob_vtype_mode = prob_vtype_mode_fallback
                                n_vtypes = n_vtypes_fallback
                                times = times_fallback
                            else:
                                #print '        primary id_vtype',ids_vtype_mode_fallback
                                id_mode = id_mode_primary
                                ids_vtype_mode =ids_vtype_mode_primary
                                prob_vtype_mode = prob_vtype_mode_primary
                                n_vtypes = n_vtypes_primary
                                times = times_primary

                            cost, route = routing.get_mincostroute_edge2edge(id_edge_orig,
                                                                             id_edge_dest,
                                                                             weights=times,# mode dependent!
                                                                             fstar=fstar
                                                                             )
                            is_nocon = len(route) == 0
                            n -= 1
                            
                            #print '      trials left',n,'is_nocon',is_nocon,'id_mode',id_mode,'id_mode_primary',id_mode_primary,'is_force_fallback',is_force_fallback
                            
                            # try fallback mode
                            if (n == 0) & is_fallback & is_nocon & (id_mode == id_mode_primary):
                                print '        force fallback'
                                # from now on force mode to be fallback
                                is_force_fallback = True
                                n = n_trials_connect
                                
                        
                        #print '      found route with length',len(route),'trial number',n_trials_connect-n,'is_nocon',is_nocon
                        if not is_make_route:
                            route = []
                    else:
                        # no check if origin and destination edges are connected
                        is_nocon = False
                        i_orig = np.argmax(random.rand(
                            n_edges_orig)*prob_edges_orig)
                        id_edge_orig = ids_edges_orig[i_orig]

                        i_dest = np.argmax(random.rand(
                            n_edges_dest)*prob_edges_dest)
                        id_edge_dest = ids_edges_dest[i_dest]
                        
                        if (are_fallback_dest[i_dest] | are_fallback_dest[i_dest]):
                            #print '        fallback to type',ids_vtype_mode_fallback 
                            id_mode = id_mode_fallback
                            ids_vtype_mode =ids_vtype_mode_fallback
                            prob_vtype_mode = prob_vtype_mode_fallback
                            n_vtypes = n_vtypes_fallback
   
                        else:
                            id_mode = id_mode_primary
                            ids_vtype_mode =ids_vtype_mode_primary
                            prob_vtype_mode = prob_vtype_mode_primary
                            n_vtypes = n_vtypes_primary

                    if not is_nocon:
                        # actually create trip with all parameters
                        ind_lane_orig = inds_lane_orig[i_orig]
                        ind_lane_dest = inds_lane_dest[i_dest]

                        pos_depart = pos_depart_default
                        pos_arrival = pos_arrival_default
                        #print '  bef:pos_depart,pos_arrival,id_mode,id_mode_ped',  pos_depart,pos_arrival,id_mode,id_mode_ped
                        if id_mode_ped == id_mode:
                            # persons do not understand "random", "max" etc
                            # so produce a random number here

                            #{ -1:"random",-2:"free",-3:"random_free",-4:"base"}
                            edgelength = edgelengths[id_edge_orig]
                            #if pos_depart in (-1, -2, -3):
                            #    pos_depart = random.uniform(
                            #        0.1*edgelength, 0.9*edgelength, 1)[0]
                            
                            if pos_depart >= 0:
                                pos_depart = 0.1*edgelength

                            # { -1:"random",-2:"max"}
                            edgelength = edgelengths[id_edge_dest]
                            #if pos_arrival == -1:
                            #    pos_arrival = random.uniform(
                            #        0.1*edgelength, 0.9*edgelength, 1)[0]
                            if pos_arrival >= 0:
                                pos_arrival = 0.9*edgelength
                        #print '  af:pos_depart,pos_arrival,id_mode,id_mode_ped',  pos_depart,pos_arrival,id_mode,id_mode_ped
                        #print '  n_vtypes',n_vtypes
                        #print '  random.randint(n_vtypes)',random.randint(n_vtypes)
                        #id_vtype = ids_vtype_mode[random.randint(n_vtypes)]
                        id_vtype = ids_vtype_mode[np.argmax(
                            random.rand(n_vtypes)*prob_vtype_mode)]
                        id_trip = trips.make_trip(id_vtype=id_vtype,
                                                  time_depart=time_depart,
                                                  id_edge_depart=id_edge_orig,
                                                  id_edge_arrival=id_edge_dest,
                                                  ind_lane_depart=ind_lane_orig,
                                                  ind_lane_arrival=ind_lane_dest,
                                                  position_depart=pos_depart,
                                                  position_arrival=pos_arrival,
                                                  speed_depart=speed_depart_default,
                                                  speed_arrival=speed_arrival_default,
                                                  route=route,
                                                  )
                        #print '  ',id_trip,id_edge_orig,edges.ids_sumo[id_edge_orig],ind_lane_depart
                        #print '  ',id_trip,self.position_depart[id_trip],
                        n_trips_generated += 1
                        #print '      generated trip',d,'total gen.',n_trips_generated,'route length',len(route)
                    
                    else:
                        #print '  no connected trip found'
                        n_trips_failed += 1
            else:
                print '  no connected trip found'
                n_trips_failed += tripnumber

        print '  n_trips_generated', n_trips_generated
        print '  n_trips_failed', n_trips_failed

    def add_od_trips(self, scale, names_orig, names_dest, tripnumbers):
        print 'OdTrips.add_od_trips'
        #print '  scale, names_orig, names_dest, tripnumbers',scale, names_orig, names_dest, tripnumbers,len(tripnumbers)
        zones = self.get_zones()

        for name_orig, name_dest, tripnumber in zip(names_orig, names_dest, tripnumbers):
            #print '  check',name_orig, name_dest, tripnumbers,zones.ids_sumo.has_index(name_orig),zones.ids_sumo.has_index(name_dest)
            if (zones.ids_sumo.has_index(name_orig)) & (zones.ids_sumo.has_index(name_dest)):
                print '  add', zones.ids_sumo.get_id_from_index(
                    name_orig), zones.ids_sumo.get_id_from_index(name_dest)
                
                ###-----
                n_trips_scale = float(scale * tripnumber)
                n_trips_scale_int = int(n_trips_scale)
                n_trips_scale_dec = float(n_trips_scale - n_trips_scale_int)
                n_random = random.random()
                if n_random > n_trips_scale_dec:
                    n_trips_scale_fin = int(n_trips_scale_int)
                else:
                    n_trips_scale_fin = int(n_trips_scale_int + 1)
                ###-----
                
                self.add_row(ids_orig=zones.ids_sumo.get_id_from_index(name_orig),
                             ids_dest=zones.ids_sumo.get_id_from_index(
                                 name_dest),
                             tripnumbers= n_trips_scale_fin) #prima c'era (tripnumbers = scale*tripnumber)
            else:
                print '  WARNING: zone named %s or %s not known' % (
                    name_orig, names_dest)
                print '  zones indexmap', zones.get_indexmap()
                print '  ids_sumo', zones.ids_sumo.get_value()
                print '  ids_sumo._index_to_id', zones.ids_sumo._index_to_id

    def get_zones(self):
        return self.ids_dest.get_linktab()


class OdModes(am.ArrayObjman):
    def __init__(self, ident, parent, modes, zones, **kwargs):
            self._init_objman(ident, parent=parent,
                              name='Mode OD tables',
                              info='Contains for each transport mode an OD trip table.',
                              xmltag=('modesods', 'modeods', 'ids_mode'), **kwargs)

            self.add_col(am.IdsArrayConf('ids_mode', modes,
                                         groupnames=['state'],
                                         choices=MODES,
                                         name='ID mode',
                                         xmltag='vClass',
                                         info='ID of transport mode.',
                                         ))

            self.add_col(cm.ObjsConf('odtrips',
                                     groupnames=['state'],
                                     is_save=True,
                                     name='OD matrix',
                                     info='Matrix with trips from origin to destintion for a specific mode.',
                                     ))

            self.add(cm.ObjConf(zones, is_child=False, groups=['_private']))

    def generate_trips(self, demand, time_start, time_end, **kwargs):
        for id_od_mode in self.get_ids():
            self.odtrips[id_od_mode].generate_trips(
                demand, time_start, time_end, self.ids_mode[id_od_mode], **kwargs)

    def generate_odflows(self, odflowtab, time_start, time_end, **kwargs):
        for id_od_mode in self.get_ids():
            self.odtrips[id_od_mode].generate_odflows(
                odflowtab, time_start, time_end, self.ids_mode[id_od_mode], **kwargs)

    def add_od_trips(self, id_mode, scale, names_orig, names_dest, tripnumbers):
        #print 'OdModes.add_od_trips',id_mode, scale, names_orig, names_dest, tripnumbers
        ids_mode = self.select_ids(self.ids_mode.get_value() == id_mode)
        if len(ids_mode) == 0:
            id_od_modes = self.add_row(ids_mode=id_mode)
            #print '  create',id_od_modes
            odtrips = OdTrips((self.odtrips.attrname, id_od_modes),
                              self, self.zones.get_value())
            self.odtrips[id_od_modes] = odtrips
            odtrips.add_od_trips(scale, names_orig, names_dest, tripnumbers)
            return odtrips
        else:
            id_od_modes = ids_mode[0]  # modes are unique
            #print '  use',id_od_modes
            self.odtrips[id_od_modes].add_od_trips(
                scale, names_orig, names_dest, tripnumbers)
            return self.odtrips[id_od_modes]


class OdIntervals(am.ArrayObjman):
    def __init__(self, ident='odintervals',  parent=None, net=None, zones=None, **kwargs):
            self._init_objman(ident, parent=parent,  # = demand
                              name='OD Demand',
                              info='Contains origin-to-destination zone transport demand for different time intervals.',
                              xmltag=('odintervals', 'odinteval', None), **kwargs)

            self.add_col(am.ArrayConf('times_start', 0,
                                      groupnames=['state'],
                                      perm='rw',
                                      name='Start time',
                                      unit='s',
                                      info='Start time of interval in seconds (no fractional seconds).',
                                      xmltag='t_start',
                                      ))

            self.add_col(am.ArrayConf('times_end', 3600,
                                      groupnames=['state'],
                                      perm='rw',
                                      name='End time',
                                      unit='s',
                                      info='End time of interval in seconds (no fractional seconds).',
                                      xmltag='t_end',
                                      ))

            activitytypes = self.parent.activitytypes
            self.add_col(am.IdsArrayConf('ids_activitytype_orig', activitytypes,
                                         groupnames=['parameters'],
                                         perm='rw',
                                         #choices = activitytypes.names.get_indexmap(),
                                         name='Activity type at orig.',
                                         symbol='Act. orig.',
                                         info='Type of activity performed at origin, before the trip.',
                                         #xmltag = 'actType',
                                         #xmlmap = get_inversemap( activitytypes.names.get_indexmap()),
                                         ))

            self.add_col(am.IdsArrayConf('ids_activitytype_dest', activitytypes,
                                         groupnames=['parameters'],
                                         perm='rw',
                                         #choices = activitytypes.names.get_indexmap(),
                                         name='Activity type at dest.',
                                         symbol='Act. dest.',
                                         info='Type of activity performed at destination, after the trip.',
                                         #xmltag = 'actType',
                                         #xmlmap = get_inversemap( activitytypes.names.get_indexmap()),
                                         ))

            self.add_col(cm.ObjsConf('odmodes',
                                     groupnames=['state'],
                                     is_save=True,
                                     name='OD modes',
                                     info='OD transport demand for all transport modes within the respective time interval.',
                                     ))
            self.add(cm.ObjConf(net, is_child=False, groups=['_private']))
            self.add(cm.ObjConf(zones, is_child=False, groups=['_private']))
            #print 'OdIntervals.__init__',self,dir(self)

    def generate_trips(self, is_refresh_zoneedges=True, **kwargs):
        """
        Generates trips in trip table.
        """
        if is_refresh_zoneedges:
            # make sure zone edges are up to date
            self.get_zones().refresh_zoneedges()
        demand = self.parent
        for id_inter in self.get_ids():
            self.odmodes[id_inter].generate_trips(demand,   self.times_start[id_inter],
                                                  self.times_end[id_inter],
                                                  **kwargs)
   
    def generate_odflows(self, **kwargs):
        """
        Generates a flat table with all OD flows.
        """
        odflowtab = OdFlowTable(self, self.get_modes(),
                                self.get_zones(), self.get_activitytypes())
        for id_inter in self.get_ids():
            self.odmodes[id_inter].generate_odflows(odflowtab,
                                                    self.times_start[id_inter],
                                                    self.times_end[id_inter],
                                                    id_activitytype_orig=self.ids_activitytype_orig[id_inter],
                                                    id_activitytype_dest=self.ids_activitytype_dest[id_inter],
                                                    **kwargs)
        return odflowtab
    
    
    
        
    def write_xml(self, fd=None, indent = 0):
        ft = self.generate_odflows()
        scenario = self.parent.parent
        ids_zone_sumo = scenario.landuse.zones.ids_sumo
        get_vtype_for_mode = scenario.demand.vtypes.get_vtype_for_mode
        ids = ft.get_ids()
        fd.write(xm.begin('trips',indent))
        self.parent.vtypes.write_xml(   fd, indent=indent,
                                        #ids = ids_vtype_selected,
                                        is_print_begin_end = False)
                                        
        for id_flow, time_start, time_end, id_mode, id_orig_sumo, id_dest_sumo, tripnumber in zip(\
                ids, ft.times_start[ids], ft.times_end[ids], ft.ids_mode[ids], 
                ids_zone_sumo[ft.ids_orig[ids]], ids_zone_sumo[ft.ids_dest[ids]], 
                ft.tripnumbers[ids]):
        
            # <flow id="f" begin="0" end="100" number="23" fromTaz="taz1" toTaz="taz2"/>

            
            fd.write(xm.start('flow',indent + 2))
            fd.write(xm.num('id',id_flow))
            fd.write(xm.num('begin',time_start))
            fd.write(xm.num('end',time_end))
            fd.write(xm.num('number',tripnumber))
            
            fd.write(xm.num('fromTaz',id_orig_sumo))
            fd.write(xm.num('toTaz',id_dest_sumo))
            fd.write(xm.num('type',get_vtype_for_mode(id_mode=id_mode, is_sumoid = True))) 
              
            fd.write(xm.stopit())
            
        fd.write(xm.end('trips',indent))
    
    def get_flowfilepath(self):
        return self.parent.parent.get_rootfilepath()+'.flow.xml'
    
    def get_amitranfilepath(self):
        return self.parent.parent.get_rootfilepath()+'.ami.xml'
    
    def export_amitranxml(self, filepath=None, encoding = 'UTF-8'):
        """
        Export flows to Amitran format that defines the demand per OD pair in time slices for every vehicle type.
        """
        print 'export_amitranxml',filepath,len(self)
        
       
        
        if len(self)==0: return None
        
        if filepath is None:
            filepath = self.get_amitranfilepath()
        
        try:
            fd=open(filepath,'w')
        except:
            print 'WARNING in export_sumoxml: could not open',filepath
            return False
        
        indent = 0

        ft = self.generate_odflows()
        scenario = self.parent.parent
        ids_zone_sumo = scenario.landuse.zones.ids_sumo
        get_vtype_for_mode = scenario.demand.vtypes.get_vtype_for_mode
        ids = ft.get_ids()
        fd.write(xm.begin('demand',indent))
        #self.parent.vtypes.write_xml(   fd, indent=indent,
        #                                #ids = ids_vtype_selected,
        #                                is_print_begin_end = False)
        
         #<demand>
        #   <actorConfig id="0">
        #       <timeSlice duration="86400000" startTime="0">
        #           <odPair amount="100" destination="2" origin="1"/>
        #       </timeSlice>
        #   </actorConfig>
        #</demand>
                                        
        for id_flow, time_start, time_end, id_mode, id_orig_sumo, id_dest_sumo, tripnumber in zip(\
                ids, ft.times_start[ids], ft.times_end[ids], ft.ids_mode[ids], 
                ids_zone_sumo[ft.ids_orig[ids]], ids_zone_sumo[ft.ids_dest[ids]], 
                ft.tripnumbers[ids]):
   
            fd.write(xm.start('actorConfig',indent + 2))
            fd.write(xm.num('id',get_vtype_for_mode(id_mode=id_mode, is_sumoid = True)))
            fd.write(xm.stop())
            
            fd.write(xm.start('timeSlice',indent + 4))
            fd.write(xm.num('duration',int(time_end-time_start)))
            fd.write(xm.num('startTime',int(time_start)))
            fd.write(xm.stop()) 
            
            fd.write(xm.start('odPair',indent + 6))
            fd.write(xm.num('origin',id_orig_sumo))
            fd.write(xm.num('destination',id_dest_sumo))
            fd.write(xm.num('amount',int(tripnumber)))
            fd.write(xm.stopit())
            
            fd.write(xm.end('timeSlice',indent + 4))
            
            fd.write(xm.end('actorConfig',indent + 2))
            
        fd.write(xm.end('demand',indent))
        

        
        fd.close() 
        return filepath
    
        
    def export_sumoxml(self, filepath=None, encoding = 'UTF-8'):
        """
        Export flows to SUMO xml file formate.
        """
        print 'export_sumoxml',filepath,len(self)
        if len(self)==0: return None
        
        if filepath is None:
            filepath = self.get_flowfilepath()
        
        try:
            fd=open(filepath,'w')
        except:
            print 'WARNING in export_sumoxml: could not open',filepath
            return False
        #xmltag, xmltag_item, attrname_id = self.xmltag
        #fd.write('<?xml version="1.0" encoding="%s"?>\n'%encoding)
        #fd.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        indent = 0
        #fd.write(xm.begin('routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.sf.net/xsd/routes_file.xsd"',indent))

    
        
        
        self.write_xml(fd,indent = 0)
        
        
        fd.close() 
        return filepath
    
    def clear_od_trips(self):
        self.clear()

    def add_od_flows(self, t_start, t_end, id_mode,
                     id_activitytype_orig, id_activitytype_dest,
                     scale, names_orig, names_dest, tripnumbers):

        #print 'OdIntervals.add_od_flows',t_start, t_end, id_mode, scale
        ids_inter = self.select_ids(
                    (self.times_start.get_value() == t_start)
                    & (self.times_end.get_value() == t_end)
                    & (self.ids_activitytype_orig.get_value() == id_activitytype_orig)
                    & (self.ids_activitytype_dest.get_value() == id_activitytype_dest)
                    )

        if len(ids_inter) == 0:
            # no existing interval found. Create a new one
            id_inter = self.add_row(times_start=t_start, times_end=t_end,
                                    ids_activitytype_orig=id_activitytype_orig,
                                    ids_activitytype_dest=id_activitytype_dest,
                                    )
            #print '  create new',id_inter
            #odintervals.add_rows(2, t_start=[0,3600], t_end=[3600, 7200])
            odmodes = OdModes((self.odmodes.attrname, id_inter), parent=self,
                              modes=self.get_net().modes, zones=self.get_zones())
            #NO!! odmodes = OdModes( ('ODMs for modes', id_inter), parent = self, modes = self.get_net().modes, zones = self.get_zones())
            self.odmodes[id_inter] = odmodes

            odtrips = odmodes.add_od_trips(
                id_mode, scale, names_orig, names_dest, tripnumbers)
            return odtrips
        else:

            # there should be only one demand table found for a certain interval
            id_inter = ids_inter[0]
            # print '  use',id_inter
            odtrips = self.odmodes[id_inter].add_od_trips(
                id_mode, scale, names_orig, names_dest, tripnumbers)
            return odtrips

    def add_od_flow(self, t_start, t_end, id_mode,
                    id_activitytype_orig, id_activitytype_dest,
                    scale,
                    name_orig, name_dest, tripnumber):

        #print 'OdIntervals.add_od_flow',t_start, t_end, id_mode, scale, name_orig,name_dest,tripnumber
        odtrips = self.add_od_flows(t_start, t_end, id_mode,
                                    id_activitytype_orig, id_activitytype_dest,
                                    scale,
                                    [name_orig], [name_dest], [tripnumber])

        return odtrips

    def get_net(self):
        return self.net.get_value()

    def get_zones(self):
        return self.zones.get_value()
    
    def get_od_matrix(self, id_interval , id_odmode, ids_zone):
        od_matrix =np.zeros((len(ids_zone),len(ids_zone)))
##        id_odmode = self.odmodes[id_interval].ids_mode.get_id_from_index(odmode)
        od_matrix_ids = self.odmodes[id_interval].odtrips[id_odmode].get_ids()
        i = 0
        j = 0
        for id_zonei in ids_zone:
            for id_zonej in ids_zone:
                for od_matrix_id in od_matrix_ids:
                    od_trip = self.odmodes[id_interval].odtrips[id_odmode].get_row(od_matrix_id)
                    id_dest = od_trip['ids_dest']
                    id_orig = od_trip['ids_orig'] 
                    
                    if id_orig == id_zonei and id_dest == id_zonej:
                        tripnumber = od_trip['tripnumbers']
                        od_matrix[i, j] += tripnumber
                        break
                j += 1
                print 'j', j
            j = 0
            i += 1 
            print 'i', i
    ##        od_matrix = self.odmodes[id_interval].odtrips[id_odmode]
        print od_matrix
        return od_matrix
    
    def get_modes(self):
        return self.net.get_value().modes

    def get_activitytypes(self):
        return self.parent.activitytypes

class OdTripgenerator(db.TripoptionMixin,CmlMixin,Process):
    def __init__(self, odintervals, logger = None,**kwargs):
        
        self._init_common(  'odtripgenerator', name = 'OD Trip generator', 
                            parent = odintervals,
                            logger = logger,
                            info ='Generates trips from OD flows.',
                            )
         
        self.init_cml(' ')# pass  no commad to generate options only
        
        
        attrsman = self.get_attrsman()
        
        
                            
        
        
        self.is_clear_trips = attrsman.add(am.AttrConf(  'is_clear_trips', True,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Clear trips', 
                                    info = 'Clear all trips in current trips database before routing.',
                                    ))
                                                                                                               
        self.is_refresh_zoneedges = attrsman.add(am.AttrConf(  'is_refresh_zoneedges', True,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Refresh zone edges', 
                                    info = """Identify all edges in all zones before generating the trips. 
                                              Dependent on the  will take some time.""",
                                    ))
        
        self.is_make_route = attrsman.add(am.AttrConf(  'is_make_route', True,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Make also routes', 
                                    info = """Perform also a shortes distance routing between edge of origin and edge of destination.""",
                                    ))
                                                                
        self.n_trials_connect = attrsman.add(am.AttrConf(  'n_trials_connect', 5,
                                    groupnames = ['options'],
                                    perm='rw', 
                                    name = 'Connect trials', 
                                    info = """Number of triels to connect randomly chosen  
                                              origin- and destination edges with valid routes.""",
                                    ))

        modechoices = odintervals.parent.parent.net.modes.names.get_indexmap()
        modechoices['No fallback'] = -1
        #print '  modechoices',modechoices
        self.id_mode_fallback = attrsman.add(am.AttrConf('id_mode_fallback',  modechoices['No fallback'], 
                                        groupnames = ['options'], 
                                        choices = modechoices,
                                        name = 'Fallback Mode', 
                                        info = """Transport mode to be used instead of "passenger" mode
                                         in case the origin and destination cannot be connected by a route. 
                                         This is typically the case with origins or destinations 
                                         in traffic restricted zones. 
                                         Coose for example "taxi" to get access to traffic restricted Zones.
                                         """,
                                        ))
                                        
        
        
        #priority_max.get_value()) & (edges.speeds_max[ids_edge] < self.speed_max.get_value()))
        self.priority_max = attrsman.add(cm.AttrConf( 'priority_max', 8,
                                                groupnames = ['options'],
                                                name = 'Max. edge priority',
                                                perm = 'rw',
                                                info = "Maximum edge priority for which edges in a zone are considered departure or arrival edges.",
                                                ))
        
        self.speed_max = attrsman.add(cm.AttrConf( 'speed_max', 14.0,
                                                groupnames = ['options'],
                                                name = 'Max. edge speed',
                                                perm = 'rw',
                                                unit = 'm/s',
                                                info = "Maximum edge speed for which edges in a zone are considered departure or arrival edges.",
                                                ))
        
        self.n_edges_min_length = attrsman.add(cm.AttrConf( 'n_edges_min_length', 1,
                                                groupnames = ['options'],
                                                name = 'Min. edge number length prob.',
                                                perm = 'rw',
                                                info = "Minimum number of edges for with the departure/arrival probability is proportional to the edge length.",
                                                ))
        
        self.n_edges_max_length = attrsman.add(cm.AttrConf( 'n_edges_max_length', 500,
                                                groupnames = ['options'],
                                                name = 'Max. edge number length prob.',
                                                perm = 'rw',
                                                info = "Maximum number of edges for with the departure/arrival probability is proportional to the edge length.",
                                                ))
                                                
        self.add_posoptions()
        self.add_laneoptions()
        self.add_speedoptions()        
        
    def do(self):
        
        if self.is_clear_trips:
            self.parent.parent.trips.clear_trips()
            
        cml = self.get_cml()
        
        self.parent.generate_trips(\
                        id_mode_fallback = self.id_mode_fallback,
                        is_refresh_zoneedges = self.is_refresh_zoneedges,
                        pos_depart_default = self.pos_depart,
                        pos_arrival_default = self.pos_arrival,
                        speed_depart_default = self.speed_depart,
                        speed_arrival_default = self.speed_arrival,
                        ind_lane_depart_default = self.ind_lane_depart,
                        ind_lane_arrival_default=self.ind_lane_arrival,
                        n_trials_connect = self.n_trials_connect,
                        is_make_route = self.is_make_route,
                        priority_max = self.priority_max,
                        speed_max = self.speed_max,
                        n_edges_min_length = self.n_edges_min_length,
                        n_edges_max_length = self.n_edges_max_length,
                        )
                       
        
        return True
   
        
