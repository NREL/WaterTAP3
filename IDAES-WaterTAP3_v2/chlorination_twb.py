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

from pyomo.network import Arc, SequentialDecomposition
import numpy as np
import pandas as pd

# Set inlet conditions to first unit
# IDAES Does have Feed components for this, but that would require a bit
# more work to set up to work (as it relies on things in the property package
# that aren't implemented for this example).
# I am just picking numbers for most of these


### FACTORS FOR ZEROTH ORDER MODEL -> TODO -> READ IN AUTOMATICALLY BASED ON UNIT PROCESS --> CREATE TABLE?!###

#########################################################################
#########################################################################

contact_time = 1.5  # hours
contact_time_mins = 1.5 * 60
ct = 450  # mg/L-min ---> ASSUME CALI STANDARD FOR NOW
chlorine_decay_rate = 3.0  # mg/Lh

# TO DO:
# Chlorine Consumption?
# Trace Organic Chemicals (TOrC)
# Estradiol Equivalency (EEQ)
# Giardia lamblia
# Total Coliforms (including fecal coliform and E. Coli)
# Viruses (enteric)

flow_recovery_factor = .99999  ## ASSUMED AS 1.0

base_fixed_cap_cost = 2.5081
cap_scaling_exp = 0.3238

basis_year = 2014
fixed_op_cost_scaling_exp = 0.7

cost_method = "wt"

# Get constituent list and removal rates for this unit process
import generate_constituent_list
train_constituent_list = generate_constituent_list.run()
train_constituent_removal_factors = generate_constituent_list.get_removal_factors("chlorination_twb")

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

    #build(up_name = "chlorination_twb")
    
    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test = "chlorination_twb")
    
    
   
    def get_costing(self, module=financials, cost_method=cost_method, year=None):
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
        
        #up_costing(self.costing, cost_method=cost_method)
        
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
    

        def get_chlorine_dose_cost(flow_in, dose): # flow in mgd for this cost curve

            import ml_regression
            df = pd.read_csv("data/chlorine_dose_cost_twb.csv") # % dir_path)  # import data
            #df = df[df.Dose != 15] # removing 15 because it would not provide an accurate cost curve - tables assume 10 and 15
            # dose is the same. 15 vs. 10 gives a higher price.

            new_dose_list = np.arange(0, 25.1, 0.5)

            cost_list = []
            flow_list = []
            dose_list = []

            for flow in df.Flow_mgd.unique():
                df_hold = df[df.Flow_mgd == flow]
                del df_hold['Flow_mgd']

                if 0 not in df_hold.Cost.values:
                    xs = np.hstack((0, df_hold.Dose.values)) # dont think we need the 0s
                    ys = np.hstack((0, df_hold.Cost.values)) # dont think we need the 0s
                else:
                    xs = df_hold.Dose.values
                    ys = df_hold.Cost.values

                a = ml_regression.get_cost_curve_coefs(xs = xs, ys = ys)[0][0]
                b = ml_regression.get_cost_curve_coefs(xs = xs, ys = ys)[0][1]

                for new_dose in new_dose_list:
                    if new_dose in df.Dose:
                        if flow in df.Flow_mgd:
                            cost_list.append(df[((df.Dose == new_dose) & (df.Flow_mgd == flow))].Cost.max())
                        else:
                            cost_list.append(a * new_dose ** b)
                    else:
                        cost_list.append(a * new_dose ** b)

                    dose_list.append(new_dose)
                    flow_list.append(flow)

            dose_cost_table = pd.DataFrame()
            dose_cost_table["flow_mgd"] = flow_list
            dose_cost_table["dose"] = dose_list
            dose_cost_table["cost"] = cost_list
            
            #print("dose:", dose)
            df1 = dose_cost_table[dose_cost_table.dose == dose]
            xs = np.hstack((0, df1.flow_mgd.values)) # dont think we need the 0s
            ys = np.hstack((0, df1.cost.values)) # dont think we need the 0s
            #print(xs)
            #print(df1)
            a = ml_regression.get_cost_curve_coefs(xs = xs, ys = ys)[0][0]
            b = ml_regression.get_cost_curve_coefs(xs = xs, ys = ys)[0][1]

            return (a * flow_in ** b) / 1000 # convert to mil
    
    
        # Build a costing method for each type of unit
        def up_costing(self, cost_method=cost_method):
            
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
            #_make_vars(self)

            self.base_fixed_cap_cost = Param(mutable=True,
                                             initialize=base_fixed_cap_cost,
                                             doc="Some parameter from TWB")
            self.cap_scaling_exp = Param(mutable=True,
                                         initialize=cap_scaling_exp,
                                         doc="Another parameter from TWB")

            # Get the first time point in the time domain
            # In many cases this will be the only point (steady-state), but lets be
            # safe and use a general approach
            time = self.parent_block().flowsheet().config.time.first()

            # Get the inlet flow to the unit and convert to the correct units
            flow_in = pyunits.convert(self.parent_block().flow_vol_in[time],
                                      to_units=pyunits.Mgallons/pyunits.day)

            
            ###### 
            #initial_chlorine_demand = get_cl2_dem(G)
            #self.applied_cl2_dose = self.cl2_dem + chlorine_decay_rate * contact_time + ct / contact_time_mins
            self.applied_cl2_dose = chlorine_decay_rate * contact_time + ct / contact_time_mins
            #self.parent_block().cl2_dem[time]
            ################### TWB METHOD ###########################################################
            if cost_method == "twb":
                self.fixed_cap_inv_unadjusted = get_chlorine_dose_cost(flow_in*pyunits.day, self.applied_cl2_dose) / 1000
                #Expression(
                #    get_chlorine_dose_cost(flow_in*pyunits.day, self.applied_cl2_dose), # / 1000, #TODO check units
                #    doc="Unadjusted fixed capital investment")
                

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
                self.fixed_cap_inv_unadjusted = get_chlorine_dose_cost(flow_in, self.applied_cl2_dose) # $M

                self.fixed_cap_inv = self.fixed_cap_inv_unadjusted * self.cap_replacement_parts
                self.land_cost = self.fixed_cap_inv * land_cost_precent_FCI
                self.working_cap = self.fixed_cap_inv * working_cap_precent_FCI
                self.total_cap_investment = self.fixed_cap_inv + self.land_cost + self.working_cap

                # variable operating costs (unit: MM$/yr) -> MIKE TO DO -> ---> CAT+CHEM IN EXCEL
                # --> should be functions of what is needed!?
                # cat_chem_df = pd.read_csv('catalyst_chemicals.csv')
                # cat_and_chem = flow_in * 365 * on_stream_factor # TODO
                
                self.electricity = .000005689  # kwh/m3 given in PML tab, no source TODO
                
                cat_chem_df = pd.read_csv('data/catalyst_chemicals.csv', index_col = "Material")
                chem_cost_sum = 0 
                
                chem_dic = {"Chlorine" : self.applied_cl2_dose}
                
                for key in chem_dic.keys():
                    chem_cost = cat_chem_df.loc[key].Price
                    chem_cost_sum = flow_in * chem_cost_sum + self.catalysts_chemicals * 365 * chem_cost * chem_dic[key] * on_stream_factor * 3.78541178 # 3.78541178 for mg/L to kg/gallon
                
                self.cat_and_chem_cost = chem_cost_sum / 1000000 # to million $
                
                flow_in_m3yr = (pyunits.convert(self.parent_block().flow_vol_in[time],
                                      to_units=pyunits.m**3/pyunits.year))
                self.electricity_cost = Expression(
                        expr= (self.electricity * flow_in_m3yr * elec_price/1000000),
                        doc="Electricity cost") # M$/yr
                
                self.other_var_cost = 0 # Expression(
                        #expr= self.cat_and_chem_cost - self.electricity_cost,
                        #doc="Other variable cost")

                # fixed operating cost (unit: MM$/yr)  ---> FIXED IN EXCEL
#                 self.base_employee_salary_cost = get_chlorine_dose_cost(flow_in, self.applied_cl2_dose) * salaries_percent_FCI
#                 self.salaries = (
#                     self.labor_and_other_fixed
#                     * self.base_employee_salary_cost
#                     * flow_in ** fixed_op_cost_scaling_exp
#                 ) # $M
                
                
#                 self.salaries = (
#                     (self.labor_and_other_fixed ** fixed_op_cost_scaling_exp) * (salaries_percent_FCI 
#                           * self.fixed_cap_inv_unadjusted) ** fixed_op_cost_scaling_exp)
               
                self.base_employee_salary_cost = self.fixed_cap_inv_unadjusted * salaries_percent_FCI
                self.salaries = Expression(
                        expr= self.labor_and_other_fixed * self.base_employee_salary_cost,
                        doc="Salaries")
                
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

            #return total_up_cost
    
        up_costing(self.costing, cost_method=cost_method)
          
        
# OTHER CALCS

def get_cl2_dem(m):
    # unit is mg/L. order matters in this list. need a better way.

    seq = SequentialDecomposition()
    G = seq.create_graph(m)
    up_type_list = []
    for node in G.nodes():
        up_type_list.append(str(node).replace('fs.', ''))

    if "secondary_BODonly" in up_type_list:
        return 0
    if "secondary_nitrified" in up_type_list:
        return 5
    if "secondary_denitrified" in up_type_list:
        return 5
    if "mbr" in up_type_list:
        return 4
    if "tertiary_media_filtration" in up_type_list:
        return 5
    if "media_filtration" in up_type_list:
        return 5
    if "biologically_active_filtration" in up_type_list:
        return 2
    if "microfiltration" in up_type_list:

        if "cas" in up_type_list:
            return 12
        elif "nas" in up_type_list:
            return 4
        elif "ozonation" in up_type_list:
            return 3
        elif "o3_baf" in up_type_list:
            return 2
        else:
            return 0
    if "ultrafiltration" in up_type_list:

        if "cas" in up_type_list:
            return 12
        elif "nas" in up_type_list:
            return 4
        elif "ozonation" in up_type_list:
            return 3
        elif "o3_baf" in up_type_list:
            return 2
        else:
            return 0
    if "ozonation" in up_type_list:
        return 3
    if "uv" in up_type_list:
        return 0
    if "reverse_osomisis" in up_type_list:
        return 0

    print("assuming initial chlorine demand is 0")

    return 0

def create(m, up_name):
    
    # Set removal and recovery fractions
    getattr(m.fs, up_name).water_recovery.fix(flow_recovery_factor)
    
    for constituent_name in train_constituent_list:
        
        if constituent_name in train_constituent_removal_factors.keys():
            getattr(m.fs, up_name).removal_fraction[:, constituent_name].fix(train_constituent_removal_factors[constituent_name])
        else:
            getattr(m.fs, up_name).removal_fraction[:, constituent_name].fix(1e-7)

    # Also set pressure drops - for now I will set these to zero
    getattr(m.fs, up_name).deltaP_outlet.fix(1e-4)
    getattr(m.fs, up_name).deltaP_waste.fix(1e-4)
        
        # Then, recovery and removal variables
    #getattr(m.fs, up_name).cl2_dem = Var(time,
    #                          initialize=0.0, #TODO: NEEDS TO BE DIFFERENT?
    #                          units=pyunits.dimensionless,
    #                          doc="Water recovery fraction")
    
    getattr(m.fs, up_name).cl2_dem.fix(1e-4) #get_cl2_dem(m))
    # Adding costing for units - this is very basic for now so use default settings
    getattr(m.fs, up_name).get_costing(module=financials)
        
    return m        
        
        
def get_additional_variables(self, units_meta, time):
    
    self.cl2_dem = Var(time, initialize=0, units=pyunits.dimensionless, doc="initial chlorine demand")    
    
  


