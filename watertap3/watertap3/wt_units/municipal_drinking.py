from pyomo.environ import Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: McGivney & Kawamura (2008) - Figure 5.5.35b

module_name = 'municipal_drinking'

basis_year = 2020
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)
        self.base_fixed_cap_cost = 0.0403
        self.cap_scaling_exp = 0.8657
        self.chem_dict = {}
        muni_cap = (self.base_fixed_cap_cost * self.flow_in ** self.cap_scaling_exp) * self.tpec_tic
        return muni_cap

    def elect(self):
        self.lift_height = 300 * pyunits.ft
        self.pump_eff = 0.9 * pyunits.dimensionless
        self.motor_eff = 0.9 * pyunits.dimensionless
        flow_in_gpm = pyunits.convert(self.flow_in, to_units=pyunits.gallons / pyunits.minute)
        flow_in_m3hr = pyunits.convert(self.flow_in, to_units=pyunits.m ** 3 / pyunits.hour)
        electricity = (0.746 * flow_in_gpm * self.lift_height / (3960 * self.pump_eff * self.motor_eff)) / flow_in_m3hr
        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)