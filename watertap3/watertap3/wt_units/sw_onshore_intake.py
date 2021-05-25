from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: Voutchkov (2018) figures 4.2 and 4.4

module_name = 'sw_onshore_intake'
basis_year = 2018
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        sw_intake_cap = self.base_fixed_cap_cost * self.flow_in ** self.cap_scaling_exp
        return sw_intake_cap

    def elect(self):
        flow_in_gpm = pyunits.convert(self.flow_in, to_units=pyunits.gallons / pyunits.minute)
        flow_in_m3hr = pyunits.convert(self.flow_in, to_units=pyunits.m ** 3 / pyunits.hour)
        electricity = (0.746 * flow_in_gpm * self.lift_height / (3960 * self.pump_eff * self.motor_eff)) / flow_in_m3hr  # kWh/m3
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

        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.day)

        self.lift_height = 100 * pyunits.ft
        self.pump_eff = 0.9 * pyunits.dimensionless
        self.motor_eff = 0.9 * pyunits.dimensionless

        self.base_fixed_cap_cost = 0.000215
        self.cap_scaling_exp = 0.888803

        self.chem_dict = {}

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3

        financials.get_complete_costing(self.costing)