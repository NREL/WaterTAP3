from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Based on costs for CHLORINE STORAGE AND FEED - FIGURE XXXXX
# Cost Estimating Manual for Water Treatment Facilities (McGivney/Kawamura) (2008)
# DOI:10.1002/9780470260036
## ELECTRICITY:
# No expected energy consumption for CO2 because storage cylinder is at 1000 psig

module_name = 'co2_addition'
basis_year = 2019
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        '''
        **"unit_params" are the unit parameters passed to the model from the input sheet as a Python dictionary.**

        **EXAMPLE: {'dose': 10}**

        Fixed capital for alum addition is a function of alum dose, alum solution flow, and the number of units.

        **Assumptions:**

        * Number of units = 2

        :return: Alum addition fixed capital cost [$MM]
        '''
        self.chem_dict = {}
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)
        self.base_fixed_cap_cost = 0.464
        self.cap_scaling_exp = 0.7
        co2_cap = self.base_fixed_cap_cost * self.flow_in ** self.cap_scaling_exp
        return co2_cap

    def elect(self):
        '''
        Electricity intensity.

        :return: Electricity intensity [kWh/m3]
        '''
        electricity = 0.01
        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)