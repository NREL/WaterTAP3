##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Demonstration zeroth-order model for WaterTAP3
"""

# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import Block, Constraint, Var, units as pyunits
from pyomo.network import Port

# Import IDAES cores
from idaes.core import (declare_process_block_class,
                        UnitModelBlockData,
                        useDefault)
from idaes.core.util.config import is_physical_parameter_block

from pyomo.environ import (
    Expression, Var, Param, NonNegativeReals, units as pyunits)

# Import WaterTAP# finanacilas module
import financials
from financials import * #ARIEL ADDED

from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import Arc
from idaes.core import FlowsheetBlock

# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock

import numpy as np

##########################################
####### UNIT PARAMETERS ######
# At this point (outside the unit), we define the unit parameters that do not change across case studies or analyses ######.
# Below (in the unit), we define the parameters that we may want to change across case studies or analyses. Those parameters should be set as variables (eventually) and atttributed to the unit model (i.e. m.fs.UNIT_NAME.PARAMETERNAME). Anything specific to the costing only should be in  m.fs.UNIT_NAME.costing.PARAMETERNAME ######
##########################################

## REFERENCE: # from McGivney/Kamakura figure 5.8.1. RO process based on DEEP model

### MODULE NAME ###
module_name = "reverse_osmosis"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_basis_yr = 2007

pump_eff = 0.8 # efficiency of pump
erd_eff = 0.9
mem_cost = 35 # ~30 dollars for 2007 converted to 2020 and from Optimum design of reverse osmosis system under different feed concentration and product specification
pump_cost = 53 / 1e5 * 3600 #$ per w
pressure_drop = 3 # bar Typical pressure drops range from 0.1-3 bar.
#a = 4.2e-7 # 𝑤𝑎𝑡𝑒𝑟 𝑝𝑒𝑟𝑚𝑒𝑎𝑏𝑖𝑙𝑖𝑡𝑦 coefficient m bar-1 s-1
b_constant = 3.5e-8 # Salt permeability coefficient m s-1
#pressure_in = 65 #bar pressure at inlet. should be unfixed.
p_atm = 1 #bar atmospheric pressure
#p_ret = p_in - pressure_drop # momentum balance
pw = 1000 # density of water kg/m3
#membrane_area_in = 50    
##########################################
##########################################

# You don't really want to know what this decorator does
# Suffice to say it automates a lot of Pyomo boilerplate for you
@declare_process_block_class("UnitProcess")
class UnitProcessData(UnitModelBlockData):
       
    """
    This class describes the rules for a zeroth-order model for a unit
    """
    # The Config Block is used tpo process arguments from when the model is
    # instantiated. In IDAES, this serves two purposes:
    #     1. Allows us to separate physical properties from unit models
    #     2. Lets us give users options for configuring complex units
    # For WaterTAP3, this will mainly be boilerplate to keep things consistent
    # with ProteusLib and IDAES.
    # The dynamic and has_holdup options are expected arguments which must exist
    # The property package arguments let us define different sets of contaminants
    # without needing to write a new model.
    CONFIG = ConfigBlock()
    CONFIG.declare("dynamic", ConfigValue(
        domain=In([False]),
        default=False,
        description="Dynamic model flag - must be False",
        doc="""Indicates whether this model will be dynamic or not,
**default** = False. Equilibrium Reactors do not support dynamic behavior."""))
    CONFIG.declare("has_holdup", ConfigValue(
        default=False,
        domain=In([False]),
        description="Holdup construction flag - must be False",
        doc="""Indicates whether holdup terms should be constructed or not.
**default** - False. Equilibrium reactors do not have defined volume, thus
this must be False."""))
    CONFIG.declare("property_package", ConfigValue(
        default=useDefault,
        domain=is_physical_parameter_block,
        description="Property package to use for control volume",
        doc="""Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PhysicalParameterObject** - a PhysicalParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(
        implicit=True,
        description="Arguments to use for constructing property packages",
        doc="""A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see property package for documentation.}"""))
    
    
    
    from unit_process_equations import initialization

    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test = module_name)
    
    
    def get_costing(self, module=financials, cost_method="wt", year=None, unit_params = None):
        """
        We need a get_costing method here to provide a point to call the
        costing methods, but we call out to an external consting module
        for the actual calculations. This lets us easily swap in different
        methods if needed.

        Within IDAES, the year argument is used to set the initial value for
        the cost index when we build the model.
        """
        # RO unit process based on the International Atomic Energy Agency's (IAEA) DEEP model
        # User Manual ==> https://www.iaea.org/sites/default/files/18/08/deep5-manual.pdf
        
        # First, check to see if global costing module is in place
        # Construct it if not present and pass year argument
        if not hasattr(self.flowsheet(), "costing"):
            self.flowsheet().get_costing(module=module, year=year)

        # Next, add a sub-Block to the unit model to hold the cost calculations
        # This is to let us separate costs from model equations when solving
        self.costing = Block()
        
        self.permeate = Block()
        self.feed = Block()
        self.retenate = Block()
        
        permeate = self.permeate
        feed = self.feed
        retenate = self.retenate
        
        units_meta = self.config.property_package.get_metadata().get_derived_units
        
        # Then call the appropriate costing function out of the costing module
        # The first argument is the Block in which to build the equations
        # Can pass additional arguments as needed
        
        self.costing.basis_year = unit_basis_yr
                
        t = self.flowsheet().config.time.first()               
        time = self.flowsheet().config.time
        
        sys_cost_params = self.parent_block().costing_param
        
        # DEFINE VARIABLES
        # Mass Fraction
        def set_flow_mass(self):
            self.mass_flow_h20 = Var(time,
                                  #initialize=1000,
                                  domain=NonNegativeReals,
                                  units=units_meta("mass")/units_meta("time"),
                                  doc="mass flow rate")
            
            self.mass_flow_tds = Var(time,
                                  #initialize=50,
                                  domain=NonNegativeReals,
                                  units=units_meta("mass")/units_meta("time"),
                                  doc="mass flow rate")            
        
        def set_mass_frac(self):
            self.mass_frac_h20 = Var(time,
                                  #initialize=0.75,
                                  #domain=NonNegativeReals,
                                  units=pyunits.dimensionless,
                                  doc="mass_fraction")
                        
            self.mass_frac_tds = Var(time,
                                  #initialize=0.35,
                                  #domain=NonNegativeReals,
                                  units=pyunits.dimensionless,
                                  doc="mass_fraction")
                                    
        def set_pressure_osm(self): # 
            self.pressure_osm = Var(time,
                                  #initialize=20,
                                  domain=NonNegativeReals,
                                  #units=pyunits.dimensionless,
                                  doc="x")
            
        def set_osm_coeff(self):
            self.osm_coeff = Var(time,
                                  initialize=0.1,
                                  #domain=NonNegativeReals,
                                  units=pyunits.dimensionless,
                                  doc="x")            
            
        def set_conc_mass(self):
            self.conc_mass_h20 = Var(time,
                                  #initialize=900,
                                  domain=NonNegativeReals,
                                  units=units_meta("mass")/units_meta("volume"),
                                  doc="h20 mass density")               
            
            self.conc_mass_total = Var(time,
                                  #initialize=1000,
                                  domain=NonNegativeReals,
                                  units=units_meta("mass")/units_meta("volume"),
                                  doc="density")
    
  
        def set_pressure(self):
            self.pressure = Var(time,
                                  initialize=45,
                                  domain=NonNegativeReals,
                                  bounds=(5, 90),
                                  #units=pyunits.dimensionless,
                                  doc="pressure")  
        
        self.feed.water_flux = Var(time,
                              initialize=5e-3,
                              bounds=(1e-5, 1.5e-2),
                              units=units_meta('mass')*units_meta('length')**-2*units_meta('time')**-1,
                              domain=NonNegativeReals,
                              doc="water flux")  
        
        self.retenate.water_flux = Var(time,
                              initialize=5e-3,
                              bounds=(1e-5, 1.5e-2),
                              units=units_meta('mass')*units_meta('length')**-2*units_meta('time')**-1,
                              domain=NonNegativeReals,
                              doc="water flux")
        
        self.pure_water_flux = Var(time,
                              initialize=5e-3,
                              bounds=(1e-3, 1.5e-2),
                              units=units_meta('mass')*units_meta('length')**-2*units_meta('time')**-1,
                              domain=NonNegativeReals,
                              doc="water flux")
        
        self.a = Var(time,
                    initialize=4.2,
                    bounds=(1.5, 9),
                    #units=units_meta('mass')/units_meta('area')**-2*units_meta('time')**-1,
                    domain=NonNegativeReals,
                    doc="water permeability")
                
        self.b = Var(time, 
                    initialize=0.35,
                    bounds=(0.15, 0.9),
                    #units=units_meta('mass')*units_meta('length')**-2*units_meta('time')**-1,
                    domain=NonNegativeReals,
                    doc="Salt permeability")
        
        self.mem_cost = Var(time, 
                    initialize=40,
                    bounds=(10, 80),
                    #units=units_meta('mass')*units_meta('length')**-2*units_meta('time')**-1,
                    domain=NonNegativeReals,
                    doc="Membrane cost")                
        
        
    # from excel regression based on paper for membrane cost y = 0.1285x - 0.0452 #R² = 0.9932. y = b. x = a.
        self.water_salt_perm_eq1 = Constraint(
                expr = self.b[t] <= (0.083*self.a[t] - 0.002) * 1.25
                )
        
        self.water_salt_perm_eq2 = Constraint(
                expr = self.b[t] >= (0.083*self.a[t] - 0.002) * 0.75
                ) 
        

        
#         self.a.fix(4.2)   
#         self.b.fix(0.35) 
        
        self.a_constant = self.a[t] * 1e-7
        self.b_constant = self.b[t] * 1e-7
        
        self.mem_cost.fix(30)
#         self.mem_cost_eq = Constraint(
#             expr = self.mem_cost[t] == 1.2*(15.05*self.a[t] - 131.1*self.b[t] + 30)
#         )
        # same 4 membranes used for regression ŷ = 15.04895X1 - 131.08641X2 + 29.43797
        
        for b in [permeate, feed, retenate]:
            set_flow_mass(b)
            set_mass_frac(b)
            set_conc_mass(b)
            set_osm_coeff(b)
            set_pressure_osm(b)
            if str(b) == "permeate":
                continue 
            else:
                set_pressure(b)                         
                #set_water_flux(b)    
        
        self.membrane_area = Var(time,
                      initialize=1e5,
                      domain=NonNegativeReals,
                      bounds=(1e1, 1e12),
                      #units=units_meta("mass")/units_meta("time"),
                      doc="area") 
        
        self.factor_membrane_replacement = Var(time,
                      initialize=0.2,
                      domain=NonNegativeReals,
                      bounds=(0.01, 3),
                      doc="replacement rate membrane fraction") 
        
        self.factor_membrane_replacement.fix(0.2)
        
        if unit_params == None:
            print("No parameters given. Assumes default single pass with default area and pressure -- check values")
            self.membrane_area.fix(membrane_area_in) # area per module m2
            feed.pressure.fix(pressure_in) #bar pressure at inlet. should be unfixed.    
        else:
            # self.membrane_area.fix(unit_params["membrane_area"]) # area per module m2
            if unit_params["pump"] == "yes":
                feed.pressure.fix(unit_params["feed_pressure"]) #bar pressure at inlet. should be unfixed.
            if unit_params["pump"] == "no":                   
                self.pressure_into_stage_eq = Constraint(
                    expr = feed.pressure[t] == self.pressure_in[t]) 
                
                #bar pressure at inlet. should be unfixed.
#             if "stage" in unit_params.keys():
#                 if ["stage"] == "yes":                   
#                     self.pressure_into_stage_eq = Constraint(
#                         expr = feed.pressure[t] == self.pressure_in[t]
#                    ) #bar pressure at inlet. should be unfixed.                
        #self.membrane_area = 50 * 1000 * self.flow_vol_in[t]
        
        
        
        
        ########################################################################
        ########################################################################                                     
        # get the variables of the feed 
        
        feed.eq1 = Constraint(
            expr = feed.conc_mass_total[t] ==  0.6312*self.conc_mass_in[t, "tds"] + 997.86 #kg/m3
        )
        
        feed.eq2 = Constraint(
            expr = feed.conc_mass_h20[t] == feed.conc_mass_total[t] - self.conc_mass_in[t, "tds"] # kg/m3
        )
        
        feed.eq3 = Constraint(
            expr = feed.mass_flow_h20[t] == feed.conc_mass_h20[t] * self.flow_vol_in[t] #kg/s
        )
        feed.eq4 = Constraint(
            expr = feed.mass_flow_tds[t] == self.conc_mass_in[t, "tds"] * self.flow_vol_in[t] #kg/s
        )            
        feed.eq5 = Constraint(
            expr = feed.mass_frac_tds[t] * (feed.mass_flow_h20[t] + feed.mass_flow_tds[t]) 
            == feed.mass_flow_tds[t]
        )        
        feed.eq6 = Constraint(
            expr = feed.mass_frac_h20[t] == 1 - feed.mass_frac_tds[t]
        )
        feed.eq7 = Constraint(
            expr = feed.osm_coeff[t] == 4.92*feed.mass_frac_tds[t]**2 + feed.mass_frac_tds[t]*0.0889 + 0.918 #unitless
        )            
        feed.eq8 = Constraint(
            expr = feed.pressure_osm[t]* 1e5* (1 - feed.mass_frac_tds[t])
            == 8.45e7 * feed.osm_coeff[t]* feed.mass_frac_tds[t]#bar
        )

               
#         # get water flux in
#         feed.water_flux_eq = Constraint(
#             expr= feed.water_flux[t] == pw* self.a[t] * 1e-7 *((feed.pressure[t] - p_atm) 
#                                                   - (feed.pressure_osm[t]))
#                                              )  #                                      
        
        ########################################################################
        ########################################################################                                     
        
        retenate.eq2 = Constraint(
            expr = retenate.conc_mass_total[t] ==  0.6312*self.conc_mass_waste[t, "tds"] + 997.86 #kg/m3
        )
        
        retenate.eq3 = Constraint(
            expr = retenate.conc_mass_h20[t] == retenate.conc_mass_total[t] - self.conc_mass_waste[t, "tds"] # kg/m3
        )         
                          
        retenate.eq6 = Constraint(
            expr = retenate.mass_frac_tds[t] * retenate.conc_mass_total[t] == self.conc_mass_waste[t, "tds"]
        )        
        retenate.eq7 = Constraint(
            expr = retenate.mass_frac_h20[t] == 1 - retenate.mass_frac_tds[t]
        )
        retenate.eq8 = Constraint(
            expr = retenate.osm_coeff[t] == 4.92 * retenate.mass_frac_tds[t]**2 
            + retenate.mass_frac_tds[t]*0.0889 + 0.918 #unitless
        )            
        retenate.eq9 = Constraint(
            expr = retenate.pressure_osm[t] * 1e5 *  (1 - retenate.mass_frac_tds[t]) 
            == 8.45e7 * retenate.osm_coeff[t] * retenate.mass_frac_tds[t] #bar 
        )
        
        # momentum (pressure) balance
        self.momentume_balance_eq = Constraint(
            expr = retenate.pressure[t] == feed.pressure[t] - pressure_drop  
        )
        
#         # get water flux retenate
#         retenate.water_flux_retenate_eq = Constraint(
#             expr= retenate.water_flux[t] == pw* self.a[t] * 1e-7 *((retenate.pressure[t] - p_atm) 
#                                                   - (retenate.pressure_osm[t]))
#         ) # 
        
        self.flow_vol_eq2 = Constraint(
            expr = self.flow_vol_waste[t] * retenate.conc_mass_total[t] == (retenate.mass_flow_tds[t] + retenate.mass_flow_h20[t])
        )
                                     
        ########################################################################
        ########################################################################        
                                             
        # get the variables of the permeate
        permeate.eq1 = Constraint(
            expr = permeate.conc_mass_total[t] == 756*permeate.mass_frac_tds[t]*1e-6 +995 
        )
        permeate.eq2 = Constraint(
            expr = self.conc_mass_out[t, "tds"] == permeate.conc_mass_total[t] * permeate.mass_frac_tds[t]*1e-6
        )            
#         permeate.eq3 = Constraint(
#             expr = permeate.mass_flow_h20[t] == 0.5 * self.membrane_area[t]
#             * (feed.water_flux[t] + retenate.water_flux[t])
#         )
        permeate.eq4 = Constraint(
            expr = permeate.mass_flow_tds[t] == 0.5 * self.membrane_area[t]
            * self.b[t] * 1e-7 * (self.conc_mass_in[t, "tds"] + self.conc_mass_waste[t, "tds"]) 
        )            
        permeate.eq5 = Constraint(
            expr = permeate.mass_frac_tds[t] * (permeate.mass_flow_tds[t] + permeate.mass_flow_h20[t]) 
            == 1e6 * permeate.mass_flow_tds[t]
        )        


#         permeate.eq7 = Constraint(
#             expr = permeate.osm_coeff[t] == 4.92 * (permeate.mass_frac_tds[t]*1e-6)**2 
#             + permeate.mass_frac_tds[t]*1e-6*0.0889 + 0.918 #unitless
#         )            
#         permeate.eq8 = Constraint(
#             expr = permeate.pressure_osm[t] == 1e-5 * (8.45e7 * permeate.osm_coeff[t]
#                                        * permeate.mass_frac_tds[t]*1e-6 / (1 - permeate.mass_frac_tds[t]*1e-6)) #bar 
#         )
        permeate.eq33 = Constraint(
        expr = self.pure_water_flux[t] == pw * self.a[t] * 1e-7 * ((feed.pressure[t] - p_atm - pressure_drop*0.5) 
                                                           - (feed.pressure_osm[t] + retenate.pressure_osm[t]) * 0.5)
                                                          )
        permeate.eq3 = Constraint(
            expr = permeate.mass_flow_h20[t] == self.membrane_area[t] * self.pure_water_flux[t]
        )

        self.flow_vol_eq1 = Constraint(
            expr = self.flow_vol_out[t] * permeate.conc_mass_total[t] == 
            (permeate.mass_flow_tds[t] + permeate.mass_flow_h20[t])
        )
        
    
        ########################################################################
        ########################################################################                 
                
        # Mass balances   
        self.mass_balance_h20 = Constraint(
            expr =  feed.mass_flow_h20[t] == permeate.mass_flow_h20[t] + retenate.mass_flow_h20[t]
        )
        
        self.mass_balance_tds = Constraint(
            expr = feed.mass_flow_tds[t] == permeate.mass_flow_tds[t] + retenate.mass_flow_tds[t]
        )
            
        ########################################################################
        ########################################################################    
        
        self.const_list2 = list(self.config.property_package.component_list) #.remove("tds")
        self.const_list2.remove("tds")

        for j in self.const_list2:
            setattr(self, ("%s_eq" % j), Constraint(
                expr = self.removal_fraction[t, j] * self.flow_vol_in[t] * self.conc_mass_in[t, j] 
                == self.flow_vol_waste[t] * self.conc_mass_waste[t, j] 
                ))
                 
        
     ########################################################################
        ########################################################################           

#          #retenate pressure difference vs. inlet pressure
#         self.pressure_waste_outlet_eq = Constraint(
#         expr = self.pressure_in[t] + self.deltaP_waste[t] == self.pressure_waste[t]
#         )   

#          #retenate pressure difference vs. inlet pressure
#         self.pressure_outlet_eq = Constraint(
#         expr = self.pressure_in[t] + self.deltaP_outlet[t] == self.pressure_out[t]
#         )           
        
                #retenate pressure difference vs. inlet pressure
        self.pressure_waste_outlet_eq = Constraint(
        expr = self.feed.pressure[t] - pressure_drop == self.pressure_waste[t]
        )        
        
        # permeate pressure
        self.p_out_eq = Constraint(
                expr = 1 == self.pressure_out[t]
            )
        
        
        #self.ro_water_recovery =  self.flow_vol_out[t] / self.flow_vol_in[t]
        
        ########################################################################
        b_cost = self.costing
        ########################################################################          
        
#         def fixed_cap_mcgiv(wacs): --> can use this to compare with Excel, if needed.

#             Single_Pass_FCI = (0.3337 * wacs ** 0.7177) * ((0.0936 * wacs ** 0.7837) / (0.1203 * wacs ** 0.7807))
#             Two_Pass_FCI = (0.3337 * wacs ** 0.7177)
            
#             #mcgivney_cap_cost = .3337 * (wacs/24)**.7177 * cost_factor_for_number_of_passes * parallel_units # Mike's UP $M
#             #guo_cap_cost =  0.13108 * (wacs/24) ** 0.82523 * cost_factor_for_number_of_passes * parallel_units # Mike's $M
#             if unit_params is None:
#                 return Single_Pass_FCI
#             else:
#                 if unit_params["pass"] == "first": 
#                     return Single_Pass_FCI
#                 if unit_params["pass"] == "second":
#                     return (Two_Pass_FCI - Single_Pass_FCI)

        plant_cap_utilization = 1
        
         ################ Electricity consumption is assumed to be only the pump before the RO unit 
        # pass assumes permeate is coming in, so pump is required
        if unit_params["pump"] == "yes": 
            self.pressure_diff = (feed.pressure[t] - self.pressure_in[t])*1e5 # assumes atm pressure before pump. change to Pa
            self.pump_power = (self.flow_vol_in[t] * self.pressure_diff) / pump_eff #w
            b_cost.pump_capital_cost = self.pump_power * (53 / 1e5 * 3600) #* 1e-6
        
        # assumes no pump needed for stage, but could change in future.
        if unit_params["pump"] == "no":
            self.pump_power = 0
            b_cost.pump_capital_cost = 0
        ########################################################################  
        
        ################ Energy Recovery
        # assumes atmospheric pressure out
        if unit_params["erd"] == "yes": 
            x_value = (retenate.mass_flow_tds[t] + retenate.mass_flow_h20[t]) / retenate.conc_mass_total[t] * 3600
            b_cost.erd_capital_cost = 3134.7 * x_value ** 0.58
            self.erd_power = (self.flow_vol_waste[t] * (retenate.pressure[t] - 1) *1e5) / erd_eff
        
        if unit_params["erd"] == "no": 
            self.erd_power = 0
            b_cost.erd_capital_cost = 0
            
        ################ captial
        # membrane capital cost       
        b_cost.mem_capital_cost = self.mem_cost[t] * self.membrane_area[t] 
        
        # total capital investment
        #b_cost.fixed_cap_inv_unadjusted = fixed_cap_mcgiv(self.flow_vol_out[t] *3600)
        b_cost.fixed_cap_inv_unadjusted = 1.65 * (self.costing.pump_capital_cost 
        + self.costing.mem_capital_cost + b_cost.erd_capital_cost) * 1e-6 #$MM ### 1.65 -> TIC -> ARIEL TO DO 
        
        ################ operating
        # membrane operating cost
        b_cost.other_var_cost = self.factor_membrane_replacement[t] * self.mem_cost[t] * self.membrane_area[t] * sys_cost_params.plant_cap_utilization * 1e-6  
        
        ####### electricity and chems
        sys_specs = self.parent_block().costing_param
        self.electricity = ((self.pump_power - self.erd_power) / 1000) / (self.flow_vol_out[t]*3600) #kwh/m3
        b_cost.pump_electricity_cost = 1e-6*(self.pump_power/1000)*365*24*sys_specs.electricity_price #$MM/yr
        b_cost.erd_electricity_sold = 1e-6*(self.erd_power/1000)*365*24*sys_specs.electricity_price #$MM/yr
        b_cost.electricity_cost = (b_cost.pump_electricity_cost - b_cost.erd_electricity_sold) * sys_cost_params.plant_cap_utilization
        
        self.chem_dict = {"unit_cost": 0.01} 
                
        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################        
        
        module.get_complete_costing(self.costing)        
        
        
  