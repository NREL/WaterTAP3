from pyomo.environ import Block, Constraint, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'brine_concentrator'
basis_year = 2007
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

        tds_in = pyunits.convert(self.conc_mass_in[time, 'tds'], to_units=(pyunits.mg / pyunits.liter))  # convert from kg/m3 to mg/L

        # self.water_recovery.unfix()
        self.water_recovery_bound1 = Constraint(
                expr=self.water_recovery[time] >= 0.5
                )

        self.water_recovery_bound2 = Constraint(
                expr=self.water_recovery[time] <= 0.98
                )

        self.chem_dict = {}

        self.costing.fixed_cap_inv_unadjusted = Expression(
                expr=15.1 + (tds_in * 3.02E-4) - (self.water_recovery[time] * 18.8) + (flow_in * 8.08E-2),
                doc='Unadjusted fixed capital investment')  # $M

        ## electricity consumption ##
        self.electricity = 9.73 + tds_in * 1.1E-4 + self.water_recovery[time] * 10.4 + flow_in * 3.83E-5  # kwh/m3

        financials.get_complete_costing(self.costing)