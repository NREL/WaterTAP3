from multiprocessing.sharedctypes import Value
import pandas as pd
from pyomo.environ import *
from pyomo.environ import units as pyunits
# from pyomo.repn.plugins.baron_writer import NonNegativeReals

from watertap3.utils import financials
from watertap3.wt_units.wt_unit import WT3UnitProcess
import idaes.core.util.scaling as iscale

## REFERENCE: ADD REFERENCE HERE

module_name = 'ion_exchange'
basis_year = 2016 # 2016 is costing year for EPA component costing data
tpec_or_tic = 'TIC'


class UnitProcess(WT3UnitProcess):



    def fixed_cap(self, unit_params):
        '''
        Docstrings go here.
        
        :return:
        '''

        self.total_ix_cap = Var(initialize=25,
                                # domain=NonNegativeReals,
                                doc='Total ion exchange FCI [$MM]')

        self.cap_per_column = Var(initialize=1,
                                #   domain=NonNegativeReals,
                                  doc='Capital per column [$MM]')

        self.column_total_cap = Var(initialize=1,
                                    # domain=NonNegativeReals,
                                    doc='Total column capital [$MM]')

        self.resin_unit_cap = Var(initialize=4000,
                                #   domain=NonNegativeReals,
                                  doc='Resin cap per m3 [$/m3]')

        self.resin_cap = Var(initialize=1E4,
                            #  domain=NonNegativeReals,
                             doc='Resin capital [$MM]')

        self.regen_pump_cap = Var(initialize=100,
                                  domain=NonNegativeReals,
                                  doc='Pump capital for regen cycle [$MM]')

        self.bw_pump_cap = Var(initialize=100,
                            #    domain=NonNegativeReals,
                               doc='Pump capital for backwash cycle [$MM]')

        self.rinse_pump_cap = Var(initialize=100,
                                #   domain=NonNegativeReals,
                                  doc='Pump capital for rinse cycle [$MM]')

        self.boost_pump_cap = Var(initialize=100,
                                #   domain=NonNegativeReals,
                                  doc='Pump capital for booster pump [$MM]')
                        
        self.total_pump_cap = Var(initialize=100,
                                #   domain=NonNegativeReals,
                                  doc='Total capital for IX pumps [$MM]')

        if self.pv_material == 'carbon_w_stainless_internals':
            self.cap_per_column_constr = Constraint(expr=self.cap_per_column ==
                                                    (16504 * self.column_vol ** 0.43) * 1E-6)
            # self.cap_per_column = (16504 * self.column_vol ** 0.43) * 1E-6
        if self.pv_material == 'carbon_w_plastic_internals':
            self.cap_per_column_constr = Constraint(expr=self.cap_per_column ==
                                                    (9120 * self.column_vol ** 0.49) * 1E-6)
            # self.cap_per_column = (9120 * self.column_vol ** 0.49) * 1E-6
        if self.pv_material == 'fiberglass':
            self.cap_per_column_constr = Constraint(expr=self.cap_per_column ==
                                                    (5637 * self.column_vol ** 0.9) * 1E-6)
            # self.cap_per_column = (5637 * self.column_vol ** 0.9) * 1E-6

        self.col_total_cap_constr = Constraint(expr=self.column_total_cap == self.cap_per_column * (self.num_columns + 1))
        # self.column_total_cap = self.cap_per_column * (self.num_columns + 1)

        self.resin_unit_cap.fix(self.resin_dict[self.resin_type])
        # self.resin_unit_cap = self.resin_dict[self.resin_type]

        self.resin_cap_constr = Constraint(expr=self.resin_cap == ((self.resin_vol + self.resin_vol_per_col) * self.resin_unit_cap) * 1E-6)  # include an additional resin vol per column to account for the extra column
        # self.resin_cap = ((self.resin_vol + self.resin_vol_per_col) * self.resin_unit_cap) * 1E-6

        self.regen_pump_cap_constr = Constraint(expr=self.regen_pump_cap == (-24.257 * self.regen_flow ** 2 + 2803.7 * self.regen_flow + 7495.7) *
                                                     (self.num_columns + 1) * 1E-6)  # assumes centrifugal pump and 1 pump per column
        # self.regen_pump_cap = (-24.257 * self.regen_flow ** 2 + 2803.7 * self.regen_flow + 7495.7) * (self.num_columns + 1) * 1E-6

        self.bw_pump_cap_constr = Constraint(expr=self.bw_pump_cap == (-24.257 * self.bw_flow ** 2 + 2803.7 * self.bw_flow + 7495.7) *
                                                  (self.num_columns + 1) * 1E-6)  # assumes centrifugal pump and 1 pump per column
        # self.bw_pump_cap = (-24.257 * self.bw_flow ** 2 + 2803.7 * self.bw_flow + 7495.7) * (self.num_columns + 1) * 1E-6

        self.rinse_pump_cap_constr = Constraint(expr=self.rinse_pump_cap == (-24.257 * self.rinse_flow ** 2 + 2803.7 * self.rinse_flow + 7495.7) *
                                                     (self.num_columns + 1) * 1E-6)  # assumes centrifugal pump and 1 pump per column
        # self.rinse_pump_cap = (-24.257 * self.rinse_flow ** 2 + 2803.7 * self.rinse_flow + 7495.7) * (self.num_columns + 1) * 1E-6

        self.flow_per_col_m3_min = pyunits.convert(self.flow_per_column, to_units=pyunits.m ** 3 / pyunits.min)

        self.boost_pump_cap_constr = Constraint(expr=self.boost_pump_cap == (-24.257 * self.flow_per_col_m3_min ** 2 + 2803.7 * self.flow_per_col_m3_min + 7495.7) *
                                                     (self.num_columns + 1) * 1E-6)  # assumes centrifugal pump and 1 pump per column
        # self.boost_pump_cap = (-24.257 * self.flow_per_col_m3_min ** 2 + 2803.7 * self.flow_per_col_m3_min + 7495.7) * (self.num_columns + 1) * 1E-6

        self.total_pump_cap_constr = Constraint(expr=self.total_pump_cap == 
                                                self.regen_pump_cap + self.bw_pump_cap + self.rinse_pump_cap + self.boost_pump_cap)

        # self.total_ix_cap_constr = Constraint(expr=self.total_ix_cap ==
                                                #    self.column_total_cap + self.resin_cap + self.regen_pump_cap + self.bw_pump_cap + self.rinse_pump_cap + self.boost_pump_cap)
                                            
        self.total_ix_cap_constr = Constraint(expr=self.total_ix_cap == 
                                                (self.column_total_cap + self.resin_cap + self.total_pump_cap) * self.tpec_tic)
        return self.total_ix_cap 

    def elect(self):

        '''
        Electricity intensity for ion exchange

        :return:
        '''

        self.main_pump_power = Var(initialize=4E-6,
                                units=pyunits.kW,
                                # domain=NonNegativeReals,
                                doc='Main pump power [kW]')

        self.regen_pump_power = Var(initialize=4E-6,
                                units=pyunits.kW,
                                #  domain=NonNegativeReals,
                                 doc='Regen pump power [kW]')

        self.bw_pump_power = Var(initialize=4E-6,
                                units=pyunits.kW,
                            #   domain=NonNegativeReals,
                              doc='Backwash pump power [kW]')

        self.rinse_pump_power = Var(initialize=4E-6,
                                units=pyunits.kW,
                                #  domain=NonNegativeReals,
                                 doc='Rinse pump power [kW]')

        self.total_pump_power = Var(initialize=4E-5,
                                units=pyunits.kW,
                                #  domain=NonNegativeReals,
                                 doc='Total pump power [kW]')

        self.ix_electricity_intensity = Var(
                                            initialize=4E-5,
                                            units=pyunits.kWh/pyunits.m**3,
                                            # domain=NonNegativeReals,
                                            doc='Total IX electricity intensity [kWh/m3]')

        flow_in_m3_hr = pyunits.convert(self.flow_vol_in[self.t], to_units=pyunits.m ** 3 / pyunits.hr)
        flow_out_m3_hr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.m ** 3 / pyunits.hr)
        flow_waste_m3_hr = pyunits.convert(self.flow_vol_waste[self.t], to_units=pyunits.m ** 3 / pyunits.hr)
        flow_per_column_m3_s = pyunits.convert(self.flow_per_column, to_units=pyunits.m ** 3 / pyunits.second)
        regen_flow_m3_s = pyunits.convert(self.regen_flow / self.num_columns, to_units=pyunits.m ** 3 / pyunits.second)
        bw_flow_m3_s = pyunits.convert(self.bw_flow / self.num_columns, to_units=pyunits.m ** 3 / pyunits.second)
        rinse_flow_m3_s = pyunits.convert(self.rinse_flow / self.num_columns, to_units=pyunits.m ** 3 / pyunits.second)
        self.pump_efficiency = Var(initialize=0.7, units=pyunits.dimensionless, doc='Pump Efficiency [dimensionless]')
        self.g = Param(initialize=9.81, units=pyunits.m / pyunits.second ** 2, doc='Gravity [m/s2]')
        self.rho = Param(initialize=1000, units=pyunits.kg / pyunits.m ** 3, doc='Pure Water Density [kg/m3]')
        self.pressure_drop_m = self.pressure_drop * (0.70325 * (pyunits.m / pyunits.psi)) ## 1 psi of differential pressure = 0.70325 m pump head
        self.pump_efficiency.fix(0.7)

        self.main_pump_power_constr = Constraint(expr=self.main_pump_power == 
                                                pyunits.convert(((self.rho * self.g * self.pressure_drop_m * flow_per_column_m3_s) / 
                                                self.pump_efficiency), to_units=pyunits.kilowatts)) # per column

        self.regen_pump_power_constr = Constraint(expr=self.regen_pump_power == 
                                                pyunits.convert(((self.regen_density * self.g * self.pressure_drop_m * regen_flow_m3_s) / 
                                                self.pump_efficiency), to_units=pyunits.kilowatts)) # per column

        self.bw_pump_power_constr = Constraint(expr=self.bw_pump_power == 
                                                pyunits.convert(((self.rho * self.g * self.pressure_drop_m * bw_flow_m3_s) / 
                                                self.pump_efficiency), to_units=pyunits.kilowatts)) # per column

        self.rinse_pump_power_constr = Constraint(expr=self.rinse_pump_power == 
                                                    pyunits.convert(((self.rho * self.g * self.pressure_drop_m * rinse_flow_m3_s) / 
                                                    self.pump_efficiency), to_units=pyunits.kilowatts)) # per column

        self.total_pump_power_constr = Constraint(expr=self.total_pump_power == 
                                                    (self.main_pump_power + self.regen_pump_power + self.bw_pump_power + self.rinse_pump_power) * (self.num_columns + 1))
        self.ix_electricity_intensity_constr = Constraint(expr=self.ix_electricity_intensity == self.total_pump_power / flow_out_m3_hr)

        return self.ix_electricity_intensity

    def ix_setup(self, unit_params):
        self.ix_regen(unit_params)
        self.ix_backwash()
        self.ix_rinse()
        self.ix_constituents(unit_params)
        self.ix_resin()
        self.ix_column()
        self.ix_constraints()

    def ix_regen(self, unit_params):

        ### REGEN VARIABLES

        self.regen_dose = Var(initialize=300,
                            #   domain=NonNegativeReals,
                              units=pyunits.kg / pyunits.m ** 3,
                              bounds=(80, 500),
                              doc='NaCl dose required for regeneration [kg/m3]')

        self.regen_rate = Var(initialize=4,
                            #   domain=NonNegativeReals,
                              bounds=(2, 5),
                              doc='Regeneration rate [BV/hr]')

        self.regen_density = Var(initialize=1000,
                                #  domain=NonNegativeReals,
                                 units=pyunits.kg / pyunits.m ** 3,
                                 bounds=(990, 1200),
                                 doc='Density of NaCl regen solution [kg/m3]')

        self.regen_ww = Var(initialize=0.1,
                            # domain=NonNegativeReals,
                            bounds=(0.015, 0.26),
                            doc='Strength of NaCl solution w/w [kg NaCl/kg soln]')

        self.regen_conc = Var(initialize=110,
                            #   domain=NonNegativeReals,
                              units=pyunits.kg / pyunits.m ** 3,
                              doc='Concentration of regen solution [kg/m3]')

        self.regen_vol = Var(initialize=2,
                            #  domain=NonNegativeReals,
                             doc='m3 of regen solution per m3 resin')

        self.regen_soln_per_column = Var(initialize=50,
                                        #  domain=NonNegativeReals,
                                         units=pyunits.m ** 3,
                                         doc='Regen solution used per column [m3/column]')

        self.regen_soln_per_column_annual = Var(initialize=1E3,
                                                # domain=NonNegativeReals,
                                                units=pyunits.m ** 3 / pyunits.year,
                                                doc='Annual regen used per column [m3/year]')

        self.regen_soln_annual = Var(initialize=1E5,
                                    #  domain=NonNegativeReals,
                                     units=pyunits.m ** 3 / pyunits.year,
                                     doc='Total volume regen solution used [m3/year]')

        self.regen_time_per_column = Var(initialize=5,
                                        #  domain=NonNegativeReals,
                                         units=pyunits.min,
                                         doc='Regen time per column [min]')

        self.regen_flow = Var(initialize=10,
                            #   domain=NonNegativeReals,
                              bounds=(0.01, 1E5),
                              units=pyunits.m ** 3 / pyunits.min,
                              doc='Regeneration flow rate [m3/min]')

        self.num_regen_per_column_annual = Var(initialize=200,
                                            #    domain=NonNegativeReals,
                                               doc='Number of regen cycles per year')

        self.salt_per_regen_per_column = Var(initialize=5E3,
                                            #  domain=NonNegativeReals,
                                             doc='Number of regen cycles per year')

        self.salt_per_column_annual = Var(initialize=1E5,
                                        #   domain=NonNegativeReals,
                                          units=pyunits.kg / pyunits.year,
                                          doc='Mass of salt per column per year [kg/yr]')

        self.salt_total_annual = Var(initialize=1E6,
                                    #  domain=NonNegativeReals,
                                     units=pyunits.kg / pyunits.year,
                                     doc='Mass of salt per year [kg/yr]')

        self.salt_dose = Var(initialize=0.1,
                            #  domain=NonNegativeReals,
                             units=pyunits.kg / pyunits.m ** 3,
                             doc='Salt dose for system [kg/m3]')

        self.total_regen_time = Var(initialize=30,
                                    units=pyunits.min,
                                    domain=NonNegativeReals,
                                    doc='Total regeneration cycle time [min]')

        self.regen_dose.fix(300)

        if 'regen_ww' in unit_params.keys():
            self.regen_ww.fix(unit_params['regen_ww'])
        else:
            self.regen_ww.fix(0.1)

    def ix_backwash(self):

        if self.mode == 'sac':
                    ### BACKWASH VARIABLES

            self.bw_rate = Var(initialize=5,
                            # domain=NonNegativeReals,
                            units=pyunits.m / pyunits.hour,
                            bounds=(4.5, 6.5),
                            doc='Backwash rate [m/hr]')

            self.bw_time = Var(initialize=6,
                            # domain=NonNegativeReals,
                            units=pyunits.minute,
                            bounds=(4, 15),
                            doc='Backwash time [min]')

            self.bw_flow = Var(initialize=5,
                            # domain=NonNegativeReals,
                            units=pyunits.m ** 3 / pyunits.minute,
                            doc='Backwash flow rate [m3/min]')

            self.bed_expansion = Var(initialize=0.5,
                                    # domain=NonNegativeReals,
                                    units=pyunits.dimensionless,
                                    bounds=(0.4, 0.6),
                                    doc='Resin bed expansion during backwash [%]')

            self.bed_expansion_h = Var(
                                    # initialize=0.5,
                                    # domain=NonNegativeReals,
                                    units=pyunits.m,
                                    bounds=(0.1, 3),
                                    doc='Resin bed expansion during backwash [m]')

            self.bw_time.fix(6)

        if self.mode == 'sba':

            ### BACKWASH VARIABLES

            self.bw_rate = Var(initialize=6,
                            # domain=NonNegativeReals,
                            units=pyunits.m / pyunits.hour,
                            bounds=(4.5, 8),
                            doc='Backwash rate [m/hr]')

            self.bw_time = Var(initialize=6,
                            # domain=NonNegativeReals,
                            units=pyunits.minute,
                            bounds=(4, 20),
                            doc='Backwash time [min]')

            self.bw_flow = Var(initialize=5,
                            # domain=NonNegativeReals,
                            units=pyunits.m ** 3 / pyunits.minute,
                            doc='Backwash flow rate [m3/min]')

            self.bed_expansion = Var(initialize=0.5,
                                    # domain=NonNegativeReals,
                                    units=pyunits.dimensionless,
                                    bounds=(0.4, 0.8),
                                    doc='Resin bed expansion during backwash [%]')

            self.bed_expansion_h = Var(
                                    # initialize=0.5,
                                    # domain=NonNegativeReals,
                                    units=pyunits.m,
                                    bounds=(0.5, 3),
                                    doc='Resin bed expansion during backwash [m]')

            # self.bw_time.fix(6)
            self.bw_time.fix(12)

    def ix_rinse(self):
        ### RINSE VARIABLES

        if self.mode == 'sac':

            self.rinse_bv = Var(initialize=5,
                                # domain=NonNegativeReals,
                                bounds=(2, 5),
                                doc='Number of bed volumes for rinse step [BV]')
            
            self.rinse_bv.fix(3)


        if self.mode == 'sba':

            self.rinse_bv = Var(initialize=5,
                            # domain=NonNegativeReals,
                            bounds=(2, 10),
                            doc='Number of bed volumes for rinse step [BV]')
                
            self.rinse_bv.fix(5)


        self.rinse_vol_per_column = Var(initialize=150,
                                        bounds=(1, 1E3),
                                        # domain=NonNegativeReals,
                                        units=pyunits.m ** 3,
                                        doc='Rinse volume per column [m3/col]')

        self.rinse_vol_per_column_annual = Var(initialize=5E3,
                                            bounds=(1, 1E6),
                                            # domain=NonNegativeReals,
                                            units=pyunits.m ** 3 / pyunits.year,
                                            doc='Rinse volume per column [m3/yr]')

        self.rinse_time_per_column = Var(initialize=4,
                                        bounds=(1, 1E3),
                                        # domain=NonNegativeReals,
                                        units=pyunits.min,
                                        doc='Rinse time per column [min]')

        self.rinse_flow = Var(initialize=2,
                                # domain=NonNegativeReals,
                                bounds=(0.01, 1E3),
                                units=pyunits.m ** 3 / pyunits.min,
                                doc='Rinse step flow rate [m3/min]')

    def ix_constituents(self, unit_params):

        self.mass_in = Var(self.config.property_package.component_list,
                           initialize=200,
                        #    domain=NonNegativeReals,
                           doc='Influent mass [eq]')

        self.mass_removed = Var(self.config.property_package.component_list,
                                initialize=10,
                                # domain=NonNegativeReals,
                                doc='Mass removed [eq]')

        self.frac_removed = Var(self.config.property_package.component_list,
                                initialize=0.8,
                                bounds=(1E-5, 1),
                                # domain=NonNegativeReals,
                                doc='Fraction removed [%]')

        self.sep_factor = Var(self.config.property_package.component_list,
                                initialize=self.sep_factor_dict,
                                doc='Separation factors [dimensionless]')

        self.meq_conv = Param(self.config.property_package.component_list,
                              initialize=self.meq_conv_dict,
                              doc='Conversions from mg/L to meq/L for constituents')

        self.target_removal = Var(initialize=1,
                                    # bounds=(1E-5, 1),
                                    doc='Removal fraction for target compound [fraction]')


        self.aqueous_conc = Var(self.config.property_package.component_list, 
                                initialize=0.01,
                                # domain=NonNegativeReals,
                                doc='Aqueous ion concentration [eq/L]')

        if 'target_removal' in unit_params.keys():
            self.target_removal.fix(unit_params['target_removal'])
        else:
            self.target_removal.fix(0.99)

    def ix_resin(self):
        ### RESIN AND FLOW VARIABLES
        self.sfr = Var(initialize=30,
                    #    domain=NonNegativeReals,
                       bounds=(6, 50),
                       doc='Service flow rate [BV/hr]')

        self.loading_rate = Var(initialize=20,
                                # domain=NonNegativeReals,
                                bounds=(10, 40),
                                units=pyunits.m / pyunits.hr,
                                doc='Column loading rate (superficial velocity) [m/hr]')

        self.cycle_time = Var(initialize=100,
                              bounds=(10, 1E6),
                            #   domain=NonNegativeReals,
                              units=pyunits.hr,
                              doc='Service cycle time [hr]')

        self.ebct = Var(initialize=1.1,
                        # domain=NonNegativeReals,
                        units=pyunits.min,
                        doc='Empty Bed Contact Time [min]')

        self.denom_resin = Var(initialize=sum(self.ix_df.loc[c].eq_L * self.sep_factor_dict[c] for c in self.cons),
                            #    domain=NonNegativeReals,
                               doc='Denominator for resin-phase conc. calc. [meq/L]')

        self.denom_aq = Var(initialize=1, 
                            # domain=NonNegativeReals
                            )

        self.resin_conc = Var(self.config.property_package.component_list,
                              initialize=0.1,
                            #   domain=NonNegativeReals,
                              doc='Resin phase concentration of each ion [eq/L resin]')
        
        self.max_vol_treated = Var(initialize=5E3,
                                #    domain=NonNegativeReals,
                                   bounds=(100, 1E6),
                                   units=pyunits.L / pyunits.L,
                                   doc='Max volume of water treated before breakthrough [L water/L resin]')
        
        self.resin_vol = Var(initialize=100,
                            # domain=NonNegativeReals,
                            units=pyunits.m ** 3,
                            doc='Total resin volume needed [m3]')
    
        self.resin_mass = Var(initialize=100,
                            # domain=NonNegativeReals,
                            units=pyunits.kg,
                            doc='Resin mass [kg]')

        self.resin_area = Var(initialize=100,
                            #   domain=NonNegativeReals,
                              units=pyunits.m ** 2,
                              doc='Resin cross-sectional area needed [m2]')

        self.resin_depth = Var(initialize=1.5,
                            #    domain=NonNegativeReals,
                               bounds=(0.75, 3),
                               units=pyunits.m,
                               doc='Resin bed depth [m]')

        self.resin_depth_to_column_diam_ratio = Var(initialize=1,
                                                    # domain=NonNegativeReals,
                                                    bounds=(0.6, 1.6),
                                                    units=pyunits.dimensionless,
                                                    doc='Ratio of resin depth to column height')

        self.resin_vol_per_col = Var(initialize=15,
                                    # domain=NonNegativeReals,
                                    units=pyunits.m ** 3,
                                    doc='Resin per column [m3]')

        self.resin_loss_frac_annual = Var(initialize=0.045,
                                        #   domain=NonNegativeReals,
                                          bounds=(0.0375, 0.0525),
                                          doc='Fraction of resin replaced per year [%]')

        self.resin_loss_annual = Var(initialize=20,
                                    #  domain=NonNegativeReals,
                                     units=pyunits.m ** 3,
                                     doc='Resin replaced per year [m3]')
        
        self.void_fraction = Var(initialize=0.37,
                                #  domain=NonNegativeReals,
                                bounds=(0.3, 0.4),
                                units=pyunits.dimensionless,
                                doc='Void fraction [--]')
        
        self.void_volume = Var(initialize=10,
                                #  domain=NonNegativeReals,
                                units=pyunits.m ** 3,
                                doc='Void volume [m3]')
                    
        self.void_vol_per_col = Var(initialize=10,
                                #  domain=NonNegativeReals,
                                units=pyunits.m ** 3,
                                doc='Void volume per column[m3]')

        self.bed_volume = Var(initialize=10,
                            #  domain=NonNegativeReals,
                            units=pyunits.m ** 3,
                            doc='Resin bed volume [m3]')

        # self.sfr.fix(10)
        self.loading_rate.fix(20)
        self.resin_loss_frac_annual.fix(0.045)
        self.void_fraction.fix(0.35)

        if self.mode == 'sac':
            self.resin_capacity = Var(initialize=1.7,
                                    # domain=NonNegativeReals,
                                    bounds=(1.6, 2.2),
                                    doc='SAC Resin capacity [eq/L]')

            self.resin_density = Var(initialize=800,
                                    # domain=NonNegativeReals,
                                    bounds=(625, 975),
                                    units=pyunits.kg / pyunits.m ** 3,
                                    doc='SAC Resin density [kg/m3]')

            self.resin_capacity.fix(1.7)
            self.resin_density.fix(800)
        
        if self.mode == 'sba':

            self.resin_capacity = Var(initialize=1.2,
                                    # domain=NonNegativeReals,
                                    bounds=(0.9, 1.5),
                                    doc='SBA Resin capacity [eq/L]')

            self.resin_density = Var(initialize=700,
                                    # domain=NonNegativeReals,
                                    bounds=(675, 725),
                                    units=pyunits.kg / pyunits.m ** 3,
                                    doc='SBA Resin density [kg/m3]')
            
            self.resin_capacity.fix(1.2)
            self.resin_density.fix(700)
        
        if self.mode == 'wac':

            self.resin_capacity = Var(initialize=3.5,
                                    # domain=NonNegativeReals,
                                    bounds=(0, 4.3),
                                    doc='WAC Resin capacity [eq/L]')

            self.resin_density = Var(initialize=725,
                                    # domain=NonNegativeReals,
                                    bounds=(650, 825),
                                    units=pyunits.kg / pyunits.m ** 3,
                                    doc='WAC Resin density [kg/m3]')
            
            self.resin_capacity.fix(3.5)
            self.resin_density.fix(725)

        if self.mode == 'wba':

            self.resin_capacity = Var(initialize=1.5,
                                    # domain=NonNegativeReals,
                                    bounds=(0.9, 2),
                                    doc='WBA Resin capacity [eq/L]')

            self.resin_density = Var(initialize=675,
                                    # domain=NonNegativeReals,
                                    bounds=(250, 725),
                                    units=pyunits.kg / pyunits.m ** 3,
                                    doc='WBA Resin density [kg/m3]')
            
            self.resin_capacity.fix(1.5)
            self.resin_density.fix(675)
        
    def ix_column(self):
       #### COLUMN VARIABLES

        self.column_h = Var(initialize=2,
                            # domain=NonNegativeReals,
                            units=pyunits.m,
                            bounds=(1, 16),
                            doc='Column height [m]')

        self.column_diam = Var(initialize=2,
                            #    domain=NonNegativeReals,
                               units=pyunits.m,
                               bounds=(0.5, 4),
                               doc='Column diameter [m]')

        self.column_area = Var(initialize=15,
                            #    domain=NonNegativeReals,
                               units=pyunits.m ** 2,
                               doc='Column cross-sectional area [m2]')

        if self.pv_material == 'fiberglass':
            self.column_vol = Var(initialize=2,
                                #   domain=NonNegativeReals,
                                  bounds=(0.5, 4),
                                  units=pyunits.m ** 3,
                                  doc='Column volume [m3]')

        else:
            self.column_vol = Var(initialize=35,
                                #   domain=NonNegativeReals,
                                  bounds=(0.5, 75),
                                  units=pyunits.m ** 3,
                                  doc='Column volume [m3]')

        self.num_columns = Var(initialize=2,
                            #    domain=PositiveIntegers,
                               bounds=(1, 50),
                               units=pyunits.dimensionless,
                               doc='Number of columns in parallel')

        self.underdrain_h = Var(initialize=0.5,
                                # domain=NonNegativeReals,
                                units=pyunits.m,
                                doc='Underdrain height [m]')

        self.distributor_h = Var(initialize=1,
                                #  domain=NonNegativeReals,
                                 units=pyunits.m,
                                 doc='Distributor height [m]')

        self.flow_per_column = Var(initialize=250,
                                #    domain=NonNegativeReals,
                                #    bounds=(1, 1E5),
                                   units=pyunits.m ** 3 / pyunits.hr,
                                   doc='Flow per column [m3/hr]')

        self.pressure_drop = Var(initialize=14,
                                #  domain=NonNegativeReals,
                                 units=pyunits.psi,
                                 bounds=(0, 25),
                                 doc='Pressure drop across column [psi]')


        self.underdrain_h.fix(0.5)
        self.distributor_h.fix(1)
        # self.column_diam.fix(2.5)

    def ix_constraints(self): 

        flow_out_m3_hr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.m ** 3 / pyunits.hr)
        flow_out_m3_yr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.m ** 3 / pyunits.year)
        flow_out_L_hr = pyunits.convert(self.flow_vol_out[self.t], to_units=pyunits.L / pyunits.hr)

        ############################# CONSTRAINTS START
        #### RESIN AND PERFORMANCE CONSTRAINTS
        
        self.aqueous_conc_tot = sum(self.ix_df.loc[c].eq_L for c in self.cons)
        self.resin_conc_constr = ConstraintList()
        self.aqueous_conc_constr = ConstraintList()
        self.mass_in_constr = ConstraintList()
        self.mass_removed_constr = ConstraintList()
        self.frac_removed_constr = ConstraintList()

        for c in self.config.property_package.component_list:
            
            if c in self.cons:
                self.sep_factor[c].fix(self.sep_factor_dict[c])
                self.resin_conc_constr.add(self.resin_conc[c] == 
                                            (self.resin_capacity * self.sep_factor[c] * self.ix_df.loc[c].eq_L) / self.denom_resin())
                self.mass_in_constr.add(self.mass_in[c] == self.ix_df.loc[c].eq_L * flow_out_L_hr * self.cycle_time)
                self.mass_removed_constr.add(self.mass_removed[c] == 
                                            (self.resin_conc[c] / self.max_vol_treated) * flow_out_L_hr * self.cycle_time)
                self.frac_removed_constr.add(self.frac_removed[c] == 
                                            self.mass_removed[c] / self.mass_in[c])
                self.aqueous_conc_constr.add(self.aqueous_conc[c] == 
                                            (self.aqueous_conc_tot * self.resin_conc[c]) / (self.sep_factor[c] * self.denom_aq))
            else:
                self.sep_factor[c].fix(0)
                self.resin_conc[c].fix(1E-8)
                self.mass_in[c].fix(1E-8)
                self.mass_removed[c].fix(1E-8)
                self.frac_removed[c].fix(1E-5)
                self.aqueous_conc[c].fix(1E-8)
        
        self.denom_resin_constr = Constraint(expr=self.denom_resin == 
                                            sum(self.ix_df.loc[c].eq_L * self.sep_factor[c] for c in self.cons))

        self.denom_aq_constr = Constraint(expr=self.denom_aq == 
                                          sum(self.resin_conc[c] / self.sep_factor[c] for c in self.cons))

        self.max_vol_treated_constr = Constraint(expr=self.max_vol_treated == 
                                                (self.resin_conc[self.target]) / (self.ix_df.loc[self.target].eq_L))

        self.resin_vol_constr = Constraint(expr=self.resin_vol == flow_out_m3_hr / self.sfr)
        self.resin_vol_L = pyunits.convert(self.resin_vol, to_units=pyunits.L)
        self.resin_total_cap = self.resin_capacity * self.resin_vol_L
        self.resin_vol_per_col_constr = Constraint(expr=self.resin_vol_per_col == self.resin_vol / self.num_columns)

        self.resin_mass_constr = Constraint(expr=self.resin_mass == self.resin_vol * self.resin_density)

        self.void_vol_constr = Constraint(expr=self.void_volume == self.resin_vol * self.void_fraction)
        self.void_vol_per_col_constr = Constraint(expr=self.void_vol_per_col == self.void_volume / self.num_columns)

        self.bed_vol_constr = Constraint(expr=self.bed_volume == self.flow_per_column / self.resin_vol_per_col)

        self.resin_depth_to_column_diam_ratio_constr = Constraint(expr=self.resin_depth_to_column_diam_ratio == 
                                                                    self.resin_depth / self.column_diam)

        self.resin_loss_annual_constr = Constraint(expr=self.resin_loss_annual == 
                                                    self.resin_vol * self.resin_loss_frac_annual)

        self.cycle_time_constr = Constraint(expr=self.cycle_time == 
                                            (self.max_vol_treated * self.resin_vol_L) / flow_out_L_hr)

        self.resin_area_constr = Constraint(expr=self.resin_area == self.resin_vol / self.resin_depth)

        self.column_area_constr = Constraint(expr=self.column_area == 3.141592 * (self.column_diam / 2) ** 2)

        self.num_columns_constr = Constraint(expr=self.num_columns == self.resin_area / self.column_area)

        self.flow_per_col_constr = Constraint(expr=self.flow_per_column == flow_out_m3_hr / self.num_columns)

        self.loading_rate_constr1 = Constraint(expr=self.loading_rate == self.flow_per_column / self.column_area)
        self.loading_rate_constr2 = Constraint(expr=self.loading_rate == self.sfr * self.resin_depth)

        self.pressure_drop_constr = Constraint(expr=self.pressure_drop == 
                                                (8.28E-04 * self.loading_rate ** 2 + 0.173 * self.loading_rate + 0.609) * self.resin_depth)  # Curve for 20C temperature

        self.column_h_constr = Constraint(expr=self.column_h == 
                                          self.resin_depth + self.bed_expansion_h + self.distributor_h + self.underdrain_h)

        self.column_vol_constr = Constraint(expr=self.column_vol == 3.14159 * (self.column_diam / 2) ** 2 * self.column_h)

        self.ebct_constr = Constraint(expr=self.ebct == 
                                     (self.resin_depth / self.loading_rate) * 60)

        #### REGEN CONSTRAINTS

        self.regen_density_constr = Constraint(expr=self.regen_density == 
                                                994.34 + 761.65 * self.regen_ww)  # kg Nacl / m3 resin

        self.regen_conc_constr = Constraint(expr=self.regen_conc == self.regen_ww * self.regen_density)

        self.regen_vol_constr = Constraint(expr=self.regen_vol == self.regen_dose / self.regen_conc)  # m3 regen soln / m3 resin

        self.num_regen_per_column_annual_constr = Constraint(expr=self.num_regen_per_column_annual == 8760 / self.cycle_time)  # numerator is hours per year

        self.salt_per_regen_per_column_constr = Constraint(expr=self.salt_per_regen_per_column == self.resin_vol_per_col * self.regen_dose)

        self.salt_per_col_annual_constr = Constraint(expr=self.salt_per_column_annual == 
                                                            self.num_regen_per_column_annual * self.salt_per_regen_per_column)  # kg / year per column

        self.salt_total_annual_constr = Constraint(expr=self.salt_total_annual == 
                                                            self.salt_per_column_annual * self.num_columns)  # kg / year

        self.salt_dose_constr = Constraint(expr=self.salt_dose == self.salt_total_annual / flow_out_m3_yr)

        self.regen_soln_per_col_constr = Constraint(expr=self.regen_soln_per_column == self.resin_vol_per_col * self.regen_vol)

        self.regen_soln_per_col_annual_constr = Constraint(expr=self.regen_soln_per_column_annual == 
                                                            self.regen_soln_per_column * self.num_regen_per_column_annual)

        self.regen_soln_annual_constr = Constraint(expr=self.regen_soln_annual == 
                                                            self.regen_soln_per_column_annual * self.num_columns)

        self.regen_time_per_col_constr = Constraint(expr=self.regen_time_per_column == self.ebct * self.regen_vol)

        self.total_regen_time_constr = Constraint(expr=self.total_regen_time == 
                                                            self.regen_time_per_column + self.rinse_time_per_column + self.bw_time)

        self.regen_flow_constr = Constraint(expr=self.regen_flow == self.column_vol / self.regen_time_per_column)

        ##### BW CONSTRAINTS

        self.bed_exp_constr = Constraint(expr=self.bed_expansion == 
                                        -1.35E-3 * self.bw_rate ** 2 + 1.02E-1 * self.bw_rate - 1.23E-2)

        self.bed_exp_h_constr = Constraint(expr=self.bed_expansion_h == self.resin_depth * self.bed_expansion)

        self.bw_flow_constr = Constraint(expr=self.bw_flow == self.column_vol / self.bw_time)

        ##### RINSE CONSTRAINTS

        self.rinse_vol_per_column_constr = Constraint(expr=self.rinse_vol_per_column == self.resin_vol_per_col * self.rinse_bv)

        self.rinse_vol_per_col_annual_constr = Constraint(expr=self.rinse_vol_per_column_annual == 
                                                                self.rinse_vol_per_column * self.num_regen_per_column_annual)

        self.rinse_time_per_col_constr = Constraint(expr=self.rinse_time_per_column == self.ebct * self.rinse_bv)

        self.rinse_flow_constr = Constraint(expr=self.rinse_flow == self.column_vol / self.rinse_time_per_column)

        ##### WATER RECOVERY, CHEM DICT, AND CONSTITUENT REMOVAL

        self.wr_constr = Constraint(expr=self.water_recovery[self.t] == 
                                    1 - (self.total_regen_time / ((self.cycle_time * 60) + self.total_regen_time)))

        self.chem_dict = {
                'Sodium_Chloride': self.salt_dose
                }

        self.del_component(self.component_removal_equation)

        self.ix_component_removal = ConstraintList()
        for c in self.config.property_package.component_list:
            self.ix_component_removal.add(self.frac_removed[c] * self.flow_vol_in[self.t] * self.conc_mass_in[self.t, c] == 
                                            self.flow_vol_waste[self.t] * self.conc_mass_waste[self.t, c])


    def get_costing(self, unit_params=None, year=None):
        '''
        Initialize the unit in WaterTAP3.
        '''
        financials.create_costing_block(self, basis_year, tpec_or_tic)
        time = self.flowsheet().config.time
        self.t = time.first()
        self.units_meta = self.config.property_package.get_metadata().get_derived_units

        try:
            self.mode = unit_params['mode']
            if self.mode not in ['sba', 'sac']:
                self.mode = 'sac' # default to cation exchange
        except (KeyError, ValueError) as e:
            self.mode = 'sac'

        self.source_df = self.parent_block().source_df[['value']]
        self.source_df['mg_L'] = self.source_df['value'] * 1000
        self.parent_block().has_ix = True
        try:
            self.pv_material = unit_params['pv_material']
        except KeyError:
            self.pv_material = 'carbon_w_plastic_internals'

        if self.mode == 'sac':
            self.resin_dict = {
                    'polystyrenic_macro': 3680,
                    'polystyrenic_gel': 6240,
                    } # cost of resin per m3, adapted to $/m3 from EPA models
            self.ix_df = pd.read_csv('data/ix_sac.csv', index_col='constituent')
            self.presaturant_ion = 'sodium'
            try:
                self.resin_type = unit_params['resin_type']
                if self.resin_type not in self.resin_dict.keys():
                    self.resin_type = 'polystyrenic_macro'
            except (KeyError, ValueError) as e:
                self.resin_type = 'polystyrenic_macro'

        if self.mode == 'sba':
            self.resin_dict = {
                    'styrenic_gel_1': 5214,
                    'styrenic_gel_2': 6116,
                    'styrenic_macro_1': 7298,
                    'styrenic_macro_2': 7810,
                    'polyacrylic': 8658,
                    'nitrate': 6116
                    } # cost of resin per m3, adapted to $/m3 from EPA models
            self.ix_df = pd.read_csv('data/ix_sba.csv', index_col='constituent')
            self.presaturant_ion = 'chloride'
            try:
                self.resin_type = unit_params['resin_type']
                if self.resin_type not in self.resin_dict.keys():
                    self.resin_type = 'styrenic_gel_1'
            except (KeyError, ValueError) as e:
                self.resin_type = 'styrenic_gel_1'

        self.cons = [c for c in self.config.property_package.component_list if c in self.ix_df.index]
        self.ix_df = self.ix_df.loc[self.cons].copy()
        self.ix_df['mg_L'] = self.source_df.loc[self.cons].value * 1000
        self.ix_df['eq_L'] = self.ix_df.mg_L / self.ix_df.meq * 1E-3
        self.ix_df['meq_L'] = self.ix_df.mg_L / self.ix_df.meq
        self.ix_df['sep_factor_eq_L'] = self.ix_df.sep_factor * self.ix_df.eq_L
        self.target = self.ix_df.sep_factor.idxmax()
        self.sep_factor_dict = self.ix_df.to_dict()['sep_factor']
        self.meq_conv_dict = self.ix_df.to_dict()['meq']
        self.cons_df = self.source_df.loc[[c for c in self.cons if c != self.presaturant_ion]].copy()
        self.cons_df['meq_L'] = [(self.cons_df.loc[c].value * 1E3) / 
                                    self.meq_conv_dict[c] for c in self.cons if c != self.presaturant_ion]
        self.ix_setup(unit_params)
        self.costing.fixed_cap_inv_unadjusted = Expression(expr=self.fixed_cap(unit_params),
                                                           doc='Unadjusted fixed capital investment')
        self.electricity = Expression(expr=self.elect(),
                                      doc='Electricity intensity [kwh/m3]')

        self.costing.other_var_cost = (self.resin_unit_cap * self.resin_loss_annual) * 1E-6
        financials.get_complete_costing(self.costing)

    def ix_print(self):
        print(f'**********IX RESULTS**********\n\n')

        print(f'COLUMN GEOMETRY:')
        print(f'\tNumber Columns [-] = {self.num_columns()} \t{self.num_columns.bounds}')
        print(f'\tFlow Per Column [m3/hr] = {round(self.flow_per_column(), 2)} \t{self.flow_per_column.bounds}')
        print(f'\tColumn Height [m] = {round(self.column_h(), 2)} \t{self.column_h.bounds}')
        print(f'\tColumn Diam. [m] = {round(self.column_diam(), 2)} \t{self.column_diam.bounds}')
        print(f'\tColumn Vol. [m3] = {round(self.column_vol(), 2)} \t{self.column_vol.bounds}')

        print(f'\nDESIGN PARAMETERS:')
        print(f'\tService Flow Rate [BV/hr] = {round(self.sfr(), 2)} \t{self.sfr.bounds}')
        print(f'\tLoading Rate [m/hr] = {round(self.loading_rate(), 2)} \t{self.loading_rate.bounds}')
        print(f'\tCycle Time [hr] = {round(self.cycle_time(), 2)} \t{self.cycle_time.bounds}')
        print(f'\tEBCT [min] = {round(self.ebct(), 2)} \t{self.ebct.bounds}')
        print(f'\tMax Vol. Treated [L water/L resin] = {round(self.max_vol_treated(), 2)} \t{self.max_vol_treated.bounds}')
        print(f'\tPressure Drop [psi] = {round(self.pressure_drop(), 2)} \t{self.pressure_drop.bounds}')

        print(f'\nRESIN:')
        print(f'\tResin Capacity [eq/L] = {round(self.resin_capacity(), 2)} \t{self.resin_capacity.bounds}')
        print(f'\tTotal Resin Vol. [m3] = {round(self.resin_vol(), 2)} \t{self.resin_vol.bounds}')
        print(f'\tResin Vol. Per Col. [m3/column] = {round(self.resin_vol_per_col(), 2)} \t{self.resin_vol_per_col.bounds}')
        print(f'\tResin Depth [m] = {round(self.resin_depth(), 2)} \t{self.resin_depth.bounds}')
        print(f'\tResin Depth to Col. Diam. Ratio [m/m] = {round(self.resin_depth_to_column_diam_ratio(), 2)} \t{self.resin_depth_to_column_diam_ratio.bounds}')

        print(f'\nCONSTITUENTS:')
        print(f'\tTarget Contaminant = {self.target.title()}')
        print('\tContaminants:')
        print('\t(IN, OUT, FRAC REMOVED) [eq]:')
        for c in self.cons:
            print(f'\t\t{c.title()}, {round(self.mass_in[c](), 2)}, {round(self.mass_removed[c](), 2)}, {round(self.frac_removed[c](), 2) * 100}%')
        print('All Constituents [mg/L]:')
        for c in self.config.property_package.component_list:
            c_in = round(pyunits.convert(self.conc_mass_in[self.t, c], to_units=pyunits.mg / pyunits.L)(), 4)
            c_out = round(pyunits.convert(self.conc_mass_out[self.t, c], to_units=pyunits.mg / pyunits.L)(), 4)
            c_waste = round(pyunits.convert(self.conc_mass_waste[self.t, c], to_units=pyunits.mg / pyunits.L)(), 4)
            print(f'\t\t{c.title()}, In: {c_in}, Out: {c_out}, Waste: {c_waste}')
        
        print(f'\nREGEN:')
        print(f'\tTotal Regen Time [min] = {round(self.total_regen_time(), 2)} \t{self.total_regen_time.bounds}')
        print(f'\tTotal Annual Regen Soln. Vol. [m3/yr] = {round(self.regen_soln_annual(), 2)} \t{self.regen_soln_annual.bounds}')
        print(f'\tTotal Annual Mass Salt [kg/yr] = {round(self.salt_total_annual(), 2)} \t{self.salt_total_annual.bounds}')
        print(f'\tRegen Soln. Required [m3 soln/m3 resin] = {round(self.regen_vol(), 2)} \t{self.regen_vol.bounds}')
        print(f'\tRegen Flow [m3/min] = {round(self.regen_flow(), 2)} \t{self.regen_flow.bounds}')
        print(f'\tRegen Rate [BV/hr] = {round(self.regen_rate(), 2)} \t{self.regen_rate.bounds}')
        print(f'\tRegen Time Per Col. [min/col] = {round(self.regen_time_per_column(), 2)} \t{self.regen_time_per_column.bounds}')
        print(f'\tRegen Soln. Per Col. [m3/col] = {round(self.regen_soln_per_column(), 2)} \t{self.regen_soln_per_column.bounds}')
        print(f'\tRegen Salt Dose [kg/m3] = {round(self.salt_dose(), 2)} \t{self.salt_dose.bounds}')
        print(f'\tRegen NaCl Soln. Density [kg/m3] = {round(self.regen_density(), 2)} \t{self.regen_density.bounds}')
        print(f'\tRegen NaCl Soln. w/w [kg NaCl/kg soln] = {round(self.regen_ww(), 2)} \t{self.regen_ww.bounds}')
        print(f'\tRegen Soln. Conc. [kg/m3] = {round(self.regen_conc(), 2)} \t{self.regen_conc.bounds}')

        print(f'\nBACKWASH:')
        print(f'\tTotal BW Time [min] = {round(self.bw_time(), 2)} \t{self.bw_time.bounds}')
        print(f'\tBW Flow [m3/min] = {round(self.bw_flow(), 2)} \t{self.bw_flow.bounds}')
        print(f'\tBW Rate [m/hr] = {round(self.bw_rate(), 2)} \t{self.bw_rate.bounds}')
        print(f'\tBed Expansion [%] = {round(self.bed_expansion(), 2) * 100}% \t{self.bed_expansion.bounds}')
        print(f'\tBed Expansion [m] = {round(self.bed_expansion_h(), 2)} \t{self.bed_expansion_h.bounds}')

        print(f'\nRINSE:')
        print(f'\tTotal Rinse Time [min] = {round(self.rinse_time_per_column(), 2)} \t{self.rinse_time_per_column.bounds}')
        print(f'\tRinse Flow [m3/min] = {round(self.rinse_flow(), 2)} \t{self.rinse_flow.bounds}')
        print(f'\tNum. BV per Rinse [m/hr] = {round(self.rinse_bv(), 2)} \t{self.rinse_bv.bounds}')
        print(f'\tAnnual Rinse Vol. [m3/yr] = {round(self.rinse_vol_per_column_annual(), 2) * self.num_columns()} \t{self.rinse_vol_per_column_annual.bounds}')

        print(f'\nCOSTING:')
        print(f'\tTotal Capital [$M] = ${round(self.total_ix_cap() / self.tpec_tic, 5)}')
        print(f'\t\tColumn Capital [$M] = ${round(self.column_total_cap(), 5)}')
        print(f'\t\tResin Capital [$M] = ${round(self.resin_cap(), 5)}')
        print(f'\t\tPump Capital [$M] = ${round(self.total_pump_cap(), 5)}')
        print(f'\t\tCapital Per Column [$M] = ${round(self.cap_per_column(), 5)}')

        print(f'\nPOWER:')
        print(f'\tTotal IX Electricity Intensity [kWh/m3] = {round(self.ix_electricity_intensity(), 7)} kWh/m3')
        print(f'\tTotal Pump Power [kW] = {round(self.total_pump_power(), 3)} kW')
        print(f'\tBooster Pump Power [kW] = {round(self.main_pump_power(), 3)} kW')
        print(f'\tRegen Pump Power [kW] = {round(self.regen_pump_power(), 3)} kW')
        print(f'\tBackwash Pump Power [kW] = {round(self.bw_pump_power(), 3)} kW')
        print(f'\tRinse Pump Power [kW] = {round(self.rinse_pump_power(), 3)} kW')
        