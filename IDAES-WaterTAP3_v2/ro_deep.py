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

# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock

import numpy as np

##########################################
####### UNIT PARAMETERS ######
# At this point (outside the unit), we define the unit parameters that do not change across case studies or analyses ######.
# Below (in the unit), we define the parameters that we may want to change across case studies or analyses. Those parameters should be set as variables (eventually) and atttributed to the unit model (i.e. m.fs.UNIT_NAME.PARAMETERNAME). Anything specific to the costing only should be in  m.fs.UNIT_NAME.costing.PARAMETERNAME ######
##########################################

## REFERENCE: # from McGivney/Kamakura figure 5.8.1. RO process based on DEEP model

### MODULE NAME ###
module_name = "ro_deep"

# Cost assumptions for the unit, based on the method #
# this is either cost curve or equation. if cost curve then reads in data from file.
unit_cost_method = "cost_curve"
tpec_or_tic = "TPEC"
unit_basis_yr = 2007

# captial costs basis
base_fixed_cap_cost = 12.612  # from McGivney/Kamakura figure 5.8.1
cap_scaling_exp = 0.7177  # from McGivney/Kamakura figure 5.8.1
fixed_op_cost_scaling_exp = 0.7


### Model Parameters (DEEP model with Carlsbad values)
# Plant specifications
tim = 25 # (deg. C) feed water inlet temperature at RO element entry   (DEEP model default) *****

# NEEDS TO BASED ON THE FLOW COMING IN. TODOURGENTCHANGE
#tds = 35000 # (ppm) total disolved solids   (Mike's input value) *****

# RO Technical parameters
# TODO --> THIS SHOULD BE BASED ON MEMBRANE!!!!!!
#pmax = 85 # (bar) maximum design pressure of the membrane (matched to Carlsbad value in VAR tab)
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

### COST FACTOR FOR PASSES AND PARA! 
cost_factor_for_number_of_passes = 1
parallel_units = 1

kmtcf = np.exp(a * (1/(tim+273) - 1/(298))) # temperature correction factor***


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

    #build(up_name = "nanofiltration_twb")
    
    def build(self):
        import unit_process_equations
        return unit_process_equations.build_up(self, up_name_test = module_name)
    
    
    def get_costing(self, module=financials, cost_method="wt", year=None, unit_params = None):
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
        
        self.costing.basis_year = unit_basis_yr
                
        time = self.flowsheet().config.time.first()               
        tds = self.conc_mass_in[time, "tds"] * 1000 # convert from kg/m3 to mg/L
        
        
        self.pmax.fix(unit_params["feed_pressure"])
        
        ################## DEEP METHOD ###########################################################
        ##### excludes the cost of water storage, transportation, distribution
        ##### *** are variables that are also in the watertap excel version of the DEEP mode                
        # optimal recovery ratio; .526 for the Carlsbad case study
        self.recovery_constraint_eq = Constraint(
            expr= self.water_recovery[time] == 1 - (ccalc/self.pmax[time]) * (self.conc_mass_in[time, "tds"] * 1000))
        
        
        dso = tds / (1-self.water_recovery[time]) # (ppm) brine salinity ***
        self.dspms = .0025 * tds * (nflux/dflux) * .5 * (1 + (1/(1-self.water_recovery[time]))) * (1+(tim - 25)*.03) # (ppm) permeate salinity ***
        
        
        
        #kmtcf = np.exp(a * (1/(tim+273) - 1/(298))) # temperature correction factor*** ariel moved to top
        kmscf = 1.5 - .000015 * .5 * (1 + (1/(1-self.water_recovery[time])))*tds # salinity correction factor***
        ndp = dflux/(nflux*kmscf) * ndpn * kmtcf/kmff # (bar) design net driving pressure ***
        
        # Get the inlet flow to the unit and convert to the correct units
        flow_in = pyunits.convert(self.flow_vol_in[time],
                                  to_units=pyunits.Mgallons/pyunits.day) # convert to MGD

        ################### DEEP METHOD ###########################################################
        ##### excludes the cost of water storage, transportation, distribution
        ##### *** are variables that are also in the watertap excel version of the DEEP mode


        # flow_in = wacs / self.parent_block().water_recovery # (m3/d) feed flow (wfm in DEEP model)
        # flow_in_m3_hr = flow_in / 24 # (m3/hr) feed flow
        # wbm = flow_in - wacs # (m3/d) brine flow

#             dso = tds / (1-self.parent_block().water_recovery) # (ppm) brine salinity ***
#             dspms = .0025 * tds * (nflux/dflux) * .5 * (1 + (1/(1-self.parent_block().water_recovery))) * (1+(tim - 25)*.03) # (ppm) permeate salinity ***

#             kmtcf = np.exp(a * (1/(tim+273) - 1/(298))) # temperature correction factor***
#             kmscf = 1.5 - .000015 * .5 * (1 + (1/(1-self.parent_block().water_recovery)))*tds # salinity correction factor***
#             ndp = dflux/(nflux*kmscf) * ndpn * kmtcf/kmff # (bar) design net driving pressure ***



        def energy_recovery(wacs):
            fsms = wacs/self.water_recovery[time] * (1000 / (24*3600)) # (kg/s) feed flow

            dphm = pavg + ndp + dpspd/2 + dppp + dpps # (bar) high head pump pressure rise  *****
            qhp = (fsms * dphm) / (ehm * ehhm * eem * 9866) * kmsgsw  # (MW) high head pump power. Different in model vs. manual. This matches model 
            #qhp = (fsms * dphm) / (ehm * ehhm * 9866) # (MW) high head pump power. Matches Mike's equation    *****

            qer1 = -fsms * (1-self.water_recovery[time])* eer * (dphm - dpspd- dpcd) * kmsgc / 10000 # (MW) energy recovery PLT *****
            qer2 =  -(1-self.water_recovery[time]) * eer * qhp # (MW) energy recovery other *****

            return qer2

        def power_demand(wacs):  # Total power use (qms) for a given plant output capacity (wacs)
            fsms = wacs/self.water_recovery[time] * (1000 / 24 / 3600) # (kg/s) feed flow

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


#             def energy_demand(wacs): # total energy (including energy recovery)
#                 tot_pow = power_demand(wacs) * 24 * 365 * 1000

#                 return tot_pow # (kWh) annual energy demand

        def electricity(wacs):
            electricity = power_demand(wacs) * 24 / (wacs/self.water_recovery[time]) * 1000  #kWh/m3

            return electricity


#             def power_per_outlet(wacs):
#                 qdp = power_demand(wacs) / wacs # (MW) specific power use per m3/d produced

#                 return qdp

#             def power_per_inlet(wacs):
#                 tppi = power_demand(wacs) / (wacs/self.parent_block().water_recovery) # (MW) specific power use per input feed

#                 return tppi

        def get_osmotic_pressure(C,T): # 
            osmotic_pressure = .0000348 * (T + 273) * (C/14.7)  # (bar) osmotic pressure function  

            return osmotic_pressure

        pavg = (get_osmotic_pressure(tds,tim) + get_osmotic_pressure(dso,tim))/2 * kmaiicf # (bar) average osmotic pressure


#             def cap_recovery(i,n):
#                 lfc = (i * (1 + i)**n) / ((1 + i) ** n - 1)

#                 return lfc # capital recovery factor function



#             def fixed_cap(wacs):
#                 cmio = csmo * cmu # in/outfall specific cost
#                 cms = cmu * kmsus + cmio # total specific base cost
#                 cmsab = wacs * cms # water plant adjusted total base cost
#                 dcmso = cmsab * kmo # water plant owners cost
#                 dcmsc = (cmsab + dcmso) * kmc # water plant contingency cost
#                 cmscon = cmsab + dcmso + dcmsc # water plant total construction cost
#                 idcs = cmscon * ((1 + ir) ** (lm/24) - 1 ) # interest during construction
#                 cmsinv = cmscon + idcs # total investment cost

#                 return cmsinv/1000000 # $M; total investment cost



#             def capital_cost(wacs): # with capital recovery included

#                 amsfc = fixed_cap(wacs) * cap_recovery(i,lwp) 

#                 return amsfc # $M, total annual capital cost


#             def annual_water_production(wacs):

#                 wpd = wacs * amp * 365 # total water production per year

#                 return wpd # m3 per year


#             def energy_cost(wacs): # all based on backup heat and load factors
#                 energy_cost = energy_demand(wacs) * energy_cost_factor

#                 return energy_cost/1000000 # annual cost; $ M


#             def OM_cost(wacs):
#                 cdm = nmsm * smm # management cost
#                 cdl = nmsl * sml # labour cost

#                 cmio = csmo * cmu # in/outfall specific cost
#                 cms = cmu * kmsus + cmio # total specific base cost
#                 cmsab = (wacs * cms) # water plant adjust base cost
#                 dcmso = cmsab * kmo # water plant owners cost
#                 dcmsc = (cmsab + dcmso) * kmc # water plant contingency cost

#                 csmt = (cmm * fma + cmsp * fpp + cmcpr + cmcpo) * annual_water_production(wacs) # material cost
#                 cmscon = dcmsc + dcmso + cmsab # water plant total construction
#                 csins = kmi * cmscon # insurance cost

#                 cdom = cdm + cdl + csmt + csins # total O&M cost

#                 return cdom/1000000 # annual O&M cost; $ M                                        


#             def get_flow_out(flow_in): 
#                 #flow_in_m3d = pyunits.convert(self.parent_block().flow_vol_in[time],
#                #                       to_units=pyunits.meter**3/pyunits.day) # conversion from MGD to m3/d
#                 flow_in_m3d = flow_in * 3785.4118
#                 flow_out = flow_in_m3d * self.parent_block().water_recovery[time]

#                 return flow_out #m3/d


#             def total_up_cost(m=None, G=None, flow_in=flow_in, cost_method="deep"):
#                 wacs = get_flow_out(flow_in) # flow_out m3/d; plant OUTPUT capacity and also called wacd in DEEP

#                 adrev = capital_cost(wacs) + OM_cost(wacs) + energy_cost(wacs) # total annual cost; $ M

#                 lifetime_cost = adrev * lwp # $ M


#                 return lifetime_cost # $M


#             def lifetime_levelized_cost(flow_in):
#                 levelized = total_up_cost(flow_in) / (get_flow_out(flow_in) * 365 * lwp * amp) 
#                             # total_up_cost must return lifetime_cost, not lifetime_cost_2

#                 return levelized # lifetime levelized (M$/m3)

            
                        
            
        def fixed_cap_mcgiv(wacs):

            Single_Pass_FCI = (0.3337 * wacs ** 0.7177) * ((0.0936 * wacs ** 0.7837) / (0.1203 * wacs ** 0.7807))
            Two_Pass_FCI = (0.3337 * wacs ** 0.7177)
            
            #mcgivney_cap_cost = .3337 * (wacs/24)**.7177 * cost_factor_for_number_of_passes * parallel_units # Mike's UP $M
            #guo_cap_cost =  0.13108 * (wacs/24) ** 0.82523 * cost_factor_for_number_of_passes * parallel_units # Mike's $M
            if unit_params is None:
                return Single_Pass_FCI
            else:
                if unit_params["pass"] == "first": 
                    return Single_Pass_FCI
                if unit_params["pass"] == "second":
                    return (Two_Pass_FCI - Single_Pass_FCI)
            


        # capital costs (unit: MM$) ---> TCI IN EXCEL
        # Get the inlet flow to the unit and convert to the correct units
        flow_out = pyunits.convert(self.flow_vol_out[time],
                                  to_units=pyunits.Mgallons/pyunits.day) # convert to MGD  

        wacs = self.flow_vol_out[time] * 3600 #what is this constant for
        #wacs = flow_in * 3785.4118 * self.parent_block().water_recovery[time]

        self.costing.fixed_cap_inv_unadjusted = Expression(
            expr=fixed_cap_mcgiv(wacs),
            doc="Unadjusted fixed capital investment")
                
        self.electricity = electricity(wacs)  # kwh/m3 (PML note: based on data from Carlsbad case)
        
        self.chem_dict = {}        
        ##########################################
        ####### GET REST OF UNIT COSTS ######
        ##########################################        
        
        module.get_complete_costing(self.costing)
          
        
# OTHER VARIABLES --> SHOULD BE IN ABOVE FUNCTION. 
        
def get_additional_variables(self, units_meta, time):
    
    self.pmax = Var(time, initialize=50, units=pyunits.bar, doc="pmax")   
       
           
        
        
        