from pyomo.environ import Block, Expression, NonNegativeReals, Var, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'deep_well_injection'
basis_year = 2011
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
        time = self.flowsheet().config.time
        t = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[t], to_units=pyunits.m ** 3 / pyunits.hr)

        self.lift_height = Var(time,
                               initialize=400,
                               domain=NonNegativeReals,
                               units=pyunits.ft,
                               doc='lift height for pump in ft')  # lift height in feet
        try:
            self.lift_height.fix(unit_params['lift_height'])
        except:
            self.lift_height.fix(400)

        self.delta_pressure = self.lift_height[t] * 0.0299  # lift height converted to bar

        cap_scaling_exp = 0.7
        cap_scaling_val = 473.2

        well_pump_fixed_cap_cost = 16.9  # this is wells/pumps fixed capital AFTER applying TIC factor -- DOES NOT INCLUDE ANY PIPING
        pipe_cost_basis = 35000  # $ / (inch * mile) -- this value taken from produced water case studies in WT3 Excel model
        pipe_distance = unit_params['pipe_distance'] * pyunits.miles
        pipe_diameter = 8 * pyunits.inches
        pipe_fixed_cap_cost = (pipe_cost_basis * pipe_distance * pipe_diameter) * 1E-6
        tot_fixed_cap = well_pump_fixed_cap_cost + pipe_fixed_cap_cost
        pump_eff = 0.9
        motor_eff = 0.9

        self.chem_dict = {}

        def fixed_cap(flow_in):
            cap_scaling_factor = flow_in / cap_scaling_val
            deep_well_cap = tot_fixed_cap * cap_scaling_factor ** cap_scaling_exp
            return deep_well_cap

        def electricity(flow_in):
            flow_in_gpm = pyunits.convert(flow_in, to_units=(pyunits.gallon / pyunits.minute))
            electricity = (0.746 * flow_in_gpm * self.lift_height[t] / (3960 * pump_eff * motor_eff)) / flow_in
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)