from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# citation here
## ELECTRICITY:
# citation here

module_name = 'passthrough'
basis_year = 2020
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self):
        '''
        Docstrings go here.

        :return:
        '''
        self.chem_dict = {}
        passthrough_cap = 0
        return passthrough_cap

    def elect(self):
        '''
        Docstrings go here.

        :return:
        '''
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
        self.deltaP_outlet.unfix()
        self.deltaP_waste.unfix()
        self.pressure_out.fix(1)
        self.pressure_waste.fix(1)
        financials.get_complete_costing(self.costing)