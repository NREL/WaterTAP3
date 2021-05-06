from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'coag_and_floc'
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

        alum_dose = pyunits.convert(unit_params['alum_dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))
        polymer_dose = pyunits.convert(unit_params['polymer_dose'] * (pyunits.mg / pyunits.liter), to_units=(pyunits.kg / pyunits.m ** 3))

        an_polymer = polymer_dose / 2  # MIKE ASSUMPTION NEEDED
        cat_polymer = polymer_dose / 2  # MIKE ASSUMPTION NEEDE
        rapid_mixers = 1 * pyunits.dimensionless
        floc_mixers = 3 * pyunits.dimensionless
        rapid_mix_processes = 1 * pyunits.dimensionless
        floc_processes = 2 * pyunits.dimensionless
        coag_processes = 1 * pyunits.dimensionless
        floc_injection_processes = 1 * pyunits.dimensionless
        rapid_mix_retention_time = 5.5 * pyunits.seconds  # seconds (rapid mix)
        floc_retention_time = 12 * pyunits.minutes  # minutes

        self.chem_dict = {'Aluminum_Al2_SO4_3': alum_dose, 'Anionic_Polymer': an_polymer, 'Cationic_Polymer': cat_polymer}

        def fixed_cap(flow_in):
            flow_in_gpm = pyunits.convert(flow_in, to_units=pyunits.gallons / pyunits.minute)  # m3/hr to GPM
            rapid_mix_basin_volume = pyunits.convert(rapid_mix_retention_time, to_units=pyunits.minutes) * flow_in_gpm  # gallons
            floc_basin_volume = floc_retention_time * flow_in_gpm * 1E-6  # gallons
            alum_flow = alum_dose * flow_in  # kg / hr
            alum_flow = pyunits.convert(alum_flow, to_units=(pyunits.lb / pyunits.hour))  # lb / hr
            poly_flow = polymer_dose * flow_in  # kg / hr
            poly_flow = pyunits.convert(poly_flow, to_units=(pyunits.lb / pyunits.day))  # lb / hr
            rapid_mix_cap = (7.0814 * rapid_mix_basin_volume + 33269) * rapid_mix_processes  # $
            floc_cap = (952902 * floc_basin_volume + 177335) * floc_processes  # $
            coag_inj_cap = (212.32 * alum_flow + 73225) * coag_processes  # $
            floc_inj_cap = (13662 * poly_flow + 20861) * floc_injection_processes  # $
            coag_floc_cap = (rapid_mix_cap + floc_cap + coag_inj_cap + floc_inj_cap) * 1E-6 * tpec_tic
            return coag_floc_cap

        def electricity(flow_in):
            flow_in_gpm = pyunits.convert(flow_in, to_units=pyunits.gallons / pyunits.minute)  # MGD to GPM
            rapid_mix_basin_volume = pyunits.convert(rapid_mix_retention_time, to_units=pyunits.minutes) * flow_in_gpm
            rapid_mix_basin_volume = pyunits.convert(rapid_mix_basin_volume, to_units=pyunits.m ** 3)  # gallons to m3
            rapid_mix_power_consumption = (900 ** 2 * 0.001 * rapid_mix_basin_volume) * pyunits.watts  # W
            rapid_mix_power = rapid_mix_power_consumption * rapid_mixers * 1E-3  # kW
            floc_basin_volume = floc_retention_time * flow_in_gpm
            floc_basin_volume = pyunits.convert(floc_basin_volume, to_units=(pyunits.m ** 3))  # gallons to m3
            floc_power_consumption = (80 ** 2 * 0.001 * floc_basin_volume) * pyunits.watts  # W
            floc_mix_power = floc_power_consumption * floc_mixers * 1E-3  # kW
            total_power = (rapid_mix_power + floc_mix_power) / flow_in

            return total_power  # kWh/m3

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)