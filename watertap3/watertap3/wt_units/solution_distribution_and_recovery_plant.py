from pyomo.environ import Block, Expression, value, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# "Precious Metal Heap Leach Design and Practice" Daniel W. Kappes (2002)
# Mineral Processing Plant Design, Practice, and Control, Volume 1, Published 2002 by SME (1606)
# http://ore-max.com/pdfs/resources/precious_metal_heap_leach_design_and_practice.pdf

module_name = 'solution_distribution_and_recovery_plant'
basis_year = 2008
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def fixed_cap(self, unit_params):
        time = self.flowsheet().config.time.first()
        self.flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        try:
            self.mining_capacity = unit_params['mining_capacity'] * (pyunits.tonnes / pyunits.day)
            self.ore_heap_soln = unit_params['ore_heap_soln'] * (pyunits.gallons / pyunits.tonnes)
            self.make_up_water = 85 / 500 * self.ore_heap_soln * (pyunits.gallons / pyunits.tonnes)
            self.recycle_water = self.ore_heap_soln - self.make_up_water
            self.make_up_water = pyunits.convert(self.make_up_water * self.mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))
            self.recycle_water = pyunits.convert(self.recycle_water * self.mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))

        except:
            self.mining_capacity = 922 * (pyunits.tonnes / pyunits.day)
            self.ore_heap_soln = 500 * (pyunits.gallons / pyunits.tonnes)
            self.make_up_water = 85 * (pyunits.gallons / pyunits.tonnes)
            self.recycle_water = self.ore_heap_soln - self.make_up_water
            self.make_up_water = pyunits.convert(self.make_up_water * self.mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))
            self.recycle_water = pyunits.convert(self.recycle_water * self.mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))

        self.dist_recov = 0.00347 * self.mining_capacity ** 0.71917

        self.perc = 0.3102 * self.mining_capacity ** 0.1119  # regression made by KAS in excel - mining capacity vs percent of subtotal
        if value(self.perc) > 1:
            self.perc = 1

        self.dist_recov_basis = self.dist_recov * (1 + self.perc)

        self.dist_recov_op = 7.71759 * self.mining_capacity ** 0.91475
        self.dist_recov_exp = 0.719
        self.dist_recov_other = self.dist_recov_op * 1E-6 * 365
        self.costing.other_var_cost = self.dist_recov_other

        self.flow_factor = self.flow_in / self.recycle_water
        self.chem_dict = {}
        dist_recov_cap = self.flow_factor * self.dist_recov_basis ** self.dist_recov_exp
        return dist_recov_cap

    def elect(self):
        # electricity = 1.8 * pyunits.convert(self.mining_capacity, to_units=(pyunits.tonnes / pyunits.hour)) / self.recycle_water
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