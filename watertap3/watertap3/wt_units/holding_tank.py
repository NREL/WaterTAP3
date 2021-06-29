from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# "Cone roof tank" costs from:
# DOE/NETL-2002/1169 - Process Equipment Cost Estimation Final Report
# Loh, H. P., Lyons, Jennifer, and White, Charles W. Process Equipment Cost Estimation, Final Report.
# United States: N. p., 2002. Web. doi:10.2172/797810.
# Regression of cost vs. capacity
# Capacity calculated based on storage time and surge capacity (user inputs)

module_name = 'holding_tank'
basis_year = 2007
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        '''
        **"unit_params" are the unit parameters passed to the model from the input sheet as a Python dictionary.**

        **EXAMPLE: {'avg_storage_time': 24, 'surge_cap': 0.2}**

        :param avg_storage_time: storage time in hours
        :param surge_cap: is the surge capacity used for calculating storage volume, expressed as a fraction of the total flow (e.g. for 20% surge capacity, use 0.2)

        :return: Fixed capital for storage tanks.
        '''
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.storage_duration = unit_params['avg_storage_time'] * pyunits.hours
        self.surge_cap = unit_params['surge_cap'] * pyunits.dimensionless
        self.capacity_needed = self.flow_in * self.storage_duration * (1 + self.surge_cap)
        self.a = 0.0001482075293096916
        self.b = 1.0143391604819805
        self.chem_dict = {}
        tank_cap = self.a * self.capacity_needed ** self.b
        return tank_cap

    def elect(self):
        '''
        WaterTAP3 has no electricity intensity associated with storage tanks.
        '''
        electricity = 0
        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')
        financials.get_complete_costing(self.costing)

