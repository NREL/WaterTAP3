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

import numpy as np
# Import IDAES cores
from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import is_physical_parameter_block
# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from scipy.optimize import curve_fit

# Import WaterTAP# financials module
import financials
from financials import *  # ARIEL ADDED

# Import properties and units from "WaterTAP Library"

##########################################
####### UNIT PARAMETERS ######
# At this point (outside the unit), we define the unit parameters that do not change across case studies or analyses ######.
# Below (in the unit), we define the parameters that we may want to change across case studies or analyses. Those parameters should be set as variables (eventually) and atttributed to the unit model (i.e. m.fs.UNIT_NAME.PARAMETERNAME). Anything specific to the costing only should be in  m.fs.UNIT_NAME.costing.PARAMETERNAME ######
##########################################

## REFERENCE: Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)

### MODULE NAME ###
module_name = "cation_exchange"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2017


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
		time = self.flowsheet().config.time.first()
		# Get the inlet flow to the unit and convert to the correct units for cost module.
		flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
		### COSTING COMPONENTS SHOULD BE SET AS SELF.costing AND READ FROM A .CSV THROUGH A FUNCTION THAT SITS IN FINANCIALS ###
		# get tic or tpec (could still be made more efficent code-wise, but could enough for now)
		sys_cost_params = self.parent_block().costing_param
		self.costing.tpec_tic = sys_cost_params.tpec if tpec_or_tic == "TPEC" else sys_cost_params.tic
		tpec_tic = self.costing.tpec_tic

		def power_curve(x, a, b):
			return a * x ** b

		# basis year for the unit model - based on reference for the method.
		self.costing.basis_year = unit_basis_yr
		# conc_in = self.conc_mass_in[time, 'TDS'] * 1E3  # mg / L TDS
		base_fixed_cap_cost = 0.0089
		cap_scaling_exp = 0.8286
		flow_lst = np.array([4.732, 48.106, 339.425, 3566.804, 11840.768])  # m3 / hr
		elec_lst = np.array([0.082, 0.052, 0.035, 0.132, 0.109])  # kWh / m3
		elec_curve, _ = curve_fit(power_curve, flow_lst, elec_lst)
		a, b = elec_curve[0], elec_curve[1]

		# TODO -->> ADD THESE TO UNIT self.X

		#### CHEMS ###
		chem_name = ''
		chemical_dosage = 0  # kg/m3 should be read from .csv
		solution_density = 1  # kg/m3
		chemical_dosage = chemical_dosage / 264.172  # pyunits to kg/g

		chem_dict = {}

		##########################################
		####### UNIT SPECIFIC EQUATIONS AND FUNCTIONS ######
		##########################################

		# def solution_vol_flow(flow_in):  # m3/hr
		# flow_in_m3h = flow_in * 189.4204
		# chemical_rate = flow_in_m3h * chemical_dosage * 24  # kg/day
		#
		# return (chemical_rate / solution_density) * 264.17  # m3/day to gal/day

		def fixed_cap(flow_in):
			source_cost = base_fixed_cap_cost * flow_in ** cap_scaling_exp  # $

			return source_cost * tpec_tic  # M$

		def electricity(flow_in):  # m3/hr
			electricity = a * flow_in ** b  # kWh/m3

			return electricity

		# Get the first time point in the time domain
		# In many cases this will be the only point (steady-state), but lets be
		# safe and use a general approach

		# Get the inlet flow to the unit and convert to the correct units for cost module.

		## fixed_cap_inv_unadjusted ##
		self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
														   doc="Unadjusted fixed capital investment")  # $M

		self.chem_dict = chem_dict

		## electricity consumption ##
		self.electricity = electricity(flow_in)  # kwh/m3

		##########################################
		####### GET REST OF UNIT COSTS ######
		##########################################

		module.get_complete_costing(self.costing)
