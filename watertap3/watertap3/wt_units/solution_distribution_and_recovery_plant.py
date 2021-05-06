from pyomo.environ import Block, Expression, units as pyunits, value
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL:
# "Precious Metal Heap Leach Design and Practice" Daniel W. Kappes (2002)
# Mineral Processing Plant Design, Practice, and Control, Volume 1, Published 2002 by SME (1606)
# http://ore-max.com/pdfs/resources/precious_metal_heap_leach_design_and_practice.pdf

module_name = 'solution_distribution_and_recovery_plant'
basis_year = 2008
tpec_or_tic = 'TPEC'


class UnitProcess(WT3UnitProcess):

    def get_costing(self, unit_params=None, year=None):
        self.costing = Block()
        self.costing.basis_year = basis_year
        sys_cost_params = self.parent_block().costing_param
        self.tpec_or_tic = tpec_or_tic
        if self.tpec_or_tic == 'TPEC':
            self.costing.tpec_tic = tpec_tic = sys_cost_params.tpec
        else:
            self.costing.tpec_tic = tpec_tic = sys_cost_params.tic

        '''
        We need a get_costing method here to provide a point to call the
        costing methods, but we call out to an external consting module
        for the actual calculations. This lets us easily swap in different
        methods if needed.

        Within IDAES, the year argument is used to set the initial value for
        the cost index when we build the model.
        '''

        time = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

        try:
            mining_capacity = unit_params['mining_capacity'] * (pyunits.tonnes / pyunits.day)
            ore_heap_soln = unit_params['ore_heap_soln'] * (pyunits.gallons / pyunits.tonnes)
            make_up_water = 85 / 500 * ore_heap_soln * (pyunits.gallons / pyunits.tonnes)
            recycle_water = ore_heap_soln - make_up_water
            make_up_water = pyunits.convert(make_up_water * mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))
            recycle_water = pyunits.convert(recycle_water * mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))

        except:
            mining_capacity = 922 * (pyunits.tonnes / pyunits.day)
            ore_heap_soln = 500 * (pyunits.gallons / pyunits.tonnes)
            make_up_water = 85 * (pyunits.gallons / pyunits.tonnes)
            recycle_water = ore_heap_soln - make_up_water
            make_up_water = pyunits.convert(make_up_water * mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))
            recycle_water = pyunits.convert(recycle_water * mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))

        mine_equip = 0.00124 * mining_capacity ** 0.93454
        mine_develop = 0.01908 * mining_capacity ** 0.43068
        crushing = 0.0058 * mining_capacity ** 0.6651
        leach = 0.0005 * mining_capacity ** 0.94819
        stacking = 0.00197 * mining_capacity ** 0.77839
        dist_recov = 0.00347 * mining_capacity ** 0.71917
        subtotal = (mine_equip + mine_develop + crushing + leach + stacking + dist_recov)
        perc = 0.3102 * mining_capacity ** 0.1119  # regression made by kurby in excel - mining capacity vs percent of subtotal
        if value(perc) > 1:
            perc = 1
        other = subtotal * perc
        stacking_basis = stacking * (1 + perc)
        stacking_exp = (mine_equip * 0.935 + mine_develop * 0.431 + crushing * 0.665 + leach * 0.948 + stacking * 0.778 + dist_recov * 0.719) / (
                mine_equip + mine_develop + crushing + leach + stacking + dist_recov)
        dist_recov_basis = dist_recov * (1 + perc)
        stacking_op = 6.28846 * mining_capacity ** 0.56932
        dist_recov_op = 7.71759 * mining_capacity ** 0.91475
        dist_recov_exp = 0.719
        dist_recov_other = dist_recov_op / make_up_water
        stacking_other = stacking_op / make_up_water  # make_up_flow needs to be in m3/day?
        # basis year for the unit model - based on reference for the method.
        flow_factor = flow_in / recycle_water

        self.chem_dict = {}

        def fixed_cap():
            dist_recov_cap = flow_factor * dist_recov_basis ** dist_recov_exp
            return dist_recov_cap

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = 0  # kwh/m3

        self.other_var_cost = dist_recov_other

        financials.get_complete_costing(self.costing)