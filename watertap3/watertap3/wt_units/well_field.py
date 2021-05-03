from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'well_field'
basis_year = 2020
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

        base_fixed_cap_cost = 4731.6
        cap_scaling_exp = 0.9196

        # lift_height = 100 * pyunits.ft  # ft # ft
        # pump_eff = 0.9 * pyunits.dimensionless
        # motor_eff = 0.9 * pyunits.dimensionless

        self.chem_dict = {}

        def fixed_cap(flow_in):
            well_cap = base_fixed_cap_cost * flow_in ** cap_scaling_exp * 1E-6
            return well_cap

        def electricity(flow_in):
            # flow_in_gpm = pyunits.convert(self.parent_block().flow_vol_in[time], to_units=pyunits.gallons / pyunits.minute)
            # flow_in_m3hr = pyunits.convert(self.parent_block().flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hour)
            # electricity = (0.746 * flow_in_gpm * lift_height / (3960 * pump_eff * motor_eff)) / flow_in_m3hr  # kWh/m3
            electricity = 0
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)