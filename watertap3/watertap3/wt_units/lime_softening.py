from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: # Minnesota Rural Water Association, Chapter 16 Lime Softening #(https://www.mrwa.com/WaterWorksMnl/Chapter%2016%20Lime%20Softening.pdf)
# https://www.necoindustrialwater.com/analysis-ion-exchange-vs-lime-softening/

module_name = 'lime_softening'
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

        # FIRST TIME POINT FOR STEADY-STATE ASSUMPTION
        time = self.flowsheet().config.time.first()
        # UNITS = m3/hr
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)

        base_fixed_cap_cost = 0.0704  # from VAR tab
        cap_scaling_exp = 0.7306  # from VAR tab

        lift_height = 100 * pyunits.ft
        pump_eff = 0.9 * pyunits.dimensionless
        motor_eff = 0.9 * pyunits.dimensionless

        chem_name = 'Lime_Suspension_CaOH_2'
        magnesium_dissolved_lime = pyunits.convert(unit_params['lime'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
        magnesium_dissolved_factor = 30 * pyunits.dimensionless  # TODO
        chemical_dosage = magnesium_dissolved_factor * magnesium_dissolved_lime
        solution_density = 1250 * (pyunits.kg / pyunits.m ** 3)  # kg/m3
        self.chem_dict = {chem_name: chemical_dosage}

        lift_height = 100 * pyunits.ft
        pump_eff = 0.9 * pyunits.dimensionless
        motor_eff = 0.9 * pyunits.dimensionless

        def solution_vol_flow(flow_in):  # m3/hr
            chemical_rate = flow_in * chemical_dosage  # kg/hr
            chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.kg / pyunits.day))
            soln_vol_flow = chemical_rate / solution_density  # m3/d
            return soln_vol_flow  # m3/d

        def fixed_cap(flow_in):
            lime_cap = base_fixed_cap_cost * flow_in ** cap_scaling_exp
            return lime_cap

        def electricity(flow_in):  # m3/hr
            soln_vol_flow = pyunits.convert(solution_vol_flow(flow_in), to_units=(pyunits.gallon / pyunits.minute))
            electricity = (0.746 * soln_vol_flow * lift_height / (3960 * pump_eff * motor_eff)) / flow_in  # kWh/m3
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)