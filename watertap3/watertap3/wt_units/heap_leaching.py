from pyomo.environ import Block, Expression, value, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# "Precious Metal Heap Leach Design and Practice" Daniel W. Kappes (2002)
# Mineral Processing Plant Design, Practice, and Control, Volume 1, Published 2002 by SME (1606)
# http://ore-max.com/pdfs/resources/precious_metal_heap_leach_design_and_practice.pdf


module_name = 'heap_leaching'
basis_year = 2008
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        time = self.flowsheet().config.time.first()
        self.chem_dict = {}
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        try:
            self.mining_capacity = unit_params['mining_capacity'] * (pyunits.tonnes / pyunits.day)
            self.ore_heap_soln = unit_params['ore_heap_soln'] * (pyunits.gallons / pyunits.tonnes)
            self.make_up_water = 85 / 500 * self.ore_heap_soln * (pyunits.gallons / pyunits.tonnes)
            self.make_up_water = pyunits.convert(self.make_up_water * self.mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))
        except:
            self.mining_capacity = 922 * (pyunits.tonnes / pyunits.day)
            self.ore_heap_soln = 500 * (pyunits.gallons / pyunits.tonnes)
            self.make_up_water = 85 * (pyunits.gallons / pyunits.tonnes)
            self.make_up_water = pyunits.convert(self.make_up_water * self.mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))
        self.mine_equip = 0.00124 * self.mining_capacity ** 0.93454
        self.mine_develop = 0.01908 * self.mining_capacity ** 0.43068
        self.crushing = 0.0058 * self.mining_capacity ** 0.6651
        self.leach = 0.0005 * self.mining_capacity ** 0.94819
        self.stacking = 0.00197 * self.mining_capacity ** 0.77839
        self.dist_recov = 0.00347 * self.mining_capacity ** 0.71917
        self.subtotal = (self.mine_equip + self.mine_develop + self.crushing + self.leach + self.stacking + self.dist_recov)
        self.perc = 0.3102 * self.mining_capacity ** 0.1119  # regression made by kurby in excel - mining capacity vs percent of subtotal
        if value(self.perc) > 1:
            self.perc = 1
        self.other = self.subtotal * self.perc
        self.mining_to_heap_basis = (self.mine_equip + self.mine_develop + self.crushing + self.leach) * (1 + self.perc)
        self.mining_to_heap_exp = (self.mine_equip * 0.935 + self.mine_develop * 0.431 + self.crushing * 0.665 + self.leach * 0.948) / (
                    self.mine_equip + self.mine_develop + self.crushing + self.leach)
        self.stacking_basis = self.stacking * (1 + self.perc)
        self.stacking_exp = (self.mine_equip * 0.935 + self.mine_develop * 0.431 + self.crushing * 0.665 + self.leach * 0.948 + self.stacking * 0.778 + self.dist_recov * 0.719) / (
                self.mine_equip + self.mine_develop + self.crushing + self.leach + self.stacking + self.dist_recov)
        self.mine_equip_op = 22.54816 * self.mining_capacity ** 0.74807
        self.crushing_op = 4.466 * self.mining_capacity ** 0.8794
        self.leach_op = 6.34727 * 0.68261
        self.stacking_op = 6.28846 * self.mining_capacity ** 0.56932
        self.dist_recov_op = 7.71759 * self.mining_capacity ** 0.91475
        self.mining_to_heap_other = (self.mine_equip_op + self.crushing_op + self.leach_op) / self.make_up_water
        self.other_var_cost = self.mining_to_heap_other
        self.stacking_other = self.stacking_op / self.make_up_water
        self.flow_factor = self.flow_in / 73
        heap_cap = self.flow_factor * self.mining_to_heap_basis ** self.mining_to_heap_exp
        return heap_cap

    def elect(self):
        electricity = 0
        return electricity

    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')  # $M
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')  # kwh/m3
        financials.get_complete_costing(self.costing)


