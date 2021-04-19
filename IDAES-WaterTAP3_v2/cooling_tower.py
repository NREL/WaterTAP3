#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import IDAES cores
from idaes.core import (declare_process_block_class, UnitModelBlockData, useDefault)
from idaes.core.util.config import is_physical_parameter_block
# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import value, Constraint
# Import WaterTAP# financials module
import financials
from financials import *  # ARIEL ADDED
from cost_curves import basic_unit

##########################################
####### UNIT PARAMETERS ######
# At this point (outside the unit), we define the unit parameters that do not change across case studies or analyses ######.
# Below (in the unit), we define the parameters that we may want to change across case studies or analyses. Those parameters should be set as variables (eventually) and atttributed to the unit model (i.e. m.fs.UNIT_NAME.PARAMETERNAME). Anything specific to the costing only should be in  m.fs.UNIT_NAME.costing.PARAMETERNAME ######
##########################################

# SOURCE :EPRI 2004-Comparison_of_Alternate_Cooling_Technologies_for_U.S._Power_Plants

### MODULE NAME ###
module_name = "cooling_tower"

# to help clalculate climate variables:
import psychrolib
# Set the unit system, for example to SI (can be either psychrolib.SI or psychrolib.IP)
psychrolib.SetUnitSystem(psychrolib.SI)
       
########################################################################
########################################################################
## THIS JUST REPRESENTS A COOLING TOWER. DOES NOT HAVE COSTS.
########################################################################
########################################################################

#psychrolib.GetTWetBulbFromRelHum(TDryBulb, RelHum, Pressure)
#Return wet-bulb temperature given dry-bulb temperature, relative humidity, and pressure.

#Parameters for calculating wet bulb
#TDryBulb (float) – Dry-bulb temperature in °F [IP] or °C [SI]
#RelHum (float) – Relative humidity in range [0, 1]
#Pressure (float) – Atmospheric pressure in Psi [IP] or Pa [SI]
#Wet-bulb temperature in °F [IP] or °C [SI]
atmospheric_pressure = 101325 #Pa
ambient_temperature = 20
relative_humidity = 0.5


# You don't really want to know what this decorator does
# Suffice to say it automates a lot of Pyomo boilerplate for you
@declare_process_block_class("UnitProcess")
class UnitProcessData(UnitModelBlockData):
    """
    This class describes the rules for a zeroth-order model for a unit

    The Config Block is used tpo process arguments from when the model is
    instantiated. In IDAES, this serves two purposes:
         1. Allows us to separate physical properties from unit models
         2. Lets us give users options for configuring complex units
    The dynamic and has_holdup options are expected arguments which must exist
    The property package arguments let us define different sets of contaminants
    without needing to write a new model.
    """

    CONFIG = ConfigBlock()
    CONFIG.declare("dynamic", ConfigValue(domain=In([False]), default=False, description="Dynamic model flag - must be False", doc="""Indicates whether this model will be dynamic or not,
**default** = False. Equilibrium Reactors do not support dynamic behavior."""))
    CONFIG.declare("has_holdup", ConfigValue(default=False, domain=In([False]), description="Holdup construction flag - must be False", doc="""Indicates whether holdup terms should be constructed or not.
**default** - False. Equilibrium reactors do not have defined volume, thus
this must be False."""))
    CONFIG.declare("property_package", ConfigValue(default=useDefault, domain=is_physical_parameter_block, description="Property package to use for control volume", doc="""Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PhysicalParameterObject** - a PhysicalParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(implicit=True, description="Arguments to use for constructing property packages", doc="""A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see property package for documentation.}"""))

    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test=module_name)

    # NOTE ---> THIS SHOULD EVENTUaLLY BE JUST FOR COSTING INFO/EQUATIONS/FUNCTIONS. EVERYTHING ELSE IN ABOVE.
    def get_costing(self, module=financials, cost_method="wt", year=None, unit_params=None):
      
    
        # NOT ACTULLY USED:
        if not hasattr(self.flowsheet(), "costing"):
            self.flowsheet().get_costing(module=module, year=year)
        # Next, add a sub-Block to the unit model to hold the cost calculations
        # This is to let us separate costs from model equations when solving
        self.costing = Block()
        # Then call the appropriate costing function out of the costing module
        # The first argument is the Block in which to build the equations
        # Can pass additional arguments as needed
        
        # First, check to see if global costing module is in place
        # Construct it if not present and pass year argument
        # based on EPRI 2004 study and equations taken from Miara et al. 2017 (that replicate the method in EPRI study)

        ########################################
        ##### data inputs and assumptions #####
        ########################################
        self.cp = 4.18; #heat capacity
        # cycles in the tower ratio of the concentration of conserved species in the circulating water (Ci circ) to that in the makeup water (Ci mu)
        self.cycles = 5.0;
        self.ci_circ = 0.0 # unset for the ratio, but could be defined in future
        self.ci_makeup = 0.0 # unset for the ratio, but could be defined in future
        self.latent_heat  = 2264.76; # latent heat of vaporization MJ/m3
        self.evap_fraction  = 0.85; # fraction of totoal heat rejected by latent heat transfer - 0.9 in EPRI report 
        self.approach = 5.55; # see Miara & Vorosmarty 2017 for assumption
        self.wet_bulb_temp = 20 # unless specified
        self.ttd = 4.44 # Celsius based on typical range of 8F from EPRI 2004
        self.range = 11.11 # Celsius based on typical range of 20F from EPRI 2004
        time = self.flowsheet().config.time.first()
        
        #####
        if "cycles" in unit_params:
            print("cycles of concentration are set based on parameters to:", unit_params["cycles"])
            self.cycles = unit_params["cycles"];
        else:
            self.cycles = 5.0;
            print("if cycles are used, assuming cycles of concentration is:", self.cycles)
        
        #####
       
        
        ########################################
        ##### evaporation fraction provided by user #####
        ########################################        
        if unit_params["method"] == "evaporation_fraction":
            self.make_up = self.flow_vol_in[time]
            #blowdown assumed to be recovered (but is techincally waste and needs to be treated)
            self.evaporation = unit_params["evaporation_fraction"] * self.flow_vol_in[time]
            self.blowdown = self.make_up - self.evaporation
        
        ########################################
        ##### basic mass balance approach #####
        ########################################
        
        if unit_params["method"] == "make_up_mass_balance":

            self.make_up = self.flow_vol_in[time]
            #blowdown assumed to be recovered (but is techincally waste and needs to be treated)
            self.blowdown = self.make_up / self.cycles
            self.evaporation = self.make_up - self.blowdown # evaporation assumed to go to waste outlet (out of system) should not go to surface discharge  
                     
        ################################################################################
        ##### mass balance and plant info used to calculate cycles of concentration, blowdown, evaporation #####
        ################################################################################         
            
        if unit_params["method"] == "plant_info_with_makeup":
            print("make up is given, cycles of concentration are calculated as a result of assumptions")
            
            set_plant_info(self, unit_params)
            
            self.nameplate = unit_params["nameplate"]
            
            self.heat_in = self.nameplate / self.eff
            
            self.desired_heat_cond = self.heat_in - (self.heat_in * self.eff) - (self.heat_in * self.heat_sink)
            self.evaporation = self.desired_heat_cond * (self.evap_fraction / self.latent_heat)
            self.flow_vol_in.unfix()           
            unfix_inlet_to_train(self)
            self.flow_vol_waste.fix(self.evaporation)
            self.make_up = unit_params["make_up"]
            self.blowdown = self.make_up - self.evaporation
            self.cycles = self.make_up / self.blowdown
            
        ################################################################################
        ##### mass balance and plant info used to calculate make up, blowdown, evaporation #####
        ################################################################################               
        
        if unit_params["method"] == "plant_info_without_makeup":
            print("make up not given as a result of assumptions, cycles of concentration are given")
            
            set_plant_info(self, unit_params)
            
            self.nameplate = unit_params["nameplate"]
            
            self.heat_in = self.nameplate / self.eff
            
            self.desired_heat_cond = self.heat_in - (self.heat_in * self.eff) - (self.heat_in * self.heat_sink)
            self.evaporation = self.desired_heat_cond * (self.evap_fraction / self.latent_heat)
            self.flow_vol_in.unfix()           
            unfix_inlet_to_train(self)
            self.flow_vol_waste.fix(self.evaporation)
            self.make_up = self.flow_vol_in[time]
            self.blowdown = self.make_up - self.evaporation
            self.make_up = self.flow_vol_in[time]
            #blowdown assumed to be recovered (but is techincally waste and needs to be treated)
            self.blowdown = self.make_up / self.cycles
            self.evaporation = self.make_up - self.blowdown # evaporation assumed to go to waste outlet (out of system) should not go to surface discharge  
            
            
#         self.water_recovery_eq = Constraint(
#             expr = self.water_recovery[time] == self.blowdown / self.make_up
#         )   
        self.water_recovery.fix(self.blowdown / self.make_up)
        
        self.costing.basis_year = 2020 # NOT USED
        
        self.chem_dict = {}

        self.costing.fixed_cap_inv_unadjusted = self.flow_vol_in[time] * 1e-9 # $M

        ## electricity consumption ##
        self.electricity = 1e-9  # kwh/m3

        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################

        module.get_complete_costing(self.costing)

        # TO DO LATER IF NEEDED ___> BASED ON WEATHER.
        ################################################################################
        ##### weather, mass balance and plant info used to calculate make up, blowdown, evaporation #####
        ################################################################################      

#         if unit_params["method"] == "weather_and_plant_info":
#             if "approach" in  unit_params:   
#                 self.approach = unit_params["approach"]
#             if "wet_bulb_temp" in unit_params:
#                 print("wet_bulb taken from params for cooling tower")
#                 self.wet_bulb = unit_params["wet_bulb"]
#             elif "air_temp" in unit_params:
#                 print("wet_bulb calculated from air temp, humidity, and pressure")
#                 self.rel_hum = unit_params["realtive_humidity"]
#                 if "pressure" in unit_params: 
#                     self.pressure = unit_params["pressure"]
#                 else:
#                     self.pressure = atmospheric_pressure
#                     print("pressure assumed atmospheric")
#                 self.air_temp = unit_params["air_temp"]
#                 self.wet_bulb = psychrolib.GetTWetBulbFromRelHum(self.air_temp, self.rel_hum, self.pressure)
#             else:
#                 print("no wet bulb temperature, air temperature, or humidity provided. Assuming wet bulb as:", self.wet_bulb_temp) 



        
        

        
        
        
        
def unfix_inlet_to_train(self):
    if hasattr(self.parent_block(), "pfd_dict"):
        for key in self.parent_block().pfd_dict:
            if self.parent_block().pfd_dict[key]["type"] == "intake":
                print("unfixing intake:", key)
                getattr(self.parent_block(), key).flow_vol_in.unfix()
    else:
        print("assuming test with source1")
        self.parent_block().source1.flow_vol_in.unfix()
    
    
def set_plant_info(self, unit_params):
    if unit_params["fuel"] == "nuclear": 
        self.heat_sink = 0.0
        self.eff = 0.3
    if unit_params["fuel"] == "natural_gas_cc": 
        self.heat_sink = 0.2
        self.eff = 0.6
    if unit_params["fuel"] == "coal": 
        self.heat_sink = 0.12
        self.eff = 0.35        
        
    if "efficiency" in unit_params:
        print("thermal efficiency of plant set based on parameters to:", unit_params["efficiency"])
        self.eff = unit_params["efficiency"];
    else:
        print("assuming thermal efficiency of plant is:", self.eff)       
        
        
