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
from financials import * #ARIEL ADDED

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

## REFERENCE: Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)

### MODULE NAME ###
module_name = "chemical_addition"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2007

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
    
    # NOTE ---> THIS SHOULD EVENTUaLLY BE JUST FOR COSTING INFO/EQUATIONS/FUNCTIONS. EVERYTHING ELSE IN ABOVE.
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
        
        ##########################################
        ####### UNIT SPECIFIC VARIABLES AND CONSTANTS -> SET AS SELF OTHERWISE LEAVE AT TOP OF FILE ######
        ##########################################   
        
        ### COSTING COMPONENTS SHOULD BE SET AS SELF.costing AND READ FROM A .CSV THROUGH A FUNCTION THAT SITS IN FINANCIALS ###
        base_fixed_cap_cost = 900.97  # Carlsbad Treatment train VAR tab
        cap_scaling_exp = .6179  # Carlsbad Treatment train VAR tab
        fixed_op_cost_scaling_exp = 0.7
        
        # get tic or tpec (could still be made more efficent code-wise, but could enough for now)
        sys_cost_params = self.parent_block().costing_param
        self.costing.tpec_tic = sys_cost_params.tpec if tpec_or_tic == "TPEC" else sys_cost_params.tic
        tpec_tic = self.costing.tpec_tic
        
        # basis year for the unit model - based on reference for the method.
        self.costing.basis_year = unit_basis_yr
        
        # TODO -->> ADD THESE TO UNIT self.X 
        number_of_units = 2
        chemical_dosage = .01 # kg/m3
        solution_density = 1781 # kg/m3
        lift_height = 100 # ft
        
#         #### CAT AND CHEMS ariel todo ###
#         for chem_name in chemical_names:
#             chemical_dosage = chemical_info.get_dosage(chem_name, module_name) # kg/m3
#             solution_density = chemical_info.get_density(chem_name) # kg/m3
#             chemical_dosage = chemical_dosage / 264.172 # pyunits to kg/g
#             chem_dict[chem_name] = {"dosage" : chemical_dosage, "density": solution_density}
        
        self.parent_block().pfd_dict
        #### CAT AND CHEMS START ###
        Sulphuric_Acid_H2SO4 = 0.01 # MIKE kg/m3
        Sulphuric_Acid_H2SO4 = Sulphuric_Acid_H2SO4 / 264.172 # pyunits to kg/g
        
        chem_name = self.parent_block().pfd_dict.Parameter.
        
        chem_dict = {"Sulphuric_Acid_H2SO4" : Sulphuric_Acid_H2SO4}

        ##########################################
        ####### UNIT SPECIFIC EQUATIONS AND FUNCTIONS ######
        ##########################################
        
        def solution_vol_flow(flow_in): # m3/hr
            flow_in_m3h = flow_in * 189.4204
            chemical_rate = flow_in_m3h * chemical_dosage * 24 # kg/day
            
            return (chemical_rate / solution_density) * 264.17 # m3/day to gal/day
        
        
        def fixed_cap(flow_in):

            source_cost = base_fixed_cap_cost * solution_vol_flow(flow_in) ** cap_scaling_exp # $

            return (source_cost * tpec_tic * number_of_units)/1000000 # M$

        
        def electricity(flow_in): # m3/hr   
            flow_in_m3h = flow_in * 189.4204
            chemical_rate = flow_in_m3h * chemical_dosage * 24 # kg/day

            electricity = (.746 * (solution_vol_flow(flow_in) / 1440) * lift_height / (3960 * .9 * .9)) / flow_in_m3h # kWh/m3

            return electricity
        
        
        # Get the first time point in the time domain
        # In many cases this will be the only point (steady-state), but lets be
        # safe and use a general approach
        time = self.flowsheet().config.time.first()

        # Get the inlet flow to the unit and convert to the correct units for cost module.
        flow_in = pyunits.convert(self.flow_vol_in[time],
                                  to_units=pyunits.Mgallons/pyunits.day)
        
        
        ## fixed_cap_inv_unadjusted ##
        self.costing.fixed_cap_inv_unadjusted = Expression(
            expr=fixed_cap(flow_in),
            doc="Unadjusted fixed capital investment") # $M
        
        self.chem_dict = chem_dict
        
        ## electricity consumption ##
        self.electricity = electricity(flow_in) # kwh/m3
        
        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################        
        
        module.get_complete_costing(self.costing)
                        
        
        
           