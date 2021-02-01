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

# Import WaterTAP financials module
import financials
from financials import * #ARIEL ADDED

from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import Arc
from idaes.core import FlowsheetBlock

# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock

# Set inlet conditions to first unit
# IDAES Does have Feed components for this, but that would require a bit
# more work to set up to work (as it relies on things in the property package
# that aren't implemented for this example).
# I am just picking numbers for most of these


### FACTORS FOR ZEROTH ORDER MODEL -> TODO -> READ IN AUTOMATICALLY BASED ON UNIT PROCESS --> CREATE TABLE?!###
flow_recovery_factor = 0.99999

# capital costs basis
base_fixed_cap_cost = .0968 # + 1.6389? 
#https://www.mrwa.com/WaterWorksMnl/Chapter%2012%20Coagulation.pdf; Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura); https://www.iwapublishing.com/news/coagulation-and-flocculation-water-and-wastewater-treatment; Water and Wastewater Engineering: Design Principles and Practice (Mackenzie L. Davis)

cap_scaling_exp =  1 # https://www.mrwa.com/WaterWorksMnl/Chapter%2012%20Coagulation.pdf; Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura); https://www.iwapublishing.com/news/coagulation-and-flocculation-water-and-wastewater-treatment; Water and Wastewater Engineering: Design Principles and Practice (Mackenzie L. Davis)
 
basis_year = 2020
fixed_op_cost_scaling_exp = 0.7

# Get constituent list and removal rates for this unit process
import generate_constituent_list
train_constituent_list = generate_constituent_list.run()
train_constituent_removal_factors = generate_constituent_list.get_removal_factors("coag_and_floc")


#### CAT AND CHEMS START ###
#https://www.mrwa.com/WaterWorksMnl/Chapter%2012%20Coagulation.pdf
#Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura)
#https://www.iwapublishing.com/news/coagulation-and-flocculation-water-and-wastewater-treatment
#Water and Wastewater Engineering: Design Principles and Practice (Mackenzie L. Davis)

Al2_SO4_3_Dosage_Rate = 10 # mg/L # MIKE ASSUMPTION NEEDED
Al2_SO4_3_Dosage_Rate = (Al2_SO4_3_Dosage_Rate / 1000 ) / 264.172 # converted to kg/gal todo in pyunits

Polymer_Dosage = 0.1 # mg/L # MIKE ASSUMPTION NEEDED
Polymer_Dosage = (Polymer_Dosage / 1000 ) / 264.172

Aluminum_Al2_SO4_3 = Al2_SO4_3_Dosage_Rate # MIKE ASSUMPTION NEEDED
Anionic_Polymer = Polymer_Dosage / 2 # MIKE ASSUMPTION NEEDED
Cationic_Polymer = Polymer_Dosage / 2 # MIKE ASSUMPTION NEEDED

chem_dic = {"Aluminum_Al2_SO4_3" : Aluminum_Al2_SO4_3, 
            "Anionic_Polymer" : Anionic_Polymer, 
            "Cationic_Polymer" : Cationic_Polymer}

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

    #build(up_name = "coag_and_floc")
    
    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test = "coag_and_floc")
    
    
    def get_costing(self, module=financials, cost_method="wt", year=None):
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
            
            # Coagulation and Flocculation (High G) with Aluminum Sulfate
            rapid_mixers = 1
            floc_mixers = 3
            rapid_mix_processes = 1
            floc_processes = 2
            coag_processes = 1
            floc_injection_processes = 1
            poly_dosage = .1 # mg/L dosage rate
            rapid_mix_retention_time = 5.5 # seconds (rapid mix)
            floc_retention_time =  12 # minutes
            al2so43_density = 8.34 * 1.33 # lb/gal
            al2so43_dosage = 10 # mg/L dosage rate


            # assumed input flow_in is in MGD
            # calculations are in GPM

            def capital_costs(flow_in):
                flow_in_gpm = pyunits.convert(self.parent_block().flow_vol_in[time], to_units=pyunits.gallons/pyunits.minute) 
                            # MGD to GPM

                rapid_mix_basin_volume = (rapid_mix_retention_time / 60) * flow_in_gpm # gallons
                floc_basin_volume = floc_retention_time * flow_in_gpm # gallons 
                al2so43_dosage_lb_per_hour = al2so43_dosage * .00050073 * flow_in_gpm 
                poly_dosage_lb_per_hour = poly_dosage * .00050073 * flow_in_gpm 

                rapid_G = (7.0814 * rapid_mix_basin_volume + 33269) * rapid_mix_processes # $
                floc_G = (952902 * floc_basin_volume/1000000 + 177335) * floc_processes # $
                coag_injection = (212.32 * al2so43_dosage_lb_per_hour + 73225) * coag_processes # $
                floc_injection = (13662 * poly_dosage_lb_per_hour * 24 + 20861) * floc_injection_processes # $

                return (rapid_G + floc_G + coag_injection + floc_injection)/1000000 # $M


            def fixed_cap(flow_in): #TODO
                x = "TPEC" # changeable by user
                TPEC = 3.4
                TIC = 1.65
                
                if x != "TPEC": 
                    TPEC = 1

                if x != "TIC": 
                    TIC = 1

                return capital_costs(flow_in) * TPEC * TIC # M$


            def total_power_consumption(flow_in): # TODO
                flow_in_gpm = pyunits.convert(self.parent_block().flow_vol_in[time], to_units=pyunits.gallons/pyunits.minute) 
                            # MGD to GPM
                flow_in_m3h = pyunits.convert(self.parent_block().flow_vol_in[time], to_units=pyunits.m**3/pyunits.hour) 
                            # MGD to m3/hr

                rapid_mix_basin_volume = ((rapid_mix_retention_time / 60) * flow_in_gpm) / 264.172 # gallons to m3
                
                rapid_mix_power_consumption = 900**2 * .001 * rapid_mix_basin_volume # W
                rapid_mix_power = rapid_mix_power_consumption * rapid_mixers # W

                floc_basin_volume = floc_retention_time * flow_in_gpm / 264.172 # gallons to m3
                floc_power_consumption = 80**2 * .001 * floc_basin_volume # W
                floc_mix_power = floc_power_consumption * floc_mixers # W

                total_power = rapid_mix_power + floc_mix_power
                total_power_per_m3 = (total_power / 1000) / flow_in_m3h # TODO

                return total_power_per_m3 # kWh/m3
            
            
            
            _make_vars(self)

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
                    expr=fixed_cap(flow_in),
                    doc="Unadjusted fixed capital investment")

                self.fixed_cap_inv = self.fixed_cap_inv_unadjusted * self.cap_replacement_parts
                self.land_cost = self.fixed_cap_inv * land_cost_precent_FCI
                self.working_cap = self.fixed_cap_inv * working_cap_precent_FCI
                self.total_cap_investment = self.fixed_cap_inv + self.land_cost + self.working_cap

                # variable operating costs (unit: MM$/yr) -> MIKE TO DO -> ---> CAT+CHEM IN EXCEL
                # --> should be functions of what is needed!?
                # cat_chem_df = pd.read_csv('catalyst_chemicals.csv')
                # cat_and_chem = flow_in * 365 * on_stream_factor # TODO
                
                # TODO for systematic approach elsewhere
                cat_chem_df = pd.read_csv('data/catalyst_chemicals.csv', index_col = "Material")
                chem_cost_sum = 0 
                for key in chem_dic.keys():
                    chem_cost = cat_chem_df.loc[key].Price
                    chem_cost_sum = chem_cost_sum + self.catalysts_chemicals * flow_in * 365 * chem_cost * chem_dic[key] * on_stream_factor
                self.cat_and_chem_cost = chem_cost_sum
                
                
                self.electricity = total_power_consumption(flow_in)  # kWh/m3
               
                flow_in_m3yr = (pyunits.convert(self.parent_block().flow_vol_in[time], to_units=pyunits.m**3/pyunits.year))
                self.electricity_cost = Expression(
                        expr= (self.electricity * flow_in_m3yr * elec_price/1000000),
                        doc="Electricity cost") # M$/yr
                self.other_var_cost = 0 #Expression(
                        #expr= self.cat_and_chem_cost - self.electricity_cost,
                        #doc="Other variable cost")

                # fixed operating cost (unit: MM$/yr)  ---> FIXED IN EXCEL
                
#                 self.base_employee_salary_cost = fixed_cap(flow_in) * salaries_percent_FCI
#                 self.salaries = (
#                     self.labor_and_other_fixed
#                     * self.base_employee_salary_cost
#                     * flow_in ** fixed_op_cost_scaling_exp
#                 )
                
#                 self.salaries = (
#                     (self.labor_and_other_fixed ** fixed_op_cost_scaling_exp) * (salaries_percent_FCI 
#                           * self.fixed_cap_inv_unadjusted) ** fixed_op_cost_scaling_exp)
                   
#                 self.salaries = (
#                     self.labor_and_other_fixed * salaries_percent_FCI * self.fixed_cap_inv_unadjusted)
                
                self.base_employee_salary_cost = fixed_cap(flow_in) * salaries_percent_FCI
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

    # Adding costing for units - this is very basic for now so use default settings
    getattr(m.fs, up_name).get_costing(module=financials)

    return m        
        
        
           
        
        
        