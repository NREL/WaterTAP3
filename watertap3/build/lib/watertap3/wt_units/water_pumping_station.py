from pyomo.environ import Block, Expression, units as pyunits
from watertap3.utils import financials
from wt_unit import WT3UnitProcess

## REFERENCE: ADD REFERENCE HERE

module_name = 'water_pumping_station'
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

        time = self.flowsheet().config.time.first()
        flow_in = pyunits.convert(self.flow_vol_in[time], to_units=pyunits.gallon / pyunits.minute)

        pump_type = unit_params['pump_type']
        # tdh = unit_params['tdh'] * pyunits.ft

        if pump_type == 'raw':
            # Costing parameters a, b determined with the following code:
            # Data taken from WT3 excel model
            #
            # from scipy.optimize import curve_fit
            # def power(x, a, b):
            # 	return a * x ** b
            #
            # flow_lst = np.array([10, 19, 53, 79, 105, 132, 159, 185, 200])  # mgd
            # flow_cost = np.array([188032, 303010, 726314, 1050344, 1363933, 1677539, 1991145, 2299522, 2482431])  # $
            # cc, _ = curve_fit(power, flow_lst, flow_cost)
            # a, b = cc[0], cc[1]
            # print(a, b)
            a = 19370.357574406607
            b = 0.9148641590272578

        if pump_type == 'treated':
            # Costing parameters a, b determined with the following code:
            # Data taken from WT3 excel model
            #
            # from scipy.optimize import curve_fit
            # def power(x, a, b):
            # 	return a * x ** b
            #
            # flow_lst = np.array([53, 80, 106, 131, 158, 185, 211, 238, 265, 300])  # mgd
            # flow_cost = np.array([1254215, 1775451, 2271801, 2755748, 3239590, 3711029, 4107735, 4616463, 5025624, 5633425])  # $
            # cc, _ = curve_fit(power, flow_lst, flow_cost)
            # a, b = cc[0], cc[1]
            # print(a, b)
            a = 40073.42661387725
            b = 0.866701037568153

        # Electricity costing parameters c, d determined with the following code:
        # Data taken from WT3 excel model
        # motor_eff = 0.9
        # pump_eff = 0.9
        # tdh_lst = [25, 50, 75, 100, 200, 300, 400, 1000, 2500]  # TDH in ft
        # tdh_elect = [(0.746 * 440.29 * x) / (3960 * motor_eff * pump_eff) for x in tdh_lst]
        # cc, _ = curve_fit(power_curve, tdh_lst, tdh_elect)
        # c, d = cc[0], cc[1]
        # print(c, d)
        c = 0.10239940765681513
        d = 0.9999999999999999

        self.chem_dict = {}

        ##########################################
        ####### UNIT SPECIFIC EQUATIONS AND FUNCTIONS ######
        ##########################################

        def fixed_cap(flow_in):
            flow_in_cap = pyunits.convert(flow_in, to_units=(pyunits.Mgallons / pyunits.day))
            return tpec_tic * a * flow_in_cap ** b * 1E-6

        def electricity(flow_in):  # m3/hr
            flow_in_elect = pyunits.convert(flow_in, to_units=(pyunits.Mgallons / pyunits.day))
            electricity = (c * (flow_in_elect / 440.29) ** d) / flow_in  # kWh / m3
            return electricity

        self.costing.fixed_cap_inv_unadjusted = Expression(expr=fixed_cap(flow_in),
                                                           doc='Unadjusted fixed capital investment')  # $M

        self.electricity = electricity(flow_in)  # kwh/m3

        financials.get_complete_costing(self.costing)