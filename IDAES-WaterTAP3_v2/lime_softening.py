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

## REFERENCE:### data specific to UP - should probably be a chemical addition class ###
### TODO check these against original source:
# Minnesota Rural Water Association, Chapter 16 Lime Softening #(https://www.mrwa.com/WaterWorksMnl/Chapter%2016%20Lime%20Softening.pdf)
# https://www.necoindustrialwater.com/analysis-ion-exchange-vs-lime-softening/

### MODULE NAME ###
module_name = "lime_softening"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2020


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

	# build(up_name = "nanofiltration_twb")

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

		# Get the first time point in the time domain
		# In many cases this will be the only point (steady-state), but lets be
		# safe and use a general approach
		time = self.flowsheet().config.time.first()

		# Get the inlet flow to the unit and convert to the correct units
		flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

		# capital costs basis
		base_fixed_cap_cost = 0.0704  # from VAR tab
		cap_scaling_exp = 0.7306  # from VAR tab

		# basis year for the unit model - based on reference for the method.
		self.costing.basis_year = unit_basis_yr

		#### CAT AND CHEMS START ###
		# these are the constituents in the inlet water assuming seawater 35 g/L -> ASSUMED TO ONLY BE VALID FOR CARLSBAD?
		co2 = 1.27  # mg/L NOT USED
		bicarb_alk_CaCO3 = 0.56  # mg/L NOT USED
		hydrox_alk_CaCO3 = 0.56  # mg/L NOT USED
		chem_name = unit_params["chemical_name"]
		magnesium_dissolved_lime = pyunits.convert(unit_params["lime"] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
		magnesium_dissolved_factor = 30 * pyunits.dimensionless  # TODO
		chemical_dosage = magnesium_dissolved_factor * magnesium_dissolved_lime
		lift_height = 100 * pyunits.ft
		pump_eff = 0.9 * pyunits.dimensionless
		motor_eff = 0.9 * pyunits.dimensionless
		solution_density = 1250 * (pyunits.kg / pyunits.m ** 3)  # kg/m3

		# assumed to be Lime_Suspension_(Ca(OH)2). kg/m3
		# chemical_dosage = chemical_dosage / 264.172 # converted to kg/gal todo in pyunits
		def solution_vol_flow(flow_in):  # m3/hr
			chemical_rate = flow_in * chemical_dosage  # kg/hr
			chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.kg / pyunits.day))
			soln_vol_flow = chemical_rate / solution_density  # m3 / d
			return soln_vol_flow  # m3 / d

		def fixed_cap(flow_in):
			lime_cap = base_fixed_cap_cost * flow_in ** cap_scaling_exp

			return lime_cap

		def electricity(flow_in):  # m3/hr
			soln_vol_flow = pyunits.convert(solution_vol_flow(flow_in), to_units=(pyunits.gallon / pyunits.minute))
			electricity = (0.746 * soln_vol_flow * lift_height / (3960 * pump_eff * motor_eff)) / flow_in  # kWh/m3
			return electricity

		#### CHEMS ###
		chem_dict = {chem_name: chemical_dosage}
		self.chem_dict = chem_dict

		self.electricity = electricity(flow_in)

		self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in), doc="Unadjusted fixed capital investment")

		##########################################
		####### GET REST OF UNIT COSTS ######
		##########################################

		module.get_complete_costing(self.costing)
