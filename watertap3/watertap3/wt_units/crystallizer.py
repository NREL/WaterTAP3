from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE
## CAPITAL AND ELECTRICITY:
# Survey of High-Recovery and Zero Liquid Discharge Technologies for Water Utilities (2008).
# WateReuse Foundation
# https://www.waterboards.ca.gov/water_issues/programs/grants_loans/water_recycling/research/02_006a_01.pdf
# Regressions for capital and electricity developed from
# data in Table A2.1, Table A2.3
# Capital = f(TDS, recovery, flow)
# Electricity = f(TDS, recovery, flow)

module_name = 'crystallizer'
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

        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.m ** 3 / pyunits.hr)
        tds_in = pyunits.convert(self.conc_mass_in[time, 'tds'], to_units=(pyunits.mg / pyunits.liter))  # convert from kg/m3 to mg/L
        water_recovery = self.water_recovery[time]

        self.chem_dict = {}

        self.costing.fixed_cap_inv_unadjusted = Expression(
            expr=1.41 - tds_in * 7.11E-7 + water_recovery * 1.45 + flow_in * 5.55E-1,
            doc='Unadjusted fixed capital investment')  # $M

        ## electricity consumption ##
        self.electricity = 56.7 + tds_in * 1.83E-5 - water_recovery * 9.47 - flow_in * 8.63E-4  # kwh/m3

        financials.get_complete_costing(self.costing)