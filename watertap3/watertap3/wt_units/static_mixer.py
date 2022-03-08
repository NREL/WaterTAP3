from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# Based on TABLE 7.2 in:
# Chemical Engineering Design, 2nd Edition. Principles, Practice and Economics of Plant and Process Design (2012)
# https://www.elsevier.com/books/chemical-engineering-design/towler/978-0-08-096659-5
# eBook ISBN: 9780080966601
## ELECTRICITY:

module_name = 'static_mixer'
basis_year = 2010
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        self.number_of_units = 2
        self.chem_dict = {}

        # self.a = 570
        # self.b = 1170
        # self.c = 0.4

        self.a = 1065.7
        self.b = 0.336

        # self.a = 14317.142
        # self.b = 389.454
        # self.c = -57.342
        # source_cost = self.a + self.b * self.flow_in ** self.c
        source_cost = self.a * self.flow_in ** self.b
        mix_cap = (source_cost * self.tpec_tic * self.number_of_units) * 1E-6
        return mix_cap

    def elect(self):
        electricity = 0
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