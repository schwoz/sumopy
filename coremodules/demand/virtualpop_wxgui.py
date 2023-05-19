import wx


import agilepy.lib_base.classman as cm
import agilepy.lib_base.arrayman as am
from agilepy.lib_base.misc import get_inversemap
from agilepy.lib_wx.ogleditor import *
import virtualpop_results_mpl as results_mpl
try:
    import virtualpop_results_mpl as results_mpl
    is_mpl = True # we have matplotlib support
except:
    print "WARNING: python matplotlib package not installed, no matplotlib plots."
    is_mpl = False 
    
    
is_bitjoin = False
import virtualpop
try:
	import bitjoin
	is_bitjoin = True
except:
	print 'WARNING - bitjoin module is missing'


from agilepy.lib_wx.processdialog import ProcessDialog, ProcessDialogInteractive
                                    
class VirtualpopWxGuiMixin:
	"""Contains Virtualpopulation spacific functions that communicate between the widgets of the main wx gui
	and the functions of the plugin.
	"""

    #def refresh_virtualpop(self,is_refresh):
    #    if is_refresh:
    #        neteditor = self.get_neteditor()
    #        #neteditor.add_tool(AddODflowTool(self, odintervals))
    #        #neteditor.add_toolclass(AddODflowTool)
            
	def add_menu_virtualpop(self, menubar):
		        #----------------------------------------------------------------------

		menubar.append_menu( 'demand/virtual population',
							bitmap = self.get_icon("icon_virtualpopulation.jpg")
							)  

		if is_bitjoin:
			
			menubar.append_menu( 'demand/virtual population/households',
	        info = 'A group of people, often a family, who live together',
	            # ~ bitmap = wx.ArtProvider.GetBitmap(wx.ART_DELETE,wx.ART_MENU),
	            )
	            
	        menubar.append_item( 'demand/virtual population/households/generate households from residential facilities...',
	            self.on_generate_households_from_residential_facilities, 
	            info='Create households from residential facilities by statistics.',
	            # ~ bitmap = wx.ArtProvider.GetBitmap(wx.ART_DELETE,wx.ART_MENU),
	            )
	        menubar.append_item( 'demand/virtual population/households/generate vp from households...',
	            self.on_generate_vp_from_households, 
	            info='Create virtual population from households by statistics.',
	            # ~ bitmap = wx.ArtProvider.GetBitmap(wx.ART_DELETE,wx.ART_MENU),
	            )
	        menubar.append_item( 'demand/virtual population/households/clear households',
	            self.on_clear_households, 
	            bitmap = wx.ArtProvider.GetBitmap(wx.ART_DELETE,wx.ART_MENU),
	            )
		
		menubar.append_menu( 'demand/virtual population/configure population',
			)
                            
		menubar.append_item( 'demand/virtual population/configure population/generate...',
			self.on_generate, 
			)
            
		menubar.append_item( 'demand/virtual population/configure population/create from zone-to-zone flows...',
			self.on_create_pop_from_odflows, 
			)
			
		menubar.append_item( 'demand/virtual population/configure population/complete daily activities...',
			self.on_complete_daily_activities, 
			) 
		
		menubar.append_menu( 'demand/virtual population/configure vehicles',
							#bitmap = self.get_icon("icon_virtualpopulation.jpg")
							)
							
		menubar.append_item( 'demand/virtual population/configure vehicles/provide vehicles...',
			self.on_provide_vehicles, 
			)
		
		menubar.append_item( 'demand/virtual population/configure vehicles/clear individual vehicles',
			self.on_clear_ivehicles, 
			bitmap = wx.ArtProvider.GetBitmap(wx.ART_DELETE,wx.ART_MENU),
			)
			  
				  
		menubar.append_menu( 'demand/virtual population/plans',
							#bitmap = self.get_icon("icon_virtualpopulation.jpg")
							)
		
		
		menubar.append_item( 'demand/virtual population/plans/generate...',
			self.on_generate_plan, 
			)
		
		
			   
		menubar.append_item( 'demand/virtual population/plans/select current plans...',
			self.on_planselection, 
			)  
		
		
			
		menubar.append_item( 'demand/virtual population/plans/reroute current plans...',
			self.on_dua_reroute, 
			) 
		
		
		menubar.append_item( 'demand/virtual population/plans/import plans from route file...',
			self.on_import_plans, 
			bitmap = self.get_agileicon("Document_Import_24px.png"),
			)
						 
		menubar.append_item( 'demand/virtual population/plans/clear plans',
			self.on_clear_plans, 
			bitmap = wx.ArtProvider.GetBitmap(wx.ART_DELETE,wx.ART_MENU),
			)
			
		
			
		#menubar.append_item( 'demand/virtual population/plans/export plans to SUMO xml...',
		#    self.on_write_plans_to_sumoxml, 
		#    info='Export all plans to SUMO routes XML format.',
		#    #bitmap = self.get_icon("Document_Import_24px.png"),
		#    )    
		
		
		  
		menubar.append_item( 'demand/virtual population/clear polulation, plans, vehicles and activities',
			self.on_clear_pop, 
			bitmap = wx.ArtProvider.GetBitmap(wx.ART_DELETE,wx.ART_MENU),
			)
		
		menubar.append_menu( 'demand/virtual population/analysis',
							bitmap = self.get_agileicon('icon_results_24px.png'),
							)   
                            
                             
		if is_mpl:
            
			menubar.append_item( 'demand/virtual population/analysis/plot activities...',
				self.on_plot_activities, 
				bitmap = results_mpl.get_mplicon(),#,
				)
			
			menubar.append_item( 'demand/virtual population/analysis/plot strategy data...',
				self.on_plot_strategies, 
				bitmap = results_mpl.get_mplicon(),#,
				)
			
			menubar.append_item( 'demand/virtual population/analysis/load iteration results...',
				self.on_open_iterationresults, 
				bitmap = self.get_agileicon("Document_Import_24px.png"),
				)
				
			menubar.append_item( 'demand/virtual population/analysis/plot iteration results...',
				self.on_plot_iterations, 
				bitmap = results_mpl.get_mplicon(),#,
				)    
                
	def on_clear_plans(self, event=None):
		self._demand.virtualpop.clear_plans()
		self._mainframe.browse_obj(self._demand.virtualpop.get_plans())
    
	def on_clear_ivehicles(self, event=None):
		self._demand.virtualpop.clear_ivehicles()
		self._mainframe.browse_obj(self._demand.virtualpop)
        
	def on_clear_households(self, event=None):
		self._demand.virtualpop.households.clear_households()
		self._mainframe.browse_obj(self._demand.virtualpop.households)
             
	def on_clear_pop(self, event=None):
		self._demand.virtualpop.clear_population()
		self._demand.virtualpop.activities.clear()
		self._mainframe.browse_obj(self._demand.virtualpop)
        #if event:  event.Skip()   
    
	def on_complete_daily_activities(self, event=None):
		"""
		Complete daily by making everyone return by the end of the day.
		"""
		proc = virtualpop.ActivityCompleter(virtualpop = self._demand.virtualpop, logger = self._mainframe.get_logger())
		dlg = ProcessDialog(self._mainframe, proc, immediate_apply=True)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		val = dlg.ShowModal()
		#print '  val,val == wx.ID_OK',val,wx.ID_OK,wx.ID_CANCEL,val == wx.ID_CANCEL
		#print '  status =',dlg.get_status()
		if dlg.get_status() != 'success':#val == wx.ID_CANCEL:
			#print ">>>>>>>>>Unsuccessful\n"
			dlg.Destroy()
			
		if dlg.get_status() == 'success':
			#print ">>>>>>>>>successful\n"
			# apply current widget values to scenario instance
			dlg.apply()
			dlg.Destroy()
			self._mainframe.browse_obj(self._demand.virtualpop)
            #self._mainframe.refresh_moduleguis()
                
                
	def on_planselection(self, event=None):
		"""
		Plan selector to set current plan with different methods
		"""
		#self._landuse.parking.make_parking()
		#self._canvas = canvas.draw()
		#drawing = self.get_drawing().get_drawobj_by_ident('parkingdraws')
		
		# TODO: make a proper import mask that allows to set parameters
		#self._landuse.maps.download()
		proc = virtualpop.PlanSelector('planselector', self._demand.virtualpop, logger = self._mainframe.get_logger())
		dlg = ProcessDialog(self._mainframe, proc, immediate_apply=True)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		val = dlg.ShowModal()
		#print '  val,val == wx.ID_OK',val,wx.ID_OK,wx.ID_CANCEL,val == wx.ID_CANCEL
		#print '  status =',dlg.get_status()
		if dlg.get_status() != 'success':#val == wx.ID_CANCEL:
			#print ">>>>>>>>>Unsuccessful\n"
			dlg.Destroy()
			
		if dlg.get_status() == 'success':
			#print ">>>>>>>>>successful\n"
			# apply current widget values to scenario instance
			dlg.apply()
			dlg.Destroy()
			self._mainframe.browse_obj(self._demand.virtualpop)
			#self._mainframe.refresh_moduleguis()

	def on_import_plans(self, event=None):
		"""Import plans from SUMO route xml file."""
		wildcards_all = "All files (*.*)|*.*"
		dlg = wx.FileDialog(self._mainframe, message="Open SUMO route file",
							defaultDir=self.get_scenario().get_rootfilepath(), 
							#defaultFile="",
							wildcard = "XML file (*.xml,*.XML)|*.xml;*.XML|"+wildcards_all,
							style=wx.OPEN | wx.CHANGE_DIR
							)
		
		# Show the dialog and retrieve the user response. If it is the OK response, 
		# process the data.
		if dlg.ShowModal() == wx.ID_OK:
			# This returns a Python list of files that were selected.
			paths = dlg.GetPaths()
			#print 'You selected %d files:' % len(paths)
			if len(paths)>0:
				filepath = paths[0]
				print 'call import_routes_xml',filepath
				self._demand.virtualpop.import_routes_xml(filepath)
				self._mainframe.browse_obj(self._demand.virtualpop.get_plans())
		
		
		dlg.Destroy()
        
	def on_dua_reroute(self, event=None):
		"""
		Reroutes the virtual population with DUA router. Diffferent rerouting methods can be chosen.
		"""
		
		#self._demand.trips.clear_routes()
		
					
		self.proc = virtualpop.DuarouterVp(  'vpduarouter',
												self._demand.virtualpop, 
												logger = self._mainframe.get_logger()
												)
		
		
		dlg = ProcessDialogInteractive( self._mainframe, 
										self.proc,
										title = self.proc.get_name(),
										func_close = self.close_process,
										)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		#val = dlg.ShowModal()
		dlg.Show()
		dlg.MakeModal(True)
        
                
	def on_create_pop_from_odflows(self, event=None):
		"""
		Generates virtual population from OD flow matrix.
		"""
		
		#self._demand.trips.clear_routes()
		
					
		self.proc = virtualpop.PopFromOdfGenerator(  'pop_from_odflow_creator',
												self._demand.virtualpop, 
												logger = self._mainframe.get_logger()
												)
		
		
		dlg = ProcessDialogInteractive( self._mainframe, 
										self.proc,
										title = self.proc.get_name(),
										func_close = self.close_process,
										)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		#val = dlg.ShowModal()
		print 'on_create_pop_from_odflows'
		dlg.Show()
		dlg.MakeModal(True) 
		
			
		
		

	def on_provide_vehicles(self, event=None):
		"""
		Provide vehicles to satisfy predefined statistical characteristics.
		"""
		
		#self._demand.trips.clear_routes()
		
					
		self.proc = virtualpop.VehicleProvider(  'vehicleprovider',
												self._demand.virtualpop, 
												logger = self._mainframe.get_logger()
												)
		
		
		dlg = ProcessDialogInteractive( self._mainframe, 
										self.proc,
										title = self.proc.get_name(),
										func_close = self.close_process,
										)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		#val = dlg.ShowModal()
		print 'on_provide_vehicles'
		dlg.Show()
		dlg.MakeModal(True) 
        
            
        
    

	def on_generate_plan(self, event=None):
		"""
		Generates mobility plans using different strategies..
		"""
		
		#self._demand.trips.clear_routes()
		
					
		self.proc = virtualpop.Planner(  'planner',
												self._demand.virtualpop, 
												logger = self._mainframe.get_logger()
												)
		
		
		dlg = ProcessDialogInteractive( self._mainframe, 
										self.proc,
										#title = self.proc.get_name(),
										func_close = self.close_process,
										is_close_after_completion = False,
										)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		#val = dlg.ShowModal()
		print 'on_generate_plan'
		dlg.Show()
		dlg.MakeModal(True) 
		if self.proc.status == 'success':
			self._mainframe.browse_obj(self._demand.virtualpop)
		
        
    
	def close_process(self, dlg):
		# called before destroying the process dialog
		if self.proc.status == 'success':
			self._mainframe.browse_obj(self._demand.virtualpop)
			
					 
		
        
        
	def on_write_plans_to_sumoxml(self, event = None):
		#print 'on_write_plans_to_sumoxml'
		dirpath = self.get_scenario().get_workdirpath()
		defaultFile = self.get_scenario().get_rootfilename()+'.rou.xml'
		wildcards_all = 'All files (*.*)|*.*|XML files (*.xml)|*.xml'
		dlg = wx.FileDialog(None, message='Write plans to SUMO rou.xml', 
							defaultDir=dirpath, 
							#defaultFile=defaultFile, 
							wildcard=wildcards_all, style=wx.SAVE | wx.CHANGE_DIR)
		if dlg.ShowModal() == wx.ID_OK:
			filepath = dlg.GetPath()
		
		else:
			return 
		
		self._demand.virtualpop.export_sumoxml(filepath)
        
	def on_plot_activities(self, event=None):
		"""
		Plot different results on activities in Matplotlib plotting envitonment.
		"""
		if is_mpl:
			resultplotter = results_mpl.ActivityPlotter('Activity Plotter',  self._demand.virtualpop, 
														logger = self._mainframe.get_logger()
														)
			dlg = results_mpl.ResultDialog(self._mainframe, resultplotter)
							 
			dlg.CenterOnScreen()
		
			# this does not return until the dialog is closed.
			val = dlg.ShowModal()
			#print '  val,val == wx.ID_OK',val,wx.ID_OK,wx.ID_CANCEL,val == wx.ID_CANCEL
			#print '  status =',dlg.get_status()
			if dlg.get_status() != 'success':#val == wx.ID_CANCEL:
				#print ">>>>>>>>>Unsuccessful\n"
				dlg.Destroy()
				
			if dlg.get_status() == 'success':
				#print ">>>>>>>>>successful\n"
				# apply current widget values to scenario instance
				dlg.apply()
				dlg.Destroy()

	def on_plot_strategies(self, event=None):
		"""
		Plot different results on strategies in Matplotlib plotting envitonment.
		"""
		if is_mpl:
			resultplotter = results_mpl.StrategyPlotter(  self._demand.virtualpop, 
														logger = self._mainframe.get_logger()
														)
			dlg = results_mpl.ResultDialog(self._mainframe, resultplotter)
							 
			dlg.CenterOnScreen()
		
			# this does not return until the dialog is closed.
			val = dlg.ShowModal()
			#print '  val,val == wx.ID_OK',val,wx.ID_OK,wx.ID_CANCEL,val == wx.ID_CANCEL
			#print '  status =',dlg.get_status()
			if dlg.get_status() != 'success':#val == wx.ID_CANCEL:
				#print ">>>>>>>>>Unsuccessful\n"
				dlg.Destroy()
				
			if dlg.get_status() == 'success':
				#print ">>>>>>>>>successful\n"
				# apply current widget values to scenario instance
				dlg.apply()
				dlg.Destroy()   

	def on_open_iterationresults(self, event=None):
		"""
		Load results from virtual population iteration simulation script_vp_iter.py
		"""
			
		wildcards_all = "All files (*.*)|*.*"
		wildcards_obj = "VP iterate result files (*.vpiterres.obj)|*.vpiterres.obj|Python binary files (*.obj)|*.obj"
		wildcards = wildcards_obj+"|"+wildcards_all
		
		# Finally, if the directory is changed in the process of getting files, this
		# dialog is set up to change the current working directory to the path chosen.
		dlg = wx.FileDialog(
			self._mainframe, message="Open VP iteration results file",
			defaultDir = self.get_scenario().get_workdirpath(), 
			#defaultFile = self.get_scenario().get_rootfilepath()+'.vpiterres.obj',
			wildcard=wildcards,
			style=wx.OPEN | wx.CHANGE_DIR
			)
		
		# Show the dialog and retrieve the user response. If it is the OK response, 
		# process the data.
		is_newresults = False
		if dlg.ShowModal() == wx.ID_OK:
			# This returns a Python list of files that were selected.
			filepath = dlg.GetPath()
			if len(filepath)>0:
				simresults = self._demand.parent.simulation.results
				if simresults is not None:
					
					# delete old object, if any
					vpiterstats = simresults.get_resultobj('vpiterstats')
					if vpiterstats is not None:
						simresults.delete('vpiterstats')
						del vpiterstats
						
					vpiterstats = cm.load_obj(filepath)
						
					simresults.add_resultobj(vpiterstats)
			
					is_newresults = True
				
				
		
		# Destroy the dialog. Don't do this until you are done with it!
		# BAD things can happen otherwise!
		dlg.Destroy()
		
		if is_newresults:
			# this should update all widgets for the new scenario!!
			#print 'call self._mainframe.refresh_moduleguis()'
			self._mainframe.browse_obj(simresults)
			#self._mainframe.select_view(name = "Result viewer") #!!!!!!!!tricky, crashes without
			#self.refresh_widgets()
			#wx.CallAfter(self.refresh_widgets)
			#self._mainframe.refresh_moduleguis()
			#if event: event.Skip()
            
	def on_generate_vp_from_households(self, event=None):
		"""
		Generate households from residential facilities by statistics..
		"""
		
		#self._demand.trips.clear_routes()
		
					
		self.proc = bitjoin.VpFromHouseholdsGenerator(  'virtualpop',
												self._demand.virtualpop, 
												logger = self._mainframe.get_logger()
												)
				
		dlg = ProcessDialogInteractive( self._mainframe, 
										self.proc,
										title = 'Generate virtualpop from households',
										func_close = self.close_process,
										is_close_after_completion = True,
										)
		
		dlg = ProcessDialogInteractive( self._mainframe, 
										self.proc,
										title = 'Generate virtualpop from households',
										func_close = self.close_process,
										)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		#val = dlg.ShowModal()
		print 'on_create_pop_from_odflows'
		dlg.Show()
		dlg.MakeModal(True) 

	def on_generate_households_from_residential_facilities(self, event=None):
		"""
		Generate households from residential facilities by statistics..
		"""
		
		#self._demand.trips.clear_routes()
		
					
		self.proc = bitjoin.HouseholdsFromFacilitiesGenerator(  'households',
												self._demand.virtualpop, 
												logger = self._mainframe.get_logger()
												)
						 
		
		dlg = ProcessDialogInteractive( self._mainframe, 
										self.proc,
										title = 'Generate households from residential facilities',
										func_close = self.close_process,
										)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		#val = dlg.ShowModal()
		print 'on_create_pop_from_odflows'
		dlg.Show()
		dlg.MakeModal(True) 
        
        
        
        
            
	def on_plot_iterations(self, event=None):
		"""
		Plot different results on strategies in Matplotlib plotting envitonment.
		First iteration results must be loaded.
		"""
		scenario = self._demand.parent
		
		vpiterstats = scenario.simulation.results.get_resultobj('vpiterstats')
		print 'on_plot_iterations  '
		print ' vpiterstats ',vpiterstats
		if is_mpl & (vpiterstats is not None):
			resultplotter = results_mpl.IteratePlotter(  scenario,
														 logger = self._mainframe.get_logger()
														)
			dlg = results_mpl.ResultDialog(self._mainframe, resultplotter)
							 
			dlg.CenterOnScreen()
		
			# this does not return until the dialog is closed.
			val = dlg.ShowModal()
			#print '  val,val == wx.ID_OK',val,wx.ID_OK,wx.ID_CANCEL,val == wx.ID_CANCEL
			#print '  status =',dlg.get_status()
			if dlg.get_status() != 'success':#val == wx.ID_CANCEL:
				#print ">>>>>>>>>Unsuccessful\n"
				dlg.Destroy()
				
			if dlg.get_status() == 'success':
				#print ">>>>>>>>>successful\n"
				# apply current widget values to scenario instance
				dlg.apply()
				dlg.Destroy()   

	def on_generate(self, event=None):
		"""
		Generates virtual population based on some statistical data.
		"""
		
		#self._demand.trips.clear_routes()
		
					
		self.proc = virtualpop.PopGenerator(  'pop_generator',
												self._demand.virtualpop, 
												logger = self._mainframe.get_logger()
												)
		
		
		dlg = ProcessDialogInteractive( self._mainframe, 
										self.proc,
										title = self.proc.get_name(),
										func_close = self.close_process,
										)
						 
		dlg.CenterOnScreen()
		
		# this does not return until the dialog is closed.
		#val = dlg.ShowModal()
		print 'on_create_pop_from_odflows'
		dlg.Show()
		dlg.MakeModal(True) 
    
