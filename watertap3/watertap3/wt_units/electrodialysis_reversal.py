from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'electrodialysis_reversal'
basis_year = 2016
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

        self.chem_dict = {}
        tds_in = pyunits.convert(self.conc_mass_in[time, 'tds'], to_units=(pyunits.mg / pyunits.L))
        tds_out = pyunits.convert(self.conc_mass_out[time, 'tds'], to_units=(pyunits.mg / pyunits.L))
        delta_tds = tds_in - tds_out

        def fixed_cap(flow_in):
            ed_cap = 31 * flow_in / 946  # $MM
            return ed_cap

        def electricity():
            ed_elect = (delta_tds / 630) * 0.337  # kwh/m3
            return ed_elect

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity()  # kwh/m3

        financials.get_complete_costing(self.costing)