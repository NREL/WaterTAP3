# Import Pyomo libraries

# Import IDAES cores

# Import WaterTAP# finanacilas module
from financials import * #ARIEL ADDED

# Import properties and units from "WaterTAP Library"

import numpy as np



# Plant specifications
# wacs = 94152 # (m3/d) required desalination plant OUTPUT capacity and also called wacd in DEEP (Mike's input value)
# wacs_m3_hr = wacs / 24 # (m3/hr) outlet flow rate
tim = 25 # (deg. C) feed water inlet temperature at RO element entry   (DEEP model default)
tds = 35000 # (ppm) total disolved solids   (Mike's input value)

# RO Technical parameters
pmax = 85 # (bar) maximum design pressure of the membrane (matched to Carlsbad value in VAR tab)
ccalc = .00115 # constant used for recovery ratio calculation
dflux = 13.6 # (l/m2-h) design average permeate flux
nflux = 27.8 # (l/m2-h) normal permeate flux
a = 3500 # polyamide membrane permeability constant
ndpn = 44.7 # (bar) nominal net driving pressure
kmff = .9 # fouling factor
kmaiicf = 1.05 # aggregation of individual ions correction factor
kmsgc = 1.04 # specific gravity of concentrate correction factor
kmsgsw = 1.02 # specific gravity of seawater feed correction factor ##########

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

fma = .73 # membrane area factor (over reference)
fpp = .99 # pretreatment, pump, pump sizing

# RO plant and feed water characteristics 
qsom = 0 # (kwh/m3) other specific power use


### Model parameters (pg. 36 of DEEP model manual)

# Operation and performance data
lm = 12 # (m) water plant lead time
lwp = 20 # (years) lifetime of water plant
amp = .9 # water plant operating availability
nmsm = 4 # management personnel
nmsl = 31 # labor personnel
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


cost_factor_for_number_of_passes = 1
parallel_units = 1




rr = 1 - (ccalc/pmax) * tds # optimal recovery ratio

flow_in = 104.6121 * .9 #MGD
            
# flow_in = wacs / self.rr # (m3/d) feed flow (wfm in DEEP model)
# flow_in_m3_hr = flow_in / 24 # (m3/hr) feed flow
# wbm = flow_in - wacs # (m3/d) brine flow
dso = tds / (1-rr) # (ppm) brine salinity
dspms = .0025 * tds * (nflux/dflux) * .5 * (1 + (1/(1-rr))) * (1+(tim - 25)*.03) # (ppm) permeate salinity

kmtcf = np.exp(a * (1/(tim+273) - 1/(298))) # temperature correction factor
kmscf = 1.5 - .000015 * .5 * (1 + (1/(1-rr)))*tds # salinity correction factor
ndp = dflux/(nflux*kmscf) * ndpn * kmtcf/kmff # (bar) design net driving pressure



def energy_recovery(wacs):
    fsms = wacs/rr * (1000 / (24*3600)) # (kg/s) feed flow

    dphm = pavg + ndp + dpspd/2 + dppp + dpps # (bar) high head pump pressure rise
    qhp = (fsms * dphm) / (ehm * ehhm *eem * 9866)*kmsgsw # (MW) high head pump power. Different in model vs. manual. (Model divides by eem and * kmsgsw, manual and Mike do not)

    qer1 = -fsms * (1-rr)* eer * (dphm - dpspd- dpcd) * kmsgc / 10000 # (MW) energy recovery PLT
    qer2 =  -(1-rr) * eer * qhp # (MW) energy recovery other

#     if qer1 < qer2:
#         recovery = qer1
#     else:
#         recovery = qer2

    return qer1

def power_demand(wacs):  # Total power use (qms) for a given plant output capacity (wacs)
    fsms = wacs/rr * (1000 / 24 / 3600) # (kg/s) feed flow

    dphm = pavg + ndp + dpspd/2 + dppp + dpps # (bar) high head pump pressure rise
    
    #qhp = (fsms * dphm) / (ehm * ehhm * 9866)  # (MW) high head pump power. (Model divides by eem and * kmsgsw, manual and Mike do not)
    qhp = (fsms * dphm) / (ehm * ehhm * eem * 9866) * kmsgsw # (MW) high head pump power. (Model version)
    
    #qsp = (fsms * dpsm) / (esm * 9866) # (MW) seawater pumping power. (Model divides by eem, manual and Mike do not)
    qsp = (fsms * dpsm) / (esm * eem * 9866) * kmsgsw # (MW) seawater pumping power. (Model version)
    
    #qbp = (fsms * dpbm) / (ebm  * 9866) # (MW) booster pump power. (Model divides by eem, manual and Mike do not)
    qbp = (fsms * dpbm) / (ebm * eem * 9866) * kmsgsw  # (MW) booster pump power. (Model version)
    
    qom = (wacs * qsom) / (24 * 1000) # (MW) other power

    qms = qsp + qbp + qhp + energy_recovery(wacs) + qom # (MW) total power use

    return qms #(MW)
 

def energy_demand(wacs): # total energy (including energy recovery)
    tot_pow = power_demand(wacs) * 24 * 365 * 1000

    return tot_pow # (kWh) annual energy demand


def power_per_outlet(wacs):
    qdp = power_demand(wacs) / wacs # (MW) specific power use per m3/d produced

    return qdp

def power_per_inlet(wacs):
    tppi = power_demand(wacs) / (wacs/rr) # (MW) specific power use per input feed

    return tppi

def get_osmotic_pressure(C,T): # 
    osmotic_pressure = .0000348 * (T + 273) * (C/14.7)  # (bar) osmotic pressure function  

    return osmotic_pressure


pavg = (get_osmotic_pressure(tds,tim) + get_osmotic_pressure(dso,tim))/2 * kmaiicf # (bar) average osmotic pressure


#########################################################################
#########################################################################
################# UP COST CALCULATIONS FOR TREATMENT TRAIN ##############
#########################################################################
#########################################################################

# excludes the cost of water storage, transportation, distribution


def cap_recovery(i,n):
    lfc = (i * (1 + i)**n) / ((1 + i) ** n - 1)

    return lfc # capital recovery factor function
  


def fixed_cap(wacs):
    cdio = csmo * cmu # in/outfall specific cost
    cdst = cmu * kmsus + cdio # total specific base cost
    cdt = wacs * cdst # water plant adjusted total base cost
    dcdo = cdt * kmo # water plant owners cost
    dcdc = (cdt + dcdo) * kmc # water plant contingency cost
    cdcon = cdt + dcdo + dcdc # water plant total construction cost
    idcd = cdcon * ((1 + ir) ** (lm/24) - 1 ) # interest during construction
    csinv = cdcon + idcd # total investment cost

    
    #Comparisons to Excel:
    mcgivney = .3337 * (wacs/24)**.7177 * cost_factor_for_number_of_passes * parallel_units # Mike's "Reverse Osmosis Unit Fixed Capital Investment" (no O&M) $millions
    guo_cap_cost =  0.13108 * (wacs/24) ** 0.82523 * cost_factor_for_number_of_passes * parallel_units # Mike's  (no O&M) $millions
    #return mcgivney
     
    
    return csinv/1000000 # $M; total investment cost


def capital_cost(wacs):

    adfc = fixed_cap(wacs) * cap_recovery(i,lwp) # $M, total annual capital cost
    return adfc


def annual_water_production(wacs):

    wpd = wacs * amp * 365 # total water production per year

    return wpd # m3 per year


def energy_cost(wacs): # all based on backup heat and load factors
    energy_cost = energy_demand(wacs) * energy_cost_factor

    return energy_cost/1000000 # annual cost; $ M


def OM_cost(wacs):
    cdm = nmsm * smm # management cost
    cdl = nmsl * sml # labour cost
    
    cdio = csmo * cmu # in/outfall specific cost
    cdst = cmu * kmsus + cdio # total specific base cost
    cdt = (wacs * cdst) # water plant adjust base cost
    dcdo = cdt * kmo # water plant owners cost
    dcdc = (cdt + dcdo) * kmc # water plant contingency cost
    
    cdmt = (cmm * fma + cmsp * fpp + cmcpr + cmcpo) * annual_water_production(wacs) # material cost
    cdcon = dcdc + dcdo + cdt # water plant total construction
    cdins = kmi * cdcon # insurance cost
    
    cdom = cdm + cdl + cdmt + cdins # total O&M cost
    
    return cdom/1000000 # annual O&M cost; $ M                                         

def get_flow_out(flow_in): 
    flow_in_m3d = flow_in * 3785.4118 # conversion from MGD to m3/d
    flow_out = flow_in_m3d * rr

    return flow_out #m3/d


def total_up_cost(m=None, G=None, flow_in=flow_in, cost_method="wt"):
    wacs = get_flow_out(flow_in) # flow_out m3/d

    adrev = capital_cost(wacs) + OM_cost(wacs) + energy_cost(wacs) # total cost; $ M

    lifetime_cost = adrev * lwp # $ M

    
    return lifetime_cost # $M
    
   

def lifetime_levelized_cost(flow_in):
    levelized = total_up_cost(flow_in) / (get_flow_out(flow_in) * 365 * lwp * plant_availability()) # total_up_cost must return lifetime_cost, not lifetime_cost_2

    return levelized # lifetime levelized (M$/m3)