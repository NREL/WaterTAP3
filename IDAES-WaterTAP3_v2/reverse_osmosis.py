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
unit_basis_yr = 2018

pump_eff = 0.85 # efficiency of pump
mem_cost = 30
factor_membrane_replacement = 0.2
pump_cost = 53 / 1e5 * 3600 #$ per w
pressure_drop = 3 # bar Typical pressure drops range from 0.1-3 bar.
a = 4.2e-7 # 𝑤𝑎𝑡𝑒𝑟 𝑝𝑒𝑟𝑚𝑒𝑎𝑏𝑖𝑙𝑖𝑡𝑦 coefficient m bar-1 s-1
pressure_in = 50 #bar pressure at inlet. should be unfixed.
p_atm = 1 #bar atmospheric pressure
#p_ret = p_in - pressure_drop # momentum balance
pw = 1000 # density of water kg/m3
b_constant = 3.5e-8 # Salt permeability coefficient m s-1
        
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
    #unit_process_equations.get_base_unit_process()

    #build(up_name = "nanofiltration_twb")
    
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
        
  
        # DEFINE VARIABLES
        # Mass Fraction
        def set_flow_mass(self):
            self.mass_flow_h20 = Var(time,
                                  initialize=0.35,
                                  domain=NonNegativeReals,
                                  units=units_meta("mass")/units_meta("time"),
                                  doc="mass flow rate")
            
            self.mass_flow_tds = Var(time,
                                  initialize=0.35,
                                  domain=NonNegativeReals,
                                  units=units_meta("mass")/units_meta("time"),
                                  doc="mass flow rate")            
        
        def set_mass_frac(self):
            self.mass_frac_h20 = Var(time,
                                  initialize=0.35,
                                  #domain=NonNegativeReals,
                                  units=pyunits.dimensionless,
                                  doc="mass_fraction")
                        
            self.mass_frac_tds = Var(time,
                                  initialize=0.35,
                                  #domain=NonNegativeReals,
                                  units=pyunits.dimensionless,
                                  doc="mass_fraction")
                                    
        def set_pressure_osm(self): # BAR
            self.pressure_osm = Var(time,
                                  initialize=50,
                                  #domain=NonNegativeReals,
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
                                  initialize=0.35,
                                  #domain=NonNegativeReals,
                                  units=units_meta("mass")/units_meta("volume"),
                                  doc="h20 mass density")               
            
            self.conc_mass_total = Var(time,
                                  initialize=1,
                                  #domain=NonNegativeReals,
                                  units=units_meta("mass")/units_meta("volume"),
                                  doc="density")
    
  
        def set_pressure(self):
            self.pressure = Var(time,
                                  initialize=50,
                                  domain=NonNegativeReals,
                                  bounds=(10, 85),
                                  #units=pyunits.dimensionless,
                                  doc="pressure")  
        def set_water_flux(self):
            self.water_flux = Var(time,
                                  initialize=1,
                                  #domain=NonNegativeReals,
                                  #units=pyunits.dimensionless,
                                  doc="water flux")  
                                       
            
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
                set_water_flux(b)    
        
        self.membrane_area = Var(time,
                      initialize=40,
                      domain=NonNegativeReals,
                      #units=units_meta("mass")/units_meta("time"),
                      doc="area") 
        
        self.membrane_area.fix(50) # area per module m2
        
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
            #* feed.conc_mass_total[t] == self.conc_mass_in[t, "tds"] 
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

        feed.pressure.fix(pressure_in) #bar pressure at inlet. should be unfixed.
        
        # get water flux in
        feed.water_flux_eq = Constraint(
            expr= feed.water_flux[t] == pw* a*((feed.pressure[t] - p_atm) 
                                                  - (feed.pressure_osm[t]))
                                             ) #                                      
        
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
        
        # get water flux retenate
        retenate.water_flux_retenate_eq = Constraint(
            expr= retenate.water_flux[t] == pw* a*((retenate.pressure[t] - p_atm) 
                                                  - (retenate.pressure_osm[t]))
        ) # 
        
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
        permeate.eq3 = Constraint(
            expr = permeate.mass_flow_h20[t] == 0.5 * self.membrane_area[t] 
            * (feed.water_flux[t] + retenate.water_flux[t])
        )
        permeate.eq4 = Constraint(
            expr = permeate.mass_flow_tds[t] == 0.5 * self.membrane_area[t]
            * b_constant * (self.conc_mass_in[t, "tds"] + self.conc_mass_waste[t, "tds"]) 
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
        b_cost = self.costing
        ########################################################################          
        
         ################ Electricity consumption is assumed to be only the pump before the RO unit 
        self.pressure_diff = (feed.pressure[t] - 1)*1e5 # assumes atm pressure before pump. change to Pa
        self.pump_power = (self.flow_vol_in[t] * self.pressure_diff / pump_eff) #w
        ########################################################################  
        
        ################ Energy Recovery
        x_value = (retenate.mass_flow_tds[t] + retenate.mass_flow_h20[t]) / retenate.conc_mass_total[t] * 3600
        
        b_cost.erd_capital_cost = 3134.7 * x_value ** 0.58
        
                
        ################ captial
        # membrane capital cost       
        b_cost.mem_capital_cost = mem_cost * self.membrane_area[t] 
        
        # pump capital cost
        # DOES NOT WORK: b_cost.pump_capital_cost = self.pump_power * pump_cost # cost is per W
        # BELOW IS MGD BASED OFF EXCEL WATER PUMPING
        b_cost.pump_capital_cost = 40299 * (22.824465227271 * self.flow_vol_in[t]) ** .8657
        
        # total capital investment
        b_cost.fixed_cap_inv_unadjusted = (self.costing.pump_capital_cost 
        + self.costing.mem_capital_cost) * 1e-6 #$MM
        
        
        ################ operating
        # membrane operating cost
        self.mem_operating_cost = factor_membrane_replacement * mem_cost * self.membrane_area[t]
        b_cost.other_var_cost = self.mem_operating_cost * 1e-6   
        
        ####### electricity and chems
        sys_specs = self.parent_block().costing_param
        self.electricity = (self.pump_power / 1000) / self.flow_vol_out[t]
        b_cost.electricity_cost = 1e-6*(self.pump_power/1000)*365*24*sys_specs.electricity_price #$MM/yr
        
        self.chem_dict = {"unit_cost": 0.01} 
                
        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################        
        
        module.get_complete_costing(self.costing)        
        
        
  