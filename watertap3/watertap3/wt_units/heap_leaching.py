from pyomo.environ import Block, Expression, units as pyunits, value
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'heap_leaching'
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

        # FIRST TIME POINT FOR STEADY-STATE ASSUMPTION
        time = self.flowsheet().config.time.first()

        self.chem_dict = {}

        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

        try:
            mining_capacity = unit_params['mining_capacity'] * (pyunits.tonnes / pyunits.day)
            ore_heap_soln = unit_params['ore_heap_soln'] * (pyunits.gallons / pyunits.tonnes)
            make_up_water = 85 / 500 * ore_heap_soln * (pyunits.gallons / pyunits.tonnes)
            make_up_water = pyunits.convert(make_up_water * mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))
        except:
            mining_capacity = 922 * (pyunits.tonnes / pyunits.day)
            ore_heap_soln = 500 * (pyunits.gallons / pyunits.tonnes)
            make_up_water = 85 * (pyunits.gallons / pyunits.tonnes)
            make_up_water = pyunits.convert(make_up_water * mining_capacity, to_units=(pyunits.m ** 3 / pyunits.hour))

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
        mining_to_heap_basis = (mine_equip + mine_develop + crushing + leach) * (1 + perc)
        mining_to_heap_exp = (mine_equip * 0.935 + mine_develop * 0.431 + crushing * 0.665 + leach * 0.948) / (mine_equip + mine_develop + crushing + leach)
        stacking_basis = stacking * (1 + perc)
        stacking_exp = (mine_equip * 0.935 + mine_develop * 0.431 + crushing * 0.665 + leach * 0.948 + stacking * 0.778 + dist_recov * 0.719) / (
                mine_equip + mine_develop + crushing + leach + stacking + dist_recov)

        mine_equip_op = 22.54816 * mining_capacity ** 0.74807
        crushing_op = 4.466 * mining_capacity ** 0.8794
        leach_op = 6.34727 * 0.68261
        stacking_op = 6.28846 * mining_capacity ** 0.56932
        dist_recov_op = 7.71759 * mining_capacity ** 0.91475

        mining_to_heap_other = (mine_equip_op + crushing_op + leach_op) / make_up_water
        stacking_other = stacking_op / make_up_water

        flow_factor = flow_in / 73

        def fixed_cap(flow_in):
            heap_cap = flow_factor * mining_to_heap_basis ** mining_to_heap_exp
            return heap_cap

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = 0  # kwh/m3

        self.other_var_cost = mining_to_heap_other

        financials.get_complete_costing(self.costing)