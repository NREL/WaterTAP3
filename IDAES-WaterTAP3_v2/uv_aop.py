#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  5 13:26:35 2021

@author: ksitterl
"""

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
from idaes.core import (declare_process_block_class, UnitModelBlockData, useDefault)
from idaes.core.util.config import is_physical_parameter_block
# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from scipy.interpolate import interp1d

# Import WaterTAP# financials module
import financials
from financials import *  # ARIEL ADDED

##########################################
####### UNIT PARAMETERS ######
# At this point (outside the unit), we define the unit parameters that do not change across case studies or analyses ######.
# Below (in the unit), we define the parameters that we may want to change across case studies or analyses. Those parameters should be set as variables (eventually) and atttributed to the unit model (i.e. m.fs.UNIT_NAME.PARAMETERNAME). Anything specific to the costing only should be in  m.fs.UNIT_NAME.costing.PARAMETERNAME ######
##########################################

## REFERENCE: Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)

### MODULE NAME ###
module_name = "uv_aop"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2014


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

		### COSTING COMPONENTS SHOULD BE SET AS SELF.costing AND READ FROM A .CSV THROUGH A FUNCTION THAT SITS IN FINANCIALS ###
		time = self.flowsheet().config.time.first()
		flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hour)  # m3 /hr
		# get tic or tpec (could still be made more efficent code-wise, but could enough for now)
		sys_cost_params = self.parent_block().costing_param
		self.costing.tpec_tic = sys_cost_params.tpec if tpec_or_tic == "TPEC" else sys_cost_params.tic
		tpec_tic = self.costing.tpec_tic

		# basis year for the unit model - based on reference for the method.
		self.costing.basis_year = unit_basis_yr

		# TODO -->> ADD THESE TO UNIT self.X

		dose_in = unit_params['uv_dose'] * (pyunits.millijoule / pyunits.cm ** 2)  # from Excel
		# uvt_in = self.conc_mass_in[time, "ultraviolet_transmittance_uvt"]
		uvt_in = 0.68  # constant from EXCEL for Santa Barbara, needs to be read in dynamically
		#### CHEMS ###
		aop = unit_params['aop']
		if aop:
			chemical_dosage = pyunits.convert(unit_params['dose'] * (pyunits.mg / pyunits.L), to_units=(pyunits.kg / pyunits.m ** 3))
			chem_name = unit_params["chemical_name"][0]
			chem_dict = {chem_name: chemical_dosage}
			h2o2_base_cap = 1228
			h2o2_cap_exp = 0.2277
		else:
			chem_dict = {}

		self.chem_dict = chem_dict

		##########################################
		####### UNIT SPECIFIC EQUATIONS AND FUNCTIONS ######
		##########################################
		def uv_cost_interp_dose(df, min_interp, max_interp, inc_interp, kind='linear', dose_list=[10, 20, 50, 100, 200, 300, 500, 800, 1000], uvt_list=[0.55, 0.6, 0.65, 0.7, 0.75, 0.85, 0.9, 0.95]):
			cost_out = pd.DataFrame()
			x = np.arange(min_interp, max_interp + inc_interp, inc_interp)
			for i, uvt in enumerate(uvt_list):
				cost = df.iloc[:, i]
				interp = interp1d(dose_list, cost, kind=kind, fill_value='extrapolate')
				y = interp(x)
				cost_out[uvt] = pd.Series(y)
			x = map(lambda x: round(x), x)
			cost_out.set_index(x, inplace=True)
			return cost_out

		def uv_cost_interp_uvt(df, min_interp, max_interp, inc_interp, kind='linear', dose_list=[10, 20, 50, 100, 200, 300, 500, 800, 1000], uvt_list=[0.55, 0.6, 0.65, 0.7, 0.75, 0.85, 0.9, 0.95]):
			cost_out = pd.DataFrame()
			x = np.arange(min_interp, max_interp + inc_interp, inc_interp)
			for i, d in enumerate(df.index):
				cost = df.iloc[i, :]
				interp = interp1d(uvt_list, cost, kind=kind, fill_value='extrapolate')
				y = interp(x)
				cost_out[d] = pd.Series(y)
			x = map(lambda x: round(x, 2), x)
			cost_out.set_index(x, inplace=True)
			cost_out = cost_out.T
			return cost_out

		def uv_cost_out(dose_in, uvt_in, uv_cost_csv, dose_list=[10, 20, 50, 100, 200, 300, 500, 800, 1000], flow_list=[1, 3, 5, 10, 25], kind='linear', min_interp_flow=0.5, max_interp_flow=50,
		                inc_interp_flow=0.1, min_interp_uvt=0.5, max_interp_uvt=0.99, inc_interp_uvt=0.01, min_interp_dose=5, max_interp_dose=1500, inc_interp_dose=1):
			# Empty list to store points for each UV Dose level
			flow_points = []
			for flow in flow_list:
				# Raw data from TWB table
				cost = uv_cost_csv.loc[flow]
				# Interpolate across dose
				cost = uv_cost_interp_dose(cost, min_interp_dose, max_interp_dose, inc_interp_dose, kind=kind)
				# Interpolate across UVT
				cost = uv_cost_interp_uvt(cost, min_interp_uvt, max_interp_uvt, inc_interp_uvt, kind=kind)

				flow_points.append(cost[uvt_in][dose_in])

			return flow_points

		def solution_vol_flow(flow_in):  # m3/hr
			chemical_rate = flow_in * chemical_dosage  # kg/hr
			chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.lb / pyunits.day))
			soln_vol_flow = chemical_rate
			return soln_vol_flow  # lb / day

		def fixed_cap(flow_in):
			uv_cost_csv = pd.read_csv('data/uv_cost.csv')  # Needed to interpolate and calculate cost
			uv_cost_csv.set_index(['Flow', 'UVDose'], inplace=True)  # Needed to interpolate and calculate cost
			flow_list = [1, 3, 5, 10, 25]  # flow in mgd
			flow_points = uv_cost_out(dose_in, uvt_in, uv_cost_csv, flow_list=flow_list)  # Costing based off table on pg 57 of TWB
			params, _, _, _, _ = ml_regression.get_cost_curve_coefs(xs=flow_list, ys=flow_points)
			a, b = params[0], params[1]
			if aop:
				h2o2_cap = h2o2_base_cap * solution_vol_flow(flow_in) ** h2o2_cap_exp
				flow_in = pyunits.convert(flow_in, to_units=(pyunits.Mgallons / pyunits.day))
				uv_aop_cap = (a * flow_in ** b + h2o2_cap) * 1E-3
			else:
				flow_in = pyunits.convert(flow_in, to_units=(pyunits.Mgallons / pyunits.day))
				uv_aop_cap = (a * flow_in ** b) * 1E-3
			return uv_aop_cap

		def electricity(flow_in):  # m3/hr
			electricity = 0.1  # kWh / m3
			return electricity

		## fixed_cap_inv_unadjusted ##
		self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in), doc="Unadjusted fixed capital investment")  # $M

		## electricity consumption ##
		self.electricity = electricity(flow_in)  # kwh/m3

		##########################################
		####### GET REST OF UNIT COSTS ######
		##########################################

		module.get_complete_costing(self.costing)
