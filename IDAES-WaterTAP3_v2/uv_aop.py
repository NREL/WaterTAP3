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
import numpy as np
import pandas as pd
# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock
from scipy.interpolate import interp1d # needed to interpolate and calculate cost

import generate_constituent_list
train_constituent_list = generate_constituent_list.run()
train_constituent_removal_factors = generate_constituent_list.get_removal_factors("uv_aop")


### FACTORS FOR ZEROTH ORDER MODEL -> TODO -> READ IN AUTOMATICALLY BASED ON UNIT PROCESS --> CREATE TABLE?!###
flow_recovery_factor = 0.99999
tds_removal_factor = 0

# Perfomance Parameter Values for Process: Constituent removals. # TODO- ARE THESE ACCURATE?

uv_dose_in = 100 # mJ / cm2 - needed to calculate UV performance (from TWB)
uvt_in = 0.88 # could be anything



# bacteria_removal, virus_removal, protozoa_removal, EEQ_removal, TOrC_removal, NDMA_removal, toc_removal_factor = uv_aop_removal(uv_dose_in)
PFOS_PFOA_removal = 0.0
nitrates_removal_factor = 0.0 
toc_removal_factor = 0
# capital costs basis
# Project Cost for Filter = $2.5M x (flow in mgd) page 55)
base_fixed_cap_cost = 9.721  # from TWB -> THIS IS SOMEHOW DIFFERENT FROM EXCEL CALCS NOT SURE WHY (3.125))
cap_scaling_exp = 0.402  # from TWB3
basis_year = 2014
recovery_factor = 1.0  ## ASSUMED AS 1.0 -> MUST BE WRONG -> CHECK
cost_method='wt'

fixed_op_cost_scaling_exp = 0.7
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
        return unit_process_equations.build_up(self, up_name_test = "uv_aop")
    
    
    def get_costing(self, module=financials, cost_method="wt", year=None):
        """
        We need a get_costing method here to provide a point to call the
        costing methods, but we call out to an external costing module
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
        
        # There are a couple of variables that IDAES expects to be present
        # These are fairly obvious, but have pre-defined names
        def _make_vars(self):
            # build generic costing variables (all costing models need these vars)
            self.base_cost = Var(initialize=1e5,
                                 domain=NonNegativeReals,
                                 doc='Unit Base Cost cost in $')
            self.purchase_cost = Var(initialize=1e4,
                                     domain=NonNegativeReals,
                                     doc='Unit Purchase Cost in $')
            
    
    
        # Build a costing method for each type of unit
        def up_costing(self, cost_method="wt"):
            
            '''
            This is where you create the variables and equations specific to each unit.
            This method should mainly consider capital costs for the unit - operating
            most costs should done for the entire flowsheet (e.g. common utilities).
            Unit specific operating costs, such as chemicals, should be done here with
            standard names that can be collected at the flowsheet level.

            You can access variables from the unit model using:

                self.parent_block().variable_name

            You can also have unit specific parameters here, which could be retrieved
            from the spreadsheet
            '''

            
            h2o2_flow = 600 # lb / d 
            h2o2_dose = 5 # from Excel
            dose_in = 80 # from Excel
            uvt_in = 0.76
            time = self.parent_block().flowsheet().config.time.first()

            flow_in = pyunits.convert(self.parent_block().flow_vol_in[time],
                                      to_units=pyunits.Mgallons/pyunits.day)
    
            def fixed_cap(dose_in, uvt_in, flow_in, h2o2_flow):
                uv_cost_csv = pd.read_csv('data/uv_cost.csv') # Needed to interpolate and calculate cost
                uv_cost_csv.set_index(['Flow', 'UVDose'], inplace=True) # Needed to interpolate and calculate cost
                flow_list = [1, 3, 5, 10, 25]
                flow_points = uv_cost_out(dose_in, uvt_in, uv_cost_csv, flow_list=flow_list) # Costing based off table on pg 57 of TWB
                params, _, _, _, _ = ml_regression.get_cost_curve_coefs(xs=flow_list, ys=flow_points)
                a, b = params[0], params[1]
                # h2o2_cost_only = (1418 * np.log(h2o2_flow - 3831)) / 1000 # H2O2 cost based on H2O2 flow; pg 59 of TWB
                h2o2_cost_only = 1228 * h2o2_flow ** 0.2277 / 1000 
                uv_aop_cap = (a * flow_in ** b) / 1000 + h2o2_cost_only
                return uv_aop_cap
            
            def electricity():
                return 0 
            
            _make_vars(self)
            
            self.base_fixed_cap_cost = Param(mutable=True,
                                              initialize=base_fixed_cap_cost,
                                              doc="Some parameter from TWB")
            self.cap_scaling_exp = Param(mutable=True,
                                         initialize=cap_scaling_exp,
                                         doc="Another parameter from TWB")
            
            ################### TWB METHOD ###########################################################
            if cost_method == "twb":
                    self.fixed_cap_inv_unadjusted = Expression(
                        expr=self.base_fixed_cap_cost *
                        (flow_in*pyunits.day/pyunits.Mgallon) ** self.cap_scaling_exp,
                        doc="Unadjusted fixed capital investment")
            ##############################################################################

            ################## WATERTAP METHOD ###########################################################
            if cost_method == "wt":

                # cost index values - TODO MOVE THIS TO TOP
                df = get_ind_table()
                self.cap_replacement_parts = df.loc[basis_year].Capital_Factor
                self.catalysts_chemicals = df.loc[basis_year].CatChem_Factor
                self.labor_and_other_fixed = df.loc[basis_year].Labor_Factor
                self.consumer_price_index = df.loc[basis_year].CPI_Factor

                # capital costs (unit: MM$) ---> TCI IN EXCEL
                self.fixed_cap_inv_unadjusted = Expression(
                    expr=fixed_cap(dose_in, uvt_in, flow_in, h2o2_flow),
                    doc="Unadjusted fixed capital investment") 
                
                self.fixed_cap_inv = self.fixed_cap_inv_unadjusted * self.cap_replacement_parts
                self.land_cost = self.fixed_cap_inv * land_cost_precent_FCI
                self.working_cap = self.fixed_cap_inv * working_cap_precent_FCI
                self.total_cap_investment = self.fixed_cap_inv + self.land_cost + self.working_cap
                self.electricity = 0
                
                cat_chem_df = pd.read_csv('data/catalyst_chemicals.csv', index_col = "Material")
                chem_cost_sum = 0 
                chem_dic = {'Hydrogen_Peroxide': h2o2_dose}
                checm_dic = {}
                for key in chem_dic.keys():
                    chem_cost = cat_chem_df.loc[key].Price
                    chem_cost_sum = chem_cost_sum + (self.parent_block().flow_vol_in[time] * chem_cost * self.catalysts_chemicals * chem_dic[key] * on_stream_factor * 365 * 24 * 3600 / 1000) 
                self.cat_and_chem_cost = chem_cost_sum / 1000000  # TODO
                
                flow_in_m3yr = (pyunits.convert(self.parent_block().flow_vol_in[time],
                                      to_units=pyunits.m**3/pyunits.year))
                self.electricity_cost = Expression(
                    expr=(self.electricity * flow_in_m3yr * elec_price / 1000000),
                    doc='Electricity cost') # KWh/day * $/KWh * 365 days
                
                self.other_var_cost = 0

                # fixed operating cost (unit: MM$/yr)  ---> FIXED IN EXCEL
                self.base_employee_salary_cost = self.fixed_cap_inv_unadjusted * salaries_percent_FCI
                self.salaries = Expression(
                    expr=self.labor_and_other_fixed * self.base_employee_salary_cost,
                    doc='Salaries')
                self.benefits = self.salaries * benefit_percent_of_salary
                self.maintenance = maintinance_costs_precent_FCI * self.fixed_cap_inv
                self.lab = lab_fees_precent_FCI * self.fixed_cap_inv
                self.insurance_taxes = insurance_taxes_precent_FCI * self.fixed_cap_inv
                self.total_fixed_op_cost = Expression(
                    expr = self.salaries + self.benefits + self.maintenance + self.lab + self.insurance_taxes)

                self.total_up_cost = (
                    self.total_cap_investment
                    + self.cat_and_chem_cost
                    + self.electricity_cost
                    + self.other_var_cost
                    + self.total_fixed_op_cost
                )
                
    
        up_costing(self.costing, cost_method=cost_method)
          
        
# OTHER CALCS

def create(m, up_name):
    
    # Set removal and recovery fractions
    getattr(m.fs, up_name).water_recovery.fix(flow_recovery_factor)
    
    for constituent_name in getattr(m.fs, up_name).config.property_package.component_list:
        
        if constituent_name in train_constituent_removal_factors.keys():
            getattr(m.fs, up_name).removal_fraction[:, constituent_name].fix(train_constituent_removal_factors[constituent_name])
        else:
            getattr(m.fs, up_name).removal_fraction[:, constituent_name].fix(0)

    # Also set pressure drops - for now I will set these to zero
    getattr(m.fs, up_name).deltaP_outlet.fix(1e-4)
    getattr(m.fs, up_name).deltaP_waste.fix(1e-4)

    # Adding costing for units - this is very basic for now so use default settings
    getattr(m.fs, up_name).get_costing(module=financials)

    return m  

# def get_additional_variables(self, units_meta, time):
#     self.uvt_in = Var(time, initialize=0.85, units=pyunits.dimensionless, doc="UV transmission %") 
    

def uv_cost_interp_dose(df, min_interp, max_interp, inc_interp, kind='linear',
                        dose_list=[10, 20, 50, 100, 200, 300, 500, 800, 1000], uvt_list=[0.55, 0.6, 0.65, 0.7, 0.75, 0.85, 0.9, 0.95]):
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

def uv_cost_interp_uvt(df, min_interp, max_interp, inc_interp, 
                       kind='linear',
                       dose_list=[10, 20, 50, 100, 200, 300, 500, 800, 1000], 
                       uvt_list=[0.55, 0.6, 0.65, 0.7, 0.75, 0.85, 0.9, 0.95]):
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
    
def uv_cost_out(dose_in, uvt_in, uv_cost_csv,
                dose_list=[10, 20, 50, 100, 200, 300, 500, 800, 1000],
                flow_list = [1, 3, 5, 10, 25],
                kind='linear', 
                min_interp_flow=0.5, max_interp_flow=50, inc_interp_flow=0.1,
                min_interp_uvt=0.5, max_interp_uvt=0.99, inc_interp_uvt=0.01,
                min_interp_dose=5, max_interp_dose=1500, inc_interp_dose=1):    
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
    
    
    
    
    
    
    