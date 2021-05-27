from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE:
# from IT3PR, section 3.5.6 figure 3.3
# from IT3PR, section 3.5.6 figure 3.3

module_name = 'tri_media_filtration'
basis_year = 2014
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):
    def fixed_cap(self):
        tri_media_cap = self.base_fixed_cap_cost * self.flow_in ** self.cap_scaling_exp
        return tri_media_cap

    def elect(self):  # m3/hr
        electricity = 1e-4   # kWh/m3
        return electricity

    def get_costing(self, unit_params=None, year=None):
        self.costing = Block()
        self.costing.basis_year = basis_year
        sys_cost_params = self.parent_block().costing_param

        time = self.flowsheet().config.time.first()

        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)
        
        self.chem_dict = {}
        self.base_fixed_cap_cost = 0.72557
        self.cap_scaling_exp = 0.5862

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3


        financials.get_complete_costing(self.costing)
