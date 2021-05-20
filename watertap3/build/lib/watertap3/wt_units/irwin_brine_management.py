from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'irwin_brine_management'
basis_year = 2019
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

        self.conc_mass_tot = 0
        for constituent in self.config.property_package.component_list:
            self.conc_mass_tot += self.conc_mass_in[time, constituent]

        self.density = 0.6312 * self.conc_mass_tot + 997.86  # kg/m3 # assumption from Tim's reference (ask Ariel for Excel if needed)
        self.total_mass = total_mass = self.density * flow_in  # kg/hr to tons for Mike's Excel needs
        self.chem_dict = {}

        lift_height = 100 * pyunits.ft
        pump_eff = 0.9 * pyunits.dimensionless
        motor_eff = 0.9 * pyunits.dimensionless
        capacity_basis = 9463.5
        base_fixed_cap_cost = 31
        cap_scaling_exp = 0.873

        def fixed_cap():
            fixed_cap_unadj = base_fixed_cap_cost * (total_mass / capacity_basis) ** cap_scaling_exp
            return fixed_cap_unadj  # M$

        def electricity(flow_in):
            flow_in_gpm = pyunits.convert(flow_in, to_units=pyunits.gallons / pyunits.minute)
            electricity = (0.746 * flow_in_gpm * lift_height / (3960 * pump_eff * motor_eff)) / flow_in  # kWh/m3
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)