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
from idaes.core import (declare_process_block_class, UnitModelBlockData, useDefault)
from idaes.core.util.config import is_physical_parameter_block

from pyomo.environ import (Expression, Var, Param, NonNegativeReals, units as pyunits)

# Import WaterTAP financials module
import financials
from financials import *  # ARIEL ADDED

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

## REFERENCE: #https://www.mrwa.com/WaterWorksMnl/Chapter%2012%20Coagulation.pdf; Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura); https://www.iwapublishing.com/news/coagulation-and-flocculation-water-and-wastewater-treatment; Water and Wastewater Engineering: Design Principles and Practice (Mackenzie L. Davis)
#### chem additions ###
# https://www.mrwa.com/WaterWorksMnl/Chapter%2012%20Coagulation.pdf
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)
# https://www.iwapublishing.com/news/coagulation-and-flocculation-water-and-wastewater-treatment
# Water and Wastewater Engineering: Design Principles and Practice (Mackenzie L. Davis)

### MODULE NAME ###
module_name = "coag_and_floc"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2020


### NEED TO MOVE THIS TO PARAMS? TODO ###


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

    from unit_process_equations import initialization
    # unit_process_equations.get_base_unit_process()

    # build(up_name = "coag_and_floc")

    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test=module_name)

    def get_costing(self, module=financials, cost_method="wt", year=None, unit_params=None):
        """
        We need a get_costing method here to provide a point to call the
        costing methods, but we call out to an external consting module
        for the actual calculations. This lets us easily swap in different
        methods if needed.

        Within IDAES, the year argument is used to set the initial value for
        the cost index when we build the model.
        """

        # Adapted from Jenny's excel "Coagulation and Flocculation with Aluminmum Sulfate" version in WaterTAP3 VAR tab
        # Sources: https://www.mrwa.com/WaterWorksMnl/Chapter%2012%20Coagulation.pdf
        # Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)
        # https://www.iwapublishing.com/news/coagulation-and-flocculation-water-and-wastewater-treatment

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
        time = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        # up_costing(self.costing, cost_method=cost_method)

        # There are a couple of variables that IDAES expects to be present
        # These are fairly obvious, but have pre-defined names
        alum_dose = pyunits.convert(unit_params['alum_dose'] * (pyunits.mg / pyunits.L), to_units=(pyunits.kg / pyunits.m ** 3))  # mg/L # MIKE ASSUMPTION NEEDED
        polymer_dose = pyunits.convert(unit_params['polymer_dose'] * (pyunits.mg / pyunits.L), to_units=(pyunits.kg / pyunits.m ** 3))  # mg/L # MIKE ASSUMPTION NEEDED

        an_polymer = polymer_dose / 2  # MIKE ASSUMPTION NEEDED
        cat_polymer = polymer_dose / 2  # MIKE ASSUMPTION NEEDED
        chem_dict = {"Aluminum_Al2_SO4_3": alum_dose, "Anionic_Polymer": an_polymer, "Cationic_Polymer": cat_polymer}
        # Coagulation and Flocculation (High G) with Aluminum Sulfate
        rapid_mixers = 1
        floc_mixers = 3
        rapid_mix_processes = 1
        floc_processes = 2
        coag_processes = 1
        floc_injection_processes = 1
        poly_dosage = 0.1 * (pyunits.mg / pyunits.liter)  # mg/L dosage rate
        rapid_mix_retention_time = 5.5 * pyunits.seconds  # seconds (rapid mix)
        floc_retention_time = 12 * pyunits.minutes  # minutes
        al2so43_density = (8.34 * 1.33) * (pyunits.pound / pyunits.gallon)  # lb/gal
        alum_dosage = 10 * (pyunits.mg / pyunits.liter)  # mg/L dosage rate

        self.chem_dict = chem_dict

        # capital costs basis
        self.base_fixed_cap_cost = 0.0968  # + 1.6389? # ANNA - IS THIS USED?!?!?
        self.cap_scaling_exp = 1  # ANNA - IS THIS USED?!?!?

        # get tic or tpec (could still be made more efficent code-wise, but could enough for now)
        sys_cost_params = self.parent_block().costing_param
        self.costing.tpec_tic = sys_cost_params.tpec if tpec_or_tic == "TPEC" else sys_cost_params.tic
        tpec_tic = self.costing.tpec_tic

        # basis year for the unit model - based on reference for the method.
        self.costing.basis_year = unit_basis_yr

        # calculations are in GPM? ANNA CHECK
        def fixed_cap(flow_in):
            flow_in_gpm = pyunits.convert(flow_in, to_units=pyunits.gallons / pyunits.minute)  # MGD to GPM
            rapid_mix_basin_volume = pyunits.convert(rapid_mix_retention_time, to_units=pyunits.minutes) * flow_in_gpm  # gallons
            floc_basin_volume = floc_retention_time * flow_in_gpm  # gallons
            alum_flow = alum_dose * flow_in  # kg / hr
            alum_flow = alum_flow * 2.2046  # lb / hr
            poly_flow = poly_dosage * flow_in  # kg / hr
            poly_flow = poly_flow * 2.2046  # lb / hr

            rapid_G = (7.0814 * rapid_mix_basin_volume + 33269) * rapid_mix_processes  # $
            floc_G = (952902 * (floc_basin_volume * 1E-6) + 177335) * floc_processes  # $
            coag_injection = (212.32 * alum_flow + 73225) * coag_processes  # $
            floc_injection = (13662 * poly_flow * 24 + 20861) * floc_injection_processes  # $

            return ((rapid_G + floc_G + coag_injection + floc_injection) * 1E-6) * tpec_tic  # $M

        def electricity(flow_in):  # TODO
            flow_in_gpm = pyunits.convert(flow_in, to_units=pyunits.gallons / pyunits.minute)  # MGD to GPM
            flow_in_m3h = pyunits.convert(flow_in, to_units=pyunits.m ** 3 / pyunits.hour)  # MGD to m3/hr

            rapid_mix_basin_volume = (pyunits.convert(rapid_mix_retention_time, to_units=pyunits.minutes) * flow_in_gpm)
            rapid_mix_basin_volume = pyunits.convert(rapid_mix_basin_volume, to_units=pyunits.m ** 3)  # gallons to m3

            rapid_mix_power_consumption = 900 ** 2 * 0.001 * rapid_mix_basin_volume  # W
            rapid_mix_power = rapid_mix_power_consumption * rapid_mixers  # W

            floc_basin_volume = floc_retention_time * flow_in_gpm / 264.172  # gallons to m3
            floc_power_consumption = 80 ** 2 * 0.001 * floc_basin_volume  # W
            floc_mix_power = floc_power_consumption * floc_mixers  # W

            total_power = rapid_mix_power + floc_mix_power
            total_power_per_m3 = (total_power / 1000) / flow_in_m3h  # TODO

            return total_power_per_m3  # kWh/m3 ANNA THIS SHOULD BE PER

        # Get the inlet flow to the unit and convert to the correct units

        # capital costs (unit: MM$) ---> TCI IN EXCEL
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in), doc="Unadjusted fixed capital investment")

        ## electricity consumption ##
        self.electricity = electricity(flow_in)  # kwh/m3

        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################

        module.get_complete_costing(self.costing)
