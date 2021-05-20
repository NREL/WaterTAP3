from pyomo.environ import Block, Expression, NonNegativeReals, Var, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'evaporation_pond'
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

        t = self.flowsheet().config.time.first()
        time = self.flowsheet().config.time

        self.chem_dict = {}
        tds_in = pyunits.convert(self.conc_mass_in[t, 'tds'], to_units=(pyunits.mg / pyunits.L))  # convert from kg/m3 to mg/L
        approach = unit_params['approach']

        self.air_temp = Var(time, initialize=20, domain=NonNegativeReals, bounds=(0, 45), doc='air temp degrees C')

        try:
            evap_method = unit_params['evap_method']
        except:
            evap_method = False
        try:
            self.humidity = unit_params['humidity']  # ratio, e.g. 50% humidity = 0.5
            self.wind_speed = unit_params['wind_speed']  # m / s
        except:
            self.humidity = 0.5  # ratio, e.g. 50% humidity = 0.5
            self.wind_speed = 5  # m / s

        if bool(evap_method):
            evap_method = unit_params['evap_method']
            try:
                self.air_temp.fix(unit_params['air_temp'])  # degree C
                self.solar_rad = unit_params['solar_rad']  # mJ / m2
            except:
                self.air_temp.fix(20)
                self.solar_rad = 25  # average for 40deg latitude
            if evap_method == 'turc':
                # Turc (1961) PE in mm for day
                self.evap_rate_pure = (0.313 * self.air_temp[t] * (self.solar_rad + 2.1) / (self.air_temp[t] + 15)) * (pyunits.millimeter / pyunits.day)
                self.evap_rate_pure = pyunits.convert(self.evap_rate_pure, to_units=(pyunits.gallons / pyunits.minute / pyunits.acre))

            if evap_method == 'jensen':
                # Jensen-Haise (1963) PE in mm per day
                self.evap_rate_pure = (0.41 * (0.025 * self.air_temp[t] + 0.078) * self.solar_rad) * (pyunits.millimeter / pyunits.day)
                self.evap_rate_pure = pyunits.convert(self.evap_rate_pure, to_units=(pyunits.gallons / pyunits.minute / pyunits.acre))
        else:
            # defaults to jensen
            self.air_temp.fix(25)
            self.solar_rad = 25  # average for 40deg latitude
            self.evap_rate_pure_mm_d = (0.41 * (0.025 * self.air_temp[t] + 0.078) * self.solar_rad) * (pyunits.millimeter / pyunits.day)
            self.evap_rate_pure = pyunits.convert(self.evap_rate_pure_mm_d, to_units=(pyunits.gallons / pyunits.minute / pyunits.acre))
            self.evap_rate_m_yr = pyunits.convert(self.evap_rate_pure_mm_d, to_units=(pyunits.meter / pyunits.year))
        ## This costing model adapted from
        # Membrane Concentrate Disposal: Practices and Regulation (April 2006) - Bureau Land Management
        try:
            liner_thickness = unit_params['liner_thickness']
            land_cost = unit_params['land_cost']
            land_clearing_cost = unit_params['land_clearing_cost']
            dike_height = unit_params['dike_height']
        except:
            liner_thickness = 50  # mil (equal to 1/1000th of an inch)
            land_cost = 5000  # $ / acre
            land_clearing_cost = 1000  # $ / acre
            dike_height = 8  # ft

        self.cost_per_acre = cost_per_acre = 5406 + 465 * liner_thickness + 1.07 * land_cost + 0.931 * land_clearing_cost + 217.5 * dike_height  # $ / acre

        x0 = self.air_temp[t]
        x1 = tds_in
        x2 = self.humidity
        x3 = self.wind_speed

        # self.ratio = -0.0465233559 * (x0) - 0.0011189096 * (x1) - 0.7088094852 * (x2) - 0.0257883428 * (x3) + 0.0017209498 * (x0 ** 2) + 7.54344e-05 * (x0 * x1) + 0.0923261483 * (
        #         x0 * x2) - 0.0002522583 * (
        #                      x0 * x3) + 7.74e-07 * (x1 ** 2) + 0.0012751516 * (x1 * x2) + 1.16276e-05 * (x1 * x3) - 0.042838386 * (x2 ** 2) + 0.0842127857 * (x2 * x3) + 0.0006828725 * (
        #                      x3 ** 2) - 2.55508e-05 * (
        #                      x0 ** 3) - 1.6415e-06 * (x0 ** 2 * x1) - 0.001500322 * (x0 ** 2 * x2) + 4.46853e-05 * (x0 ** 2 * x3) + 2.8e-08 * (x0 * x1 ** 2) - 8.93471e-05 * (
        #                      x0 * x1 * x2) - 2.6285e-06 * (
        #                      x0 * x1 * x3) - 0.0472354101 * (x0 * x2 ** 2) + 0.000814877 * (x0 * x2 * x3) - 0.0001268287 * (x0 * x3 ** 2) - 2.4e-09 * (x1 ** 3) + 1.9905e-06 * (
        #                      x1 ** 2 * x2) - 1.214e-07 * (
        #                      x1 ** 2 * x3) - 0.0004983631 * (x1 * x2 ** 2) - 0.0002213007 * (x1 * x2 * x3) + 1.36134e-05 * (x1 * x3 ** 2) + 0.4822279076 * (x2 ** 3) - 0.0473877989 * (
        #                      x2 ** 2 * x3) - 0.0027941016 * (x2 * x3 ** 2) + 9.36662e-05 * (x3 ** 3) + 1.3159327466

        ## CHANGED RATIO FUNCTION TO BE DEGREE=2 5/2/2021 -KAS
        self.ratio = 0.0181657227 * (x0) + 4.38801e-05 * (x1) + 0.2504964875 * (x2) + 0.011328485 * (x3) - 0.0003463853 * (x0 ** 2) - 2.16888e-05 * (x0 * x1) - 0.0181098164 * (
                x0 * x2) + 0.0002098163 * (x0 * x3) + 8.654e-07 * (x1 ** 2) - 0.0004358946 * (x1 * x2) - 8.73918e-05 * (x1 * x3) - 0.0165224935 * (x2 ** 2) - 0.0174278724 * (
                             x2 * x3) + 0.0003850584 * (x3 ** 2) + 0.7943236298

        self.evap_rate = self.evap_rate_pure * 0.7  # ratio factor from the BLM document

        flow_in = pyunits.convert(self.flow_vol_in[t], to_units=(pyunits.gallons / pyunits.minute))  # volume coming in
        flow_waste = pyunits.convert(self.flow_vol_waste[t], to_units=(pyunits.gallons / pyunits.minute))  # left over volume
        flow_out = pyunits.convert(self.flow_vol_out[t], to_units=(pyunits.gallons / pyunits.minute))  # what gets evaporated

        self.area = area = flow_out / self.evap_rate

        self.total_area = total_area = 1.2 * self.area * (1 + 0.155 * dike_height / (self.area ** 0.5))

        def fixed_cap(flow_in):
            if approach == 'zld':
                return 0.3 * area
            if approach == 'wt3':
                return (cost_per_acre * total_area) * 1E-6
            else:  # this is Lenntech cost curve based on flow for 1 m/y evap rate
                flow_in_m3_d = pyunits.convert(flow_in, to_units=(pyunits.m ** 3 / pyunits.day))
                return 0.03099 * flow_in_m3_d ** 0.7613  # this is Lenntech cost curve based on flow for 1 m/y evap rate

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = 0  # kwh/m3

        financials.get_complete_costing(self.costing)