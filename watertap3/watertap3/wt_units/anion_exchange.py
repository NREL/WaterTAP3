from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import cost_curve, financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE
# CAPITAL AND ELECTRICITY:
# EPA Drinking Water Treatment Technology Unit Cost Models
# https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models
# EPA model run several times under different conditions
# Regression for capital and electricity costs based on regression from those model outputs.

module_name = 'anion_exchange'
basis_year = 2017
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.tds_in = unit_params['tds_in']
        self.cost_coeffs, self.elect_coeffs, self.mats_name, self.mats_cost, _ = cost_curve(module_name, tds_in=self.tds_in)
        for k, v in self.mats_cost.items():
            self.mats_cost[k] = v * (pyunits.kg / pyunits.m ** 3)
        self.chem_dict = self.mats_cost
        an_ex_cap = self.cost_coeffs[0] * self.flow_in ** self.cost_coeffs[1]  # $
        return an_ex_cap * 1E-6  # M$

    def elect(self):  # m3/hr
        electricity = self.elect_coeffs[0] * self.flow_in ** self.elect_coeffs[1]  # kWh/m3
        return electricity

    def get_costing(self, unit_params=None, year=None):
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)