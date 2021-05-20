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
from pyomo.environ import Block, Constraint, Expression, NonNegativeReals, Var, units as pyunits
# Import IDAES cores
from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import is_physical_parameter_block
# Import WaterTAP# financials module
import financials
from financials import *

# Import properties and units from "WaterTAP Library"

# Set inlet conditions to first unit
# IDAES Does have Feed components for this, but that would require a bit
# more work to set up to work (as it relies on things in the property package
# that aren't implemented for this example).
# I am just picking numbers for most of these


### FACTORS FOR ZEROTH ORDER MODEL -> TODO -> READ IN AUTOMATICALLY BASED ON UNIT PROCESS --> CREATE TABLE?!###
#flow_recovery_factor = 0.95 # ANNA CHECK TODO

# capital costs basis
### FACTORS FOR ZEROTH ORDER MODEL -> TODO -> READ IN AUTOMATICALLY BASED ON UNIT PROCESS --> CREATE TABLE?!###
#flow_recovery_factor = 0.8
#tds_removal_factor = 0.992

# captial costs basis
base_fixed_cap_cost = 12.612  # from McGivney/Kamakura figure 5.8.1
cap_scaling_exp = 0.7177  # from McGivney/Kamakura figure 5.8.1

basis_year = 2007 # McGivney year
fixed_op_cost_scaling_exp = 0.7


# recycle_factor = (1 - recovery_factor) * (recyle_fraction_of_waste)
# waste_factor = 1 - water_recovery  # - G.edges[edge]['recycle_factor']


### Model Parameters (DEEP model with Carlsbad values)


# Plant specifications
tim = 25 # (deg. C) feed water inlet temperature at RO element entry   (DEEP model default) *****

# NEEDS TO BASED ON THE FLOW COMING IN. TODOURGENTCHANGE
tds = 35000 # (ppm) total disolved solids   (Mike's input value) *****

# RO Technical parameters
pmax = 85 # (bar) maximum design pressure of the membrane (matched to Carlsbad value in VAR tab)
ccalc = .00115 # constant used for recovery ratio calculation *****
dflux = 13.6 # (l/m2*h) design average permeate flux  ****
nflux = 27.8 # (l/m2*h) normal permeate flux ****
a = 3500 # polyamide membrane permeability constant *****
ndpn = 44.7 # (bar) nominal net driving pressure
kmff = .9 # fouling factor *****
kmaiicf = 1.05 # aggregation of individual ions correction factor *****
kmsgc = 1.04 # specific gravity of concentrate correction factor *****
kmsgsw = 1.02 # specific gravity of seawater feed correction factor  ##### Not used in Excel version

# Pump data
dpspd = 2 # (bar) pressure drop across the system *****
dppp = 1 # (bar) permeate pressure losses *****
dpps = 1 # (bar) pump suction pressure *****
dpcd = .5 # (bar) concentrate discharge pressure *****
dpsm = 1.7 # (bar) seawater pump head  *****
dpbm = 3.3 # (bar) booster pump head *****

ehm = .85 # high head pump efficiency *****
ehhm = .97 # hydraulic pump hydraulic coupling efficiency *****
esm = .85 # seawater pump efficiency  *****
ebm = .85 # booster pump efficiency  *****
eer = .95 # energy recovery efficiency *****
eem = .96 # electric motor efficiency  ##### Not used in Excel version

fma = .73 # membrane area factor (over reference)
fpp = .99 # pretreatment, pump, pump sizing

# RO plant and feed water characteristics 
qsom = 0 # (kwh/m3) other specific power use (.4 in DEEP default, 0 for Carlsbad)


### Model parameters (pg. 36 of DEEP model manual)

# Operation and performance data
lm = 12 # (m) water plant lead time  ##### Not used in Excel version
lwp = 20 # (years) lifetime of water plant  ##### Not used in Excel version
amp = .9 # water plant operating availability  ##### Not used in Excel version
nmsm = 4 # management personnel  ##### Not used in Excel version
nmsl = 31 # labor personnel  ##### Not used in Excel version
app = .9 # power plant availability  ##### Not used in Excel version
apm = .9 # water production availability  ##### Not used in Excel version
acpm = apm * app # combined pp/wp load factor  ##### Not used in Excel version

# Cost data
cmu = 900 # ($/m3/d) base unit cost  ##### Not used in Excel version
cpe = .06 # ($/kWh) purchase power cost  ##### Not used in Excel version
smm = 66000 # ($) management salary  ##### Not used in Excel version
sml = 29700 # ($) labor salary  ##### Not used in Excel version
cmsp = .04 # ($/m3) specific O&M spare parts cost  ##### Not used in Excel version
cmcpr = .03 # ($/m3) specific O&M chemicals cost for pre-treatment  ##### Not used in Excel version
cmcpo = .01 # ($/m3) specific O&M chemicals cost for post-treatment  ##### Not used in Excel version
cmm = .07 # ($/m3) O&M membrane replacement cost  ##### Not used

kmsus = 1 # unit size correction factor
csmo = .07 # in/outfall specific cost factor
kmo = .05 # water plant owners cost factor
kmc = .1 # water plant cost contingency factor
kmi = .005 # water palnt O&M insurance cost

# Economic inputs

ir = .05 # interest (default in DEEP)
i = .05 # discount ratio (default in DEEP)
#eff = # fossil fuel annual real escalation
ycr = 2020 # currency reference year
yi = 2000 # initial year of operation
energy_cost_factor = .08 # $/kWh


cost_factor_for_number_of_passes = 1
parallel_units = 1

import numpy as np
kmtcf = np.exp(a * (1/(tim+273) - 1/(298))) # temperature correction factor***

# Get constituent list and removal rates for this unit process
import generate_constituent_list
train_constituent_list = generate_constituent_list.run()
train_constituent_removal_factors = generate_constituent_list.get_removal_factors("ro_deep")


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

    #unit_process_equations.get_base_unit_process()

    #build(up_name = "nanofiltration_twb")
    
    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test = "ro_deep")
    
    
    def get_costing(self, module=financials, cost_method="wt", year=None):
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
        
        time = self.flowsheet().config.time.first()  
        
        # Then, recovery and removal variables
#         self.water_recovery = Var(time,
#                               initialize=0.8, #TODO: NEEDS TO BE DIFFERENT?
#                               #within=PositiveReals,
#                               units=pyunits.dimensionless,
#                               bounds=(0.0001, 1.0),
#                               doc="Water recovery fraction")
    
            
        # optimal recovery ratio; .526 for the Carlsbad case study
        
        
        self.recovery_constraint_eq = Constraint(
            expr= self.water_recovery[time] == 1 - (ccalc/pmax) * (self.conc_mass_in[time, "TDS"] * 1000))
        
        #self.water_recovery[time] = 1 - (ccalc/pmax) * (self.tds_in * 1000)
        
        
        dso = tds / (1-self.water_recovery[time]) # (ppm) brine salinity ***
        dspms = .0025 * tds * (nflux/dflux) * .5 * (1 + (1/(1-self.water_recovery[time]))) * (1+(tim - 25)*.03) # (ppm) permeate salinity ***

        #kmtcf = np.exp(a * (1/(tim+273) - 1/(298))) # temperature correction factor*** ariel moved to top
        kmscf = 1.5 - .000015 * .5 * (1 + (1/(1-self.water_recovery[time])))*tds # salinity correction factor***
        ndp = dflux/(nflux*kmscf) * ndpn * kmtcf/kmff # (bar) design net driving pressure ***
        
        
        
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
            
            def energy_recovery(wacs):
                fsms = wacs/self.parent_block().water_recovery[time] * (1000 / (24*3600)) # (kg/s) feed flow

                dphm = pavg + ndp + dpspd/2 + dppp + dpps # (bar) high head pump pressure rise  *****
                qhp = (fsms * dphm) / (ehm * ehhm * eem * 9866) * kmsgsw  # (MW) high head pump power. Different in model vs. manual. This matches model 
                #qhp = (fsms * dphm) / (ehm * ehhm * 9866) # (MW) high head pump power. Matches Mike's equation    *****
                    
                qer1 = -fsms * (1-self.parent_block().water_recovery[time])* eer * (dphm - dpspd- dpcd) * kmsgc / 10000 # (MW) energy recovery PLT *****
                qer2 =  -(1-self.parent_block().water_recovery[time]) * eer * qhp # (MW) energy recovery other *****

                return qer2

            def power_demand(wacs):  # Total power use (qms) for a given plant output capacity (wacs)
                fsms = wacs/self.parent_block().water_recovery[time] * (1000 / 24 / 3600) # (kg/s) feed flow

                dphm = pavg + ndp + dpspd/2 + dppp + dpps # (bar) high head pump pressure rise
                
                #qhp = (fsms * dphm) / (ehm * ehhm * 9866) # (MW) high head pump power. Different in model vs. manual.
                                #(Model divides by eem and * kmsgsw, manual and Mike do not)
                qhp = (fsms * dphm) / (ehm * ehhm * eem * 9866) * kmsgsw # (MW) high head pump power. (Model version)
                
                #qsp = (fsms * dpsm) / (esm * 9866) # (MW) sw pumping power. Model divides by eem, manual and Mike do not *****
                qsp = (fsms * dpsm) / (esm * eem * 9866) * kmsgsw # (MW) seawater pumping power. (Model version)
                
                #qbp = (fsms * dpbm) / (ebm  * 9866) # (MW) booster pump power. Model divides by eem, manual and Mike do not ***
                qbp = (fsms * dpbm) / (ebm * eem * 9866) * kmsgsw # (MW) booster pump power. (Model version)
                
                qom = (wacs * qsom) / (24 * 1000) # (MW) other power  *****

                qms = qsp + qbp + qhp + energy_recovery(wacs) + qom # (MW) total power use *****

                return qms #(MW) annually

            def electricity(wacs):
                electricity = power_demand(wacs) * 24 / (wacs/self.parent_block().water_recovery[time]) * 1000  #kWh/m3
                
                return electricity

            
            def get_osmotic_pressure(C,T): # 
                osmotic_pressure = .0000348 * (T + 273) * (C/14.7)  # (bar) osmotic pressure function  

                return osmotic_pressure


            pavg = (get_osmotic_pressure(tds,tim) + get_osmotic_pressure(dso,tim))/2 * kmaiicf # (bar) average osmotic pressure
               
                
            def fixed_cap_mcgiv(wacs):
               
                mcgivney_cap_cost = .3337 * (wacs/24)**.7177 * cost_factor_for_number_of_passes * parallel_units # Mike's UP $M
                #guo_cap_cost =  0.13108 * (wacs/24) ** 0.82523 * cost_factor_for_number_of_passes * parallel_units # Mike's $M
                
                return mcgivney_cap_cost
            
            
            time = self.parent_block().flowsheet().config.time.first()
            flow_out = pyunits.convert(self.parent_block().flow_vol_out[time],
                          to_units=pyunits.Mgallons/pyunits.day) # convert to MGD  

            wacs = flow_out * 3785.4118 #what is this constant for
            
            # Get the first time point in the time domain
            # In many cases this will be the only point (steady-state), but lets be
            # safe and use a general approach

            # Get the inlet flow to the unit and convert to the correct units
            flow_in = pyunits.convert(self.parent_block().flow_vol_in[time],
                                      to_units=pyunits.Mgallons/pyunits.day)
            

            ################### TWB METHOD ###########################################################
            if cost_method == "twb":
                    self.fixed_cap_inv_unadjusted = Expression(
                        expr=self.base_fixed_cap_cost *
                        flow_in ** self.cap_scaling_exp,
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
                    expr=fixed_cap_mcgiv(wacs),
                    doc="Unadjusted fixed capital investment") 

                self.fixed_cap_inv = self.fixed_cap_inv_unadjusted * self.cap_replacement_parts
                self.land_cost = self.fixed_cap_inv * land_cost_precent_FCI
                self.working_cap = self.fixed_cap_inv * working_cap_precent_FCI
                self.total_cap_investment = self.fixed_cap_inv + self.land_cost + self.working_cap

                # variable operating costs (unit: MM$/yr) -> MIKE TO DO -> ---> CAT+CHEM IN EXCEL
                # --> should be functions of what is needed!?
                # cat_chem_df = pd.read_csv('catalyst_chemicals.csv')
                # cat_and_chem = flow_in * 365 * on_stream_factor # TODO
                self.electricity = electricity(wacs) # kwh/m3 
                self.cat_and_chem_cost = 0  # TODO
                
                total_flow_rate = 2042132 # kg/hr - from design tab. For Carlsbad only 
                                            # TODO need to calculate this value
                
                flow_in_m3yr = (pyunits.convert(self.parent_block().flow_vol_in[time], to_units=pyunits.m**3/pyunits.year))
                
                self.electricity_cost = Expression(
                        expr= (self.electricity * flow_in_m3yr * elec_price/1000000),
                        doc="Electricity cost") # M$/yr
                self.other_var_cost = 0 #Expression(
                        #expr= self.total_cap_investment - self.cat_and_chem_cost - self.electricity_cost,
                        #doc="Other variable cost")

                # fixed operating cost (unit: MM$/yr)  ---> FIXED IN EXCEL
#                 self.base_employee_salary_cost = fixed_cap(flow_in) * salaries_percent_FCI #.00976 #excel value
#                 self.salaries = (
#                     self.labor_and_other_fixed
#                     * self.base_employee_salary_cost 
#                     * flow_in ** fixed_op_cost_scaling_exp
#                 )
                
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

def create(m, up_name):
    
    # Set removal and recovery fractions
    #getattr(m.fs, up_name).water_recovery.fix(flow_recovery_factor)
    
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
        
        
           
        
        
        