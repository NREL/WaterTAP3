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

# Import WaterTAP# financials module
import financials
from financials import *

from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import Arc
from idaes.core import FlowsheetBlock

# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock

##########################################
####### UNIT PARAMETERS ######
# At this point (outside the unit), we define the unit parameters that do not change across case studies or analyses ######.
# Below (in the unit), we define the parameters that we may want to change across case studies or analyses. Those parameters should be set as variables (eventually) and atttributed to the unit model (i.e. m.fs.UNIT_NAME.PARAMETERNAME). Anything specific to the costing only should be in  m.fs.UNIT_NAME.costing.PARAMETERNAME ######
##########################################

## REFERENCE:backwash_solids_handling unit process based on costs for Solids Handling in Table 5.7.1 in Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)

### MODULE NAME ###
module_name = "backwash_solids_handling"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2007

filter_backwash_pumping_cost = 186458
surface_wash_system = 99941
air_scour_system = 463853
wash_water_surge_basins = 770643
wash_water_storage_tank = 216770
gravity_sludge_thickener = 94864
sludge_dewatering_lagoons = 4173
sand_drying_beds = 45801

filter_backwash_pumping_cost_units = 2
surface_wash_system_units = 2
air_scour_system_units = 2
wash_water_surge_basins_units = 1
wash_water_storage_tank_units = 1
gravity_sludge_thickener_units = 1
sludge_dewatering_lagoons_units = 3
sand_drying_beds_units = 6


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
        # First, check to see if global costing module is in place
        # Construct it if not present and pass year argument
        if not hasattr(self.flowsheet(), "costing"):
            self.flowsheet().get_costing(module=module, year=year)

        # Next, add a sub-Block to the unit model to hold the cost calculations
        # This is to let us separate costs from model equations when solving
        self.costing = Block()
        # Then call the appropriate costing function out of the costing module
        # The first argument is the Block in which to build the equations
        # Can pass additional arguments as needed
        
        # capital costs basis
        self.base_fixed_cap_cost = 9.76 # from PML tab, for the kg/hr and not consistent with the usual flow rate cost curves TODO
        self.cap_scaling_exp = .918  # from PML tab, for the kg/hr and not consistent with the usual flow rate cost curves TODO 
        self.fixed_op_cost_scaling_exp = 0.7

        # get tic or tpec (could still be made more efficent code-wise, but could enough for now)
        sys_cost_params = self.parent_block().costing_param
        self.costing.tpec_tic = sys_cost_params.tpec if tpec_or_tic == "TPEC" else sys_cost_params.tic
        tpec_tic = self.costing.tpec_tic 
        
        # basis year for the unit model - based on reference for the method.
        self.costing.basis_year = unit_basis_yr
    
        time = self.flowsheet().config.time.first()
        conc_mass_tot = 0     
        
        for constituent in self.config.property_package.component_list:
            conc_mass_tot = conc_mass_tot + self.conc_mass_in[time, constituent] 
        
        self.conc_mass_tot = conc_mass_tot
        density = 0.6312 * conc_mass_tot + 997.86 #kg/m3 # assumption from Tim's reference (ask Ariel for Excel if needed)
        self.total_mass = (density * self.flow_vol_in[time] * 3600) #kg/hr for Mike's Excel needs
        total_flow_rate = self.total_mass #kg/hr
        
        #self.water_recovery.fix(unit_params["recovery"])
        
        lift_height = 100 # ft

        def fixed_cap(total_flow_rate): # TODO not based on flow, just have placeholder numbers for Carlsbad

            fc = filter_backwash_pumping_cost * filter_backwash_pumping_cost_units
            sc = surface_wash_system * surface_wash_system_units
            ac = air_scour_system * air_scour_system_units 
            sb = wash_water_surge_basins * wash_water_surge_basins_units 
            st = wash_water_storage_tank * wash_water_storage_tank_units
            gs = gravity_sludge_thickener * gravity_sludge_thickener_units 
            sd = sludge_dewatering_lagoons *  sludge_dewatering_lagoons_units
            db = sand_drying_beds * sand_drying_beds_units

            costs_list = [fc, sc, ac, sb, st, gs, sd, db]

            scaling_factor_list = [1.000, 1.000, 1.000, 0.751, 0.847, 1.305, 0.714, 0.875] # ANNA CHANGE TO VARIABLES

            base_fixed_cap_cost = sum(costs_list)/1000000 # $M

            cap_scaling_exp = sum(x * y for x, y in zip(scaling_factor_list, costs_list)) / sum(costs_list)

            capacity_basis = 1577255 # m3/s to kg/hr - CONSTANT BASED ON ASSUMPTION OF 100MGD BASIS

            fixed_cap_unadj = self.base_fixed_cap_cost * (total_flow_rate / capacity_basis) ** self.cap_scaling_exp

            return fixed_cap_unadj # M$
 
               
        def electricity(flow_in): # m3/hr
            flow_in_gpm = pyunits.convert(self.flow_vol_in[time],
                                  to_units=pyunits.gallons/pyunits.minute)
            flow_in_m3h = pyunits.convert(self.flow_vol_in[time],
                                  to_units=pyunits.m**3/pyunits.hour)
            electricity = (.746 * flow_in_gpm * lift_height / (3960 * .9 * .9)) / flow_in_m3h # kWh/m3

            return (electricity/1000) # grid_electricity PML value is divided by 1000- ask Mike
    

        # Get the inlet flow to the unit and convert to the correct units
        flow_in = pyunits.convert(self.flow_vol_in[time],
                                  to_units=pyunits.Mgallons/pyunits.day)

        
        # capital costs (unit: MM$) ---> TCI IN EXCEL
        self.costing.fixed_cap_inv_unadjusted = Expression(
            expr=fixed_cap(total_flow_rate),
            doc="Unadjusted fixed capital investment") 

        self.electricity = electricity(flow_in) # kwh/m3 
                        
        self.chem_dict = {}
        
        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################        
        
        module.get_complete_costing(self.costing)
           
        
        
        