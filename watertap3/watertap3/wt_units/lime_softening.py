from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Minnesota Rural Water Association, Chapter 16 Lime Softening
# #(https://www.mrwa.com/WaterWorksMnl/Chapter%2016%20Lime%20Softening.pdf)
# https://www.necoindustrialwater.com/analysis-ion-exchange-vs-lime-softening/

module_name = 'lime_softening'
basis_year = 2020
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def solution_vol_flow(self):  # m3/hr
        chemical_rate = self.flow_in * self.chemical_dosage  # kg/hr
        chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.kg / pyunits.day))
        soln_vol_flow = chemical_rate / self.solution_density  # m3/d
        return soln_vol_flow  # m3/d

    def fixed_cap(self):
        lime_cap = self.base_fixed_cap_cost * self.flow_in ** self.cap_scaling_exp
        return lime_cap

    def elect(self):  # m3/hr
        soln_vol_flow = pyunits.convert(self.solution_vol_flow(), to_units=(pyunits.gallon / pyunits.minute))
        electricity = (0.746 * soln_vol_flow * self.lift_height / (3960 * self.pump_eff * self.motor_eff)) / self.flow_in  # kWh/m3
        return electricity

    def get_costing(self, unit_params=None, year=None):
        financials.create_costing_block(self, basis_year, tpec_or_tic)

        time = self.flowsheet().config.time.first()

        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

        self.base_fixed_cap_cost = 0.0704
        self.cap_scaling_exp = 0.7306

        self.lift_height = 100 * pyunits.ft
        self.pump_eff = 0.9 * pyunits.dimensionless
        self.motor_eff = 0.9 * pyunits.dimensionless

        chem_name = 'Lime_Suspension_CaOH_2'
        self.magnesium_dissolved_lime = pyunits.convert(unit_params['lime'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
        self.magnesium_dissolved_factor = 30 * pyunits.dimensionless  #
        self.chemical_dosage = self.magnesium_dissolved_factor * self.magnesium_dissolved_lime
        self.solution_density = 1250 * (pyunits.kg / pyunits.m ** 3)  # kg/m3
        self.chem_dict = {chem_name: self.chemical_dosage}


        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3

        financials.get_complete_costing(self.costing)