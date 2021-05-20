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
from pyomo.environ import Block, Expression, NonNegativeReals, Param, Var, units as pyunits
# Import IDAES cores
from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import is_physical_parameter_block
# Import WaterTAP# finanacilas module
import financials
from financials import *  # ARIEL ADDED
import numpy as np

# Import properties and units from "WaterTAP Library"

# Set inlet conditions to first unit
# IDAES Does have Feed components for this, but that would require a bit
# more work to set up to work (as it relies on things in the property package
# that aren't implemented for this example).
# I am just picking numbers for most of these


### FACTORS FOR ZEROTH ORDER MODEL -> TODO -> READ IN AUTOMATICALLY BASED ON UNIT PROCESS --> CREATE TABLE?!###
flow_recovery_factor = 0.5265
tds_removal_factor = 0.992 # PML

# Perfomance Parameter Values for Process: Constituent removals.
toc_removal_factor = 0.0  # Asano et al (2007)
nitrates_removal_factor = 0.0  # None but in Excel tool appears to be removed sometimes?
TOrC_removal = 0.0  # slightly lower removal than for UF. Some removal is expected due to particle association of TOrCs.
EEQ_removal = 0.0  # Linden et al., 2012 (based on limited data))
NDMA_removal = 0.0
PFOS_PFOA_removal = 0.0
protozoa_removal = 0.0
virus_removal = 0.0

# captial costs basis
# Project Cost for Filter = $2.5M x (flow in mgd) page 55)
base_fixed_cap_cost = 132.2  # from TWB -> THIS IS SOMEHOW DIFFERENT FROM EXCEL CALCS NOT SURE WHY (3.125))

cap_scaling_exp = 0.718  # from TWB

recovery_factor = 1.0  ## ASSUMED AS 1.0 -> MUST BE WRONG -> CHECK


# recycle_factor = (1 - recovery_factor) * (recyle_fraction_of_waste)
waste_factor = 1 - recovery_factor  # - G.edges[edge]['recycle_factor']

# Plant specifications
# wacs = 94152 # (m3/d) required desalination plant OUTPUT capacity and also called wacd in DEEP (Mike's input value)
# wacs_m3_hr = wacs / 24 # (m3/hr) outlet flow rate
tim = 25 # (deg. C) feed water inlet temperature at RO element entry   (DEEP model default)
tds = 35000 # (ppm) total disolved solids   (Mike's input value)


### Model Parameters (pg. 22 of DEEP model manual)

# RO Technical parameters
pmax = 80 # (bar) maximum design pressure of the membrane
ccalc = .00115 # constant used for recovery ratio calculation
dflux = 13.6 # (l/m2*h) design average permeate flux
nflux = 27.8 # (l/m2*h) normal permeate flux
a = 3500 # polyamide membrane permeability constant
ndpn = 28.2 # (bar) nominal net driving pressure
kmff = .9 # fouling factor
kmaiicf = 1.05 # aggregation of individual ions correction factor
kmsgc = 1.04 # specific gravity of concentrate correction factor
kmsgsw = 1.02 # specific gravity of seawater feed correction factor

# Pump data
dpspd = 2 # (bar) pressure drop across the system
dppp = 1 # (bar) permeate pressure losses
dpps = 1 # (bar) pump suction pressure
dpcd = .5 # (bar) concentrate discharge pressure
dpsm = 1.7 # (bar) seawater pump head 
dpbm = 3.3 # (bar) booster pump head

ehm = .85 # high head pump efficiency
ehhm = .97 # hydraulic pump hydraulic coupling efficiency
esm = .85 # seawater pump efficiency 
ebm = .85 # booster pump efficiency 
eer = .95 # energy recovery efficiency
eem = .96 # electric motor efficiency

# RO plant and feed water characteristics 
qsom = .4 # (kwh/m3) other specific power use


# flow_in = wacs / rr # (m3/d) feed flow (wfm in DEEP model)
# flow_in_m3_hr = flow_in / 24 # (m3/hr) feed flow
# wbm = flow_in - wacs # (m3/d) brine flow



### Model parameters (pg. 36 of DEEP model manual)

# Operation and performance data
lm = 12 # (m) water plant lead time *****
lwp = 20 # (years) lifetime of water plant *****
amp = .9 # water plant operating availability
opm = .032 # water plant outage rate *****
oum = .06 # water plant unplanned outage rate *****
nmsm = 3 # management personnel *****
nmsl = 23 # labor personnel
app = .9 # power plant availability
apm = .9 # water production availability
acpm = apm * app # combined pp/wp load factor

# Cost data
cmu = 900 # ($/m3/d) base unit cost *****
cpe = .06 # ($/kWh) purchase power cost
smm = 66000 # ($) management salary
sml = 29700 # ($) labor salary *****
cmsp = .04 # ($/m3) specific O&M spare parts cost *****
cmcpr = .03 # ($/m3) specific O&M chemicals cost for pre-treatment *****
cmcpo = .01 # ($/m3) specific O&M chemicals cost for post-treatment *****
cmm = .07 # ($/m3) O&M membrane replacement cost

kmsus = 1 # unit size correction factor *****
csmo = .07 # in/outfall specific cost factor *****
kmo = .05 # water plant owners cost factor *****
kmc = .1 # water plant cost contingency factor *****
kmi = .005 # water palnt O&M insurance cost *****

# Economic inputs

ir = .05 # interest (default in DEEP) *****
i = .05 # discount ratio (default in DEEP) *****
#eff = # fossil fuel annual real escalation
ycr = 2020 # currency reference year
yi = 2000 # initial year of operation
energy_cost_factor = .08 # $/kWh



            
            
# assumed input flow_in is in MGD
# calculations are in m3/d and based on output capacity, not input flow.  
# Conversions from inflow to output capacity are done automatically by get_flow_out function


def energy_recovery(wacs):
    fsms = wacs/rr * (1000 / (24*3600)) # (kg/s) feed flow

    dphm = pavg + ndp + dpspd/2 + dppp + dpps # (bar) high head pump pressure rise
    qhp = (fsms * dphm) * kmsgsw / (ehm * ehhm * 9866) # (MW) high head pump power. Different in model vs. manual

    qer1 = -fsms * (1-rr)* eer * (dphm - dpspd- dpcd) * kmsgc / 10000 # (MW) energy recovery PLT
    qer2 =  -(1-rr) * eer * qhp # (MW) energy recovery other

#     if qer1 < qer2:
#         recovery = qer1
#     else:
#         recovery = qer2

    return qer1

def power_demand(wacs):  # Total power use (qms) for a given plant output capacity (wacs)
    fsms = wacs/rr * (1000 / (24*3600)) # (kg/s) feed flow

    dphm = pavg + ndp + dpspd/2 + dppp + dpps # (bar) high head pump pressure rise
    qhp = (fsms * dphm) / (ehm * ehhm * 9866) * kmsgsw # (MW) high head pump power. (Model divides by eem, manual and Mike do not)
    #qhp = (fsms * dphm) / (ehm * ehhm * eem * 9866) * kmsgsw # (MW) high head pump power. (Model version)
    qsp = (fsms * dpsm) / (esm * 9866) # (MW) seawater pumping power. (Model divides by eem, manual and Mike do not)
    #qsp = (fsms * dpsm) / (esm * eem * 9866) # (MW) seawater pumping power. (Model version)
    qbp = (fsms * dpbm) / (ebm  * 9866) # (MW) booster pump power. (Model divides by eem, manual and Mike do not)
    #qbp = (fsms * dpbm) / (ebm * eem * 9866) # (MW) booster pump power. (Model version)
    qom = (wacs * qsom) / (24 * 1000) # (MW) other power

    qms = qsp + qbp + qhp + energy_recovery(wacs) + qom # (MW) total power use

    return qms #(MW)


def energy_demand(wacs): # total energy (including energy recovery)
    tot_pow = power_demand(wacs) * 24 * 365 * 1000

    return tot_pow # (kWh) annual energy demand


def power_per_outlet(wacs):
    qdp = power_demand(wacs) * 24 / wacs * 1000 # (MW) specific power use per output

    return qdp

def power_per_inlet(wacs):
    tppi = power_demand(wacs) * 24 / flow_in * 1000 # (MW) specific power use per input feed

    return tppi

def get_osmotic_pressure(C,T): # 
    osmotic_pressure = .0000348 * (T + 273) * (C/14.7)  # (bar) osmotic pressure function  

    return osmotic_pressure


pavg = (get_osmotic_pressure(tds,tim) + get_osmotic_pressure(dso,tim))/2 * kmaiicf # (bar) average osmotic pressure





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
    
        self.water_recovery.fix(1 - (ccalc/pmax) * tds)
        
        
        dso = tds / (1-self.water_recovery) # (ppm) brine salinity
        dspms = .0025 * tds * (nflux/dflux) * .5 * (1 + (1/(1-self.water_recovery))) * (1+(tim - 25)*.03) # (ppm) permeate salinity

        kmtcf = np.exp(a * (1/(tim+273) - 1/(298))) # temperature correction factor
        kmscf = 1.5 - .000015 * .5 * (1 + (1/(1-self.water_recovery)))*tds # salinity correction factor
        ndp = dflux/(nflux*kmscf) * ndpn * kmtcf/kmff # (bar) design net driving pressure
        
    
    def get_costing(self, module=financials, cost_method="wt", year=None):
        """
        We need a get_costing method here to provide a point to call the
        costing methods, but we call out to an external consting module
        for the actual calculations. This lets us easily swap in different
        methods if needed.

        Within IDAES, the year argument is used to set the initial value for
        the cost index when we build the model.
        """
        # RO unit process based on the International Atomic Energy Agency's (IAEA) DEEP model
        # User Manual ==> https://www.iaea.org/sites/default/files/18/08/deep5-manual.pdf
        
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
            
            
            
            
            #########################################################################
            #########################################################################
            ################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
            #########################################################################
            #########################################################################

            # excludes the cost of water storage, transportation, distribution


            def cap_recovery(i,n):
                lfc = (i * (1 + i)**n) / ((1 + i) ** n - 1)

                return lfc # capital recovery factor function


            def capital_cost(wacs):
                cdio = csmo * cmu # in/outfall specific cost
                cdst = cmu * kmsus + cdio # total specific base cost
                cdt = wacs * cdst # water plant adjusted total base cost
                dcdo = cdt * kmo # water plant owners cost
                dcdc = (cdt + dcdo) * kmc # water plant contingency cost
                cdcon = cdt + dcdo + dcdc # water plant total construction cost
                idcd = cdcon * ((1 + ir) ** (lm/24) - 1 ) # interest during construction
                csinv = cdcon + idcd # total investment cost
                adfc = csinv * cap_recovery(i,lwp) # annual water plant fixed charge

                return adfc # total annual fixed charge
            
            def fixed_cap(wacs):
                cdio = csmo * cmu # in/outfall specific cost
                cdst = cmu * kmsus + cdio # total specific base cost
                cdt = wacs * cdst # water plant adjusted total base cost
                dcdo = cdt * kmo # water plant owners cost
                dcdc = (cdt + dcdo) * kmc # water plant contingency cost
                cdcon = cdt + dcdo + dcdc # water plant total construction cost
                idcd = cdcon * ((1 + ir) ** (lm/24) - 1 ) # interest during construction
                csinv = cdcon + idcd # total investment cost
                
                return csinv/1000000 # $M
                
            def plant_availability():
                apd = (1 -  opm) * (1 - oum) # water plant operating availability

                return apd


            def annual_water_production(wacs):

                wpd = wacs * plant_availability() * 365 # total water production per year

                return wpd # m3 per year


            def energy_cost(wacs): # all based on backup heat and load factors
                energy_cost = energy_demand(wacs) * energy_cost_factor

                return energy_cost # annual cost


            def OM_cost(wacs):
                cdm = nmsm * smm # management cost
                cdl = nmsl * sml # labour cost
                cdio = csmo * cmu # in/outfall specific cost
                cdst = cmu * kmsus + cdio # total specific base cost
                cdmt = (cmsp + cmcpr + cmcpo) * annual_water_production(wacs)
                cdins = kmi * wacs * cdst # insurance cost
                cdom = cdm + cdl + cdmt + cdins # total O&M cost

                return cdom # annual O&M cost                                          

            def get_flow_out(flow_in): 
                #flow_in_m3h = flow_in * 3785.411784 # conversion from MGD to m3d 
                flow_in_m3h = flow_in * 157.7255 # conversion from MGD to m3hr
                flow_out = flow_in_m3h * self.water_recovery

                return flow_out

            def total_up_cost(m=None, G=None, flow_in=flow_in, cost_method="wt"):
                wacs = get_flow_out(flow_in) # flow_out

                adrev = capital_cost(wacs) + OM_cost(wacs) + energy_cost(wacs)      # total annual cost

                lifetime_cost = (adrev * lwp / 1000000)

                lifetime_cost_2 = .3337 * (wacs/24)**.7177 # Mike's "Reverse Osmosis Unit Fixed Capital Investment" (no O&M) $millions

                lifetime_cost_3 =  0.011342 * wacs ** 0.844273 # Mike's "Total Plant Fixed Capital Investment" (no O&M) $millions

                return lifetime_cost_2 # $M


            def lifetime_levelized_cost(flow_in):
                levelized = (total_up_cost(flow_in)) / (((get_flow_out(flow_in)) * 365 * lwp) * plant_availability()) # total_up_cost must return lifetime_cost, not lifetime_cost_2

                return levelized # lifetime levelized (M$/m3)
            
            
            
            
            
            

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
                wacs = get_flow_out(flow_in)
                self.fixed_cap_inv_unadjusted = Expression(
                    expr=fixed_cap(wacs),
                    doc="Unadjusted fixed capital investment")

                self.fixed_cap_inv = self.fixed_cap_inv_unadjusted * self.cap_replacement_parts
                self.land_cost = self.fixed_cap_inv * land_cost_precent_FCI
                self.working_cap = self.fixed_cap_inv * working_cap_precent_FCI
                self.total_cap_investment = self.fixed_cap_inv + self.land_cost + self.working_cap

                # variable operating costs (unit: MM$/yr) -> MIKE TO DO -> ---> CAT+CHEM IN EXCEL
                # --> should be functions of what is needed!?
                # cat_chem_df = pd.read_csv('catalyst_chemicals.csv')
                # cat_and_chem = flow_in * 365 * on_stream_factor # TODO
                self.electricity = 0  # flow_in * 365 * on_stream_factor * elec_price # TODO
                self.cat_and_chem_cost = 0  # TODO
                self.electricity_cost = self.electricity * elec_price * 365  # KWh/day * $/KWh * 365 days
                self.other_var_cost = self.cat_and_chem_cost - self.electricity_cost

                # fixed operating cost (unit: MM$/yr)  ---> FIXED IN EXCEL
                self.base_employee_salary_cost = capital_cost(wacs) * salaries_percent_FCI
                self.salaries = (
                    self.labor_and_other_fixed
                    * self.base_employee_salary_cost
                    * flow_in ** fixed_op_cost_scaling_exp
                )
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
                    
                   
                
                wacs = get_flow_out(flow_in)
                self.fixed_cap_inv_unadjusted = Expression(
                    expr=fixed_cap(wacs),
                    doc="Unadjusted fixed capital investment") #*pyunits.day/pyunits.Mgallon
                
                self.total_up_cost = total_up_cost(m=None, G=None, flow_in=flow_in, cost_method="wt")
                
                

            #return total_up_cost
    
        up_costing(self.costing, cost_method=cost_method)
          
        
# OTHER CALCS

def create(m, up_name):
    
    # Set removal and recovery fractions
    getattr(m.fs, up_name).water_recovery
    getattr(m.fs, up_name).removal_fraction[:, "TDS"].fix(tds_removal_factor)
    # I took these values from the WaterTAP3 nf model
    getattr(m.fs, up_name).removal_fraction[:, "TOC"].fix(toc_removal_factor)
    getattr(m.fs, up_name).removal_fraction[:, "nitrates"].fix(nitrates_removal_factor)

    # Also set pressure drops - for now I will set these to zero
    getattr(m.fs, up_name).deltaP_outlet.fix(1e-4)
    getattr(m.fs, up_name).deltaP_waste.fix(1e-4)

    # Adding costing for units - this is very basic for now so use default settings
    getattr(m.fs, up_name).get_costing(module=financials)

    return m        
        
        
           
        
        
        