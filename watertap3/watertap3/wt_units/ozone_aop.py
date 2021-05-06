from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCES
## CAPITAL:
# Regression based on Texas Water Board - IT3PR documentation Table 3.24
# https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf
## ELECTRICITY:
# "A Review of Ozone Systems Costs for Municipal Applications. Report by the Municipal Committee – IOA Pan American Group"
# (2018) B. Mundy et al. https://doi.org/10.1080/01919512.2018.1467187
# From source: "5.0–5.5 kWh/lb might be used to include total energy consumption of ozone generator, ozone destruct, nitrogen feed system, cooling water pumps, and other miscellaneous
# energy uses."

module_name = 'ozone_aop'
basis_year = 2014
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
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.Mgallons / pyunits.day)

        toc_in = pyunits.convert(self.conc_mass_in[time, 'toc'], to_units=(pyunits.mg / pyunits.liter))

        aop = unit_params['aop']
        contact_time = unit_params['contact_time'] * (1 / pyunits.minutes)
        ct = unit_params['ct'] * (pyunits.mg / (pyunits.liter * pyunits.minute))
        mass_transfer = unit_params['mass_transfer'] * pyunits.dimensionless
        ozone_consumption = ((toc_in + ct / contact_time) / mass_transfer)
        ozone_consumption = pyunits.convert(ozone_consumption, to_units=(pyunits.kg / pyunits.m ** 3))
        o3_toc_ratio = 1 + (ct / contact_time / toc_in)

        if aop:
            chemical_dosage = pyunits.convert((0.5 * o3_toc_ratio * toc_in), to_units=(pyunits.kg / pyunits.m ** 3))
            chem_name = unit_params['chemical_name']
            self.chem_dict = {chem_name: chemical_dosage}
            h2o2_base_cap = 1228
            h2o2_cap_exp = 0.2277
        else:
            self.chem_dict = {}

        def solution_vol_flow(flow_in):
            flow_in = pyunits.convert(flow_in, to_units=(pyunits.m ** 3 / pyunits.hour))  # convert from MGD to m3/hr
            chemical_rate = flow_in * chemical_dosage  # kg/hr
            chemical_rate = pyunits.convert(chemical_rate, to_units=(pyunits.lb / pyunits.day))
            return chemical_rate

        def o3_flow(flow_in):
            flow_in = pyunits.convert(flow_in, to_units=(pyunits.m ** 3 / pyunits.hour))  # convert from MGD to m3/hr
            ozone_flow = flow_in * ozone_consumption  # kg/hr
            ozone_flow = pyunits.convert(ozone_flow, to_units=(pyunits.lb / pyunits.hour))
            return ozone_flow  # lb / day

        def fixed_cap(flow_in):
            x0 = pyunits.convert(ozone_consumption, to_units=(pyunits.mg / pyunits.liter))  # mg/L
            x1 = flow_in  # MGD

            ozone_cap = 368.1024498765 * (x0) + 1791.4380214814 * (x1) - 21.1751721133 * (x0 ** 2) + 90.5123958036 * (x0 * x1) - 193.6107786923 * (x1 ** 2) + 0.6038025161 * (
                    x0 ** 3) + 0.0313834266 * (x0 ** 2 * x1) - 2.4261957652 * (x0 * x1 ** 2) + 5.2214653914 * (x1 ** 3) - 1888.3973953339
            if aop:
                h2o2_flow = solution_vol_flow(flow_in)
                h2o2_cap = h2o2_base_cap * h2o2_flow ** h2o2_cap_exp
            else:
                h2o2_cap = 0
            ozone_aop_cap = (ozone_cap + h2o2_cap) * 1E-3
            return ozone_aop_cap

        def electricity(flow_in):

            ozone_flow = o3_flow(flow_in)  # lb/day
            flow_in = pyunits.convert(flow_in, to_units=(pyunits.m ** 3 / pyunits.hour))
            electricity = (5 * ozone_flow) / flow_in
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)