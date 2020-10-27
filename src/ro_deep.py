import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys

from src.financials import *

# RO unit process based on the International Atomic Energy Agency's (IAEA) DEEP model
# User Manual ==> https://www.iaea.org/sites/default/files/18/08/deep5-manual.pdf

# NEEDS TO BE IN M3/DAY FOR THIS UNIT PROCESS
### FLOW IN MUST BE IN M3/DAY OR MGD### TODO


### THESE SHOULD BE COMING FROM ELSEWHERE
unit = "m3d"

# unit conversion needed for model
if unit == "MGD": 
    volume_conversion_factor = 1 / (0.0037854 * 1000000)  # million gallons/d to m3/d
else:
    volume_conversion_factor = 1


#########################################################################
#########################################################################
#########################################################################

# Plant specifications
wacs = 49688 # (m3/d) required desalination plant OUTPUT capacity and also called wacd in DEEP (Mike's input value)
wacs_m3_hr = wacs / 24 # (m3/hr) outlet flow rate
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

rr = 1 - (ccalc/pmax) * tds # optimal recovery ratio
flow_in = wacs / rr # (m3/d) feed flow (wfm in DEEP model)
flow_in_m3_hr = flow_in / 24 # (m3/hr) feed flow
wbm = flow_in - wacs # (m3/d) brine flow
fsms = flow_in * (1000 / (24*3600)) # (kg/s) feed flow
dso = tds / (1-rr) # (ppm) brine salinity
dspms = .0025 * tds * (nflux/dflux) * .5 * (1 + (1/(1-rr))) * (1+(tim - 25)*.03) # (ppm) permeate salinity

kmtcf = np.exp(a * (1/(tim+273) - 1/(298))) # temperature correction factor
kmscf = 1.5 - .000015 * .5 * (1 + (1/(1-rr)))*tds # salinity correction factor
ndp = dflux/(nflux*kmscf) * ndpn * kmtcf/kmff # (bar) design net driving pressure



### Model parameters (pg. 36 of DEEP model manual)

# Operation and performance data
lm = 12 # (m) water plant lead time
lwp = 20 # (years) lifetime of water plant
amp = .9 # water plant operating availability
opm = .032 # water plant outage rate
oum = .06 # water plant unplanned outage rate
nmsm = 3 # management personnel
nmsl = 23 # labor personnel
app = .9 # power plant availability
apm = .9 # water production availability
acpm = apm * app # combined pp/wp load factor

# Cost data
cmu = 900 # ($/m3/d) base unit cost
cpe = .06 # ($/kWh) purchase power cost
smm = 66000 # ($) management salary
sml = 29700 # ($) labor salary
cmsp = .04 # ($/m3) specific O&M spare parts cost
cmcpr = .03 # ($/m3) specific O&M chemicals cost for pre-treatment
cmcpo = .01 # ($/m3) specific O&M chemicals cost for post-treatment
cmm = .07 # ($/m3) O&M membrane replacement cost

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



def energy_recovery(wacs):
    dphm = pavg + ndp + dpspd/2 + dppp + dpps # (bar) high head pump pressure rise
    qhp = (fsms * dphm) * kmsgsw / (ehm * ehhm * 9866) # (MW) high head pump power. Different in model vs. manual
    
    qer1 = -fsms * (1-rr)* eer * (dphm - dpspd- dpcd) * kmsgc / 10000 # (MW) energy recovery PLT
    qer2 =  -(1-rr) * eer * qhp # (MW) energy recovery other
    
    return min(qer1, qer2)
    
def power_demand(wacs):  # Total power use (qms) for a given plant capacity (wacs)
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


#Single Purpose Performance Calc (on the "Model" page of the DEEP model)

#### Do we want these calculations?  They dive into the power plant side of the model in order to get the energy 


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

def plant_availability():
    apd = (1 -  opm) * (1 - oum) # water plant operating availability
    
    return apd
    
                                                  
def annual_water_production():
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
    cdmt = (cmsp + cmcpr + cmcpo) * annual_water_production()
    cdins = kmi * wacs * cdst # insurance cost
    cdom = cdm + cdl + cdmt + cdins # total O&M cost
                                                 
    return cdom # annual O&M cost                                          

def get_flow_out(flow_in): # TODO
    flow_out = flow_in * rr
    
    return flow_out
    
def total_up_cost(m=None, G=None, flow_in = flow_in, cost_method="wt"):
    wacs = get_flow_out(flow_in) # flow_out
    
    adrev = capital_cost(wacs) + OM_cost(wacs) + energy_cost(wacs)      # total annual cost
    lifetime_cost = adrev * lwp
     
    lifetime_cost_2 = .3337 * (wacs/24)**.7177 # Mike's equation for "Reverse Osmosis Unit Fixed Capital Investment" (no O&M)
    
    return lifetime_cost # $
 

def lifetime_levelized_cost(flow_in):
    levelized = (total_up_cost(flow_in)) / (((get_flow_out(flow_in)) * 365 * lwp) * plant_availability()) # total_up_cost must return lifetime_cost, not lifetime_cost_2
    
    return levelized # lifetime levelized ($/m3)



#####################################################################
######## End of DEEP 5 model ########################################
#####################################################################


def flow_treatment_equation(m, G, link_variable):
    return link_variable * recovery_factor


def toc_treatment_equation(m, G, link_variable):
    return link_variable * (1 - toc_removal)


def nitrate_treatment_equation(m, G, link_variable):
    return link_variable * (1 - nitrate_removal)


def eeq_treatment_equation(m, G, link_variable):
    return link_variable * (1 - EEQ_removal)


def torc_treatment_equation(m, G, link_variable):
    return link_variable * (1 - TOrC_removal)


def tds_treatment_equation(m, G, link_variable_wname, up_edge):
    return link_variable_wname * 1


#####################################################################
#####################################################################
#### NETWORK RELATED FUNCTIONS AND DATA #####


def get_edge_info(unit_process_name):
    start_node = "%s_start" % unit_process_name
    end_node = "%s_end" % unit_process_name
    edge = (start_node, end_node)

    return start_node, end_node, edge


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
