from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'cartridge_filtration'
basis_year = 2014
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):
    def fixed_cap(self):
        cart_filt_cap = base_fixed_cap_cost * flow_in ** cap_scaling_exp
        return cart_filt_cap

    def elect(self):  # m3/hr
        electricity = 0
        return electricity

    def get_costing(self, unit_params=None, year=None):
        self.costing = Block()
        self.costing.basis_year = basis_year
        sys_cost_params = self.parent_block().costing_param
        self.tpec_or_tic = tpec_or_tic
        if self.tpec_or_tic == 'TPEC':
            self.costing.tpec_tic = self.tpec_tic = sys_cost_params.tpec
        else:
            self.costing.tpec_tic = self.tpec_tic = sys_cost_params.tic

        time = self.flowsheet().config.time.first()

        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)

        self.chem_dict = {}

        self.base_fixed_cap_cost = 0.72557
        self.cap_scaling_exp = 0.5862

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3

        financials.get_complete_costing(self.costing)