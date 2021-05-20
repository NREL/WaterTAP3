##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
############################# Pyomo components are added with the add_component method# Pyomo
# components are added with the add_component
# method##################################################
"""
Demonstration zeroth-order model for WaterTAP3
"""

from pyomo.environ import NonNegativeReals, PositiveReals  # ariel

# Import Pyomo libraries
from pyomo.network import Port

# from watertap3.wt_units import sw_onshore_intake
# Import WaterTAP# finanacilas module
from . import financials


from watertap3.wt_units import sw_onshore_intake

def build_up(self, unit_name):
    print(f'\nbuild_up() got called!\n unit name = {unit_name}\n\n')
    if unit_name == "nanofiltration_twb":
        import nanofiltration_twb as unit_process_model
    if unit_name == "chlorination":
        import chlorination as unit_process_model
    if unit_name == "media_filtration":
        import media_filtration as unit_process_model
    if unit_name == "coag_and_floc":
        import coag_and_floc as unit_process_model
    if unit_name == "lime_softening":
        import lime_softening as unit_process_model
    if unit_name == "ro_deep":
        import ro_deep as unit_process_model
    if unit_name == "treated_storage":
        import treated_storage as unit_process_model
    if unit_name == "sedimentation":
        import sedimentation as unit_process_model
    if unit_name == "water_pumping_station":
        import water_pumping_station as unit_process_model
    if unit_name == "sulfuric_acid_addition":
        import sulfuric_acid_addition as unit_process_model
    if unit_name == "sodium_bisulfite_addition":
        import sodium_bisulfite_addition as unit_process_model
    if unit_name == "co2_addition":
        import co2_addition as unit_process_model
    if unit_name == "ammonia_addition":
        import ammonia_addition as unit_process_model
    if unit_name == "municipal_drinking":
        import municipal_drinking as unit_process_model

    if unit_name == "sw_onshore_intake":
        import sw_onshore_intake as unit_process_model

    if unit_name == "holding_tank":
        import holding_tank as unit_process_model
    if unit_name == "tri_media_filtration":
        import tri_media_filtration as unit_process_model
    if unit_name == "cartridge_filtration":
        import cartridge_filtration as unit_process_model
    if unit_name == "backwash_solids_handling":
        import backwash_solids_handling as unit_process_model
    if unit_name == "surface_discharge":
        import surface_discharge as unit_process_model
    if unit_name == "landfill":
        import landfill as unit_process_model
    if unit_name == "coagulant_addition":
        import coagulant_addition as unit_process_model
    if unit_name == "ferric_chloride_addition":
        import ferric_chloride_addition as unit_process_model
    if unit_name == "caustic_soda_addition":
        import caustic_soda_addition as unit_process_model
    if unit_name == "static_mixer":
        import static_mixer as unit_process_model
    if unit_name == "ro_deep_scnd_pass":
        import ro_deep_scnd_pass as unit_process_model
    if unit_name == "anti_scalant_addition":
        import anti_scalant_addition as unit_process_model
    if unit_name == 'uv_aop':
        import uv_aop as unit_process_model
    if unit_name == 'well_field':
        import well_field as unit_process_model
    if unit_name == 'iron_and_manganese_removal':
        import iron_and_manganese_removal as unit_process_model
    if unit_name == 'hydrochloric_acid_addition':
        import hydrochloric_acid_addition as unit_process_model
    if unit_name == 'deep_well_injection':
        import deep_well_injection as unit_process_model
    if unit_name == 'chemical_addition':
        import chemical_addition as unit_process_model
    if unit_name == 'anion_exchange':
        import anion_exchange as unit_process_model
    if unit_name == 'cation_exchange':
        import cation_exchange as unit_process_model
    if unit_name == 'electrodialysis_reversal':
        import electrodialysis_reversal as unit_process_model
    if unit_name == 'irwin_brine_management':
        import irwin_brine_management as unit_process_model
    if unit_name == 'fixed_bed_pressure_vessel':
        import fixed_bed_pressure_vessel as unit_process_model
    if unit_name == 'fixed_bed_gravity_basin':
        import fixed_bed_gravity_basin as unit_process_model
    if unit_name == 'fluidized_bed':
        import fluidized_bed as unit_process_model
    if unit_name == 'multi_stage_bubble_aeration':
        import multi_stage_bubble_aeration as unit_process_model
    if unit_name == 'packed_tower_aeration':
        import packed_tower_aeration as unit_process_model
    if unit_name == 'gac_pressure_vessel':
        import gac_pressure_vessel as unit_process_model
    if unit_name == 'gac_gravity':
        import gac_gravity as unit_process_model
    if unit_name == 'ozone_aop':
        import ozone_aop as unit_process_model
    if unit_name == 'microfiltration':
        import microfiltration as unit_process_model
    if unit_name == 'reverse_osmosis':
        import reverse_osmosis as unit_process_model
    if unit_name == 'basic_unit':
        import basic_unit as unit_process_model
    if unit_name == 'cooling_tower':
        import cooling_tower as unit_process_model
    if unit_name == 'evaporation_pond':
        import evaporation_pond as unit_process_model
    if unit_name == 'basic_mass_based':
        import basic_mass_based as unit_process_model
    if unit_name == 'heap_leaching':
        import heap_leaching as unit_process_model
    if unit_name == 'agglom_stacking':
        import agglom_stacking as unit_process_model
    if unit_name == 'solution_distribution_and_recovery_plant':
        import solution_distribution_and_recovery_plant as unit_process_model
    if unit_name == 'lime_addition':
        import lime_addition as unit_process_model
    if unit_name == 'brine_concentrator':
        import brine_concentrator as unit_process_model
    if unit_name == 'crystallizer':
        import crystallizer as unit_process_model
    if unit_name == 'gac':
        import gac as unit_process_model
    if unit_name == 'anion_exchange_epa':
        import anion_exchange_epa as unit_process_model
    if unit_name == "landfill_zld":
        import landfill_zld as unit_process_model

    """
    The build method is the core of the unit model, and contains the rules
    for building the Vars and Constraints that make up the unit model.
    """
    # build always starts by calling super().build()
    # This triggers a lot of boilerplate in the background for you
    # print(unit_process_model)
    super(unit_process_model.UnitProcessData, self).build()

    # Next, get the base units of measurement from the property definition
    units_meta = unit_process_model.UnitProcessData.config.property_package.get_metadata(

            ).get_derived_units

    # Also need to get time domain
    # This will not be used for WaterTAP3, but will be needed to integrate
    # with ProteusLib dynamic models
    time = self.flowsheet().config.time

    # Add variables representing flow at inlet
    # Note that Vars are indexed by time and have units derived from
    # property package
    # Property metadata does not currently support concentration or volumetric
    # flow, but I will fix that.
    # Note that the concentration variable is indexed by components
    # I included temperature and pressure as these would commonly be used
    # in ProteusLib
    if unit_name == "chlorination":
        unit_process_model.get_additional_variables(self, units_meta, time)
    if unit_name == "ro_deep":
        unit_process_model.get_additional_variables(self, units_meta, time)
    if unit_name == "ro_deep_scnd_pass":
        unit_process_model.get_additional_variables(self, units_meta, time)
    # if unit_name == "uv_aop":
    #     unit_process_model.get_additional_variables(self, units_meta, time)

    self.flow_vol_in = Var(time,
                           initialize=1,
                           domain=NonNegativeReals,
                           units=units_meta("volume") / units_meta("time"),
                           bounds=(1e-8, 1e2),
                           doc="Volumetric flowrate of water into unit")
    self.conc_mass_in = Var(time,
                            self.config.property_package.component_list,
                            initialize=1e-5,
                            # domain=NonNegativeReals,
                            units=units_meta("mass") / units_meta("volume"),
                            doc="Mass concentration of species at inlet")
    self.temperature_in = Var(time,
                              initialize=300,
                              units=units_meta("temperature"),
                              doc="Temperature at inlet")
    self.pressure_in = Var(time,
                           initialize=1,
                           domain=NonNegativeReals,
                           units=units_meta("pressure"),
                           doc="Pressure at inlet")

    # Add similar variables for outlet and waste stream
    self.flow_vol_out = Var(time,
                            initialize=1,
                            domain=NonNegativeReals,
                            units=units_meta("volume") / units_meta("time"),
                            doc="Volumetric flowrate of water out of unit")
    self.conc_mass_out = Var(time,
                             self.config.property_package.component_list,
                             initialize=0,
                             # domain=NonNegativeReals,
                             units=units_meta("mass") / units_meta("volume"),
                             doc="Mass concentration of species at outlet")
    self.temperature_out = Var(time,
                               initialize=300,
                               units=units_meta("temperature"),
                               doc="Temperature at outlet")
    self.pressure_out = Var(time,
                            initialize=1,
                            domain=NonNegativeReals,
                            units=units_meta("pressure"),
                            doc="Pressure at outlet")

    self.flow_vol_waste = Var(
            time,
            initialize=1,
            domain=NonNegativeReals,
            units=units_meta("volume") / units_meta("time"),
            doc="Volumetric flowrate of water in waste")
    self.conc_mass_waste = Var(
            time,
            self.config.property_package.component_list,
            # domain=NonNegativeReals,
            initialize=0,
            units=units_meta("mass") / units_meta("volume"),

            doc="Mass concentration of species in waste")
    self.temperature_waste = Var(time,
                                 initialize=300,
                                 domain=NonNegativeReals,
                                 units=units_meta("temperature"),
                                 doc="Temperature of waste")
    self.pressure_waste = Var(time,
                              initialize=1,
                              domain=NonNegativeReals,
                              units=units_meta("pressure"),
                              doc="Pressure of waste")

    # Next, add additional variables for unit performance
    self.deltaP_outlet = Var(time,
                             initialize=1e-6,
                             # domain=NonNegativeReals,
                             units=units_meta("pressure"),
                             doc="Pressure change between inlet and outlet")
    self.deltaP_waste = Var(time,
                            initialize=1e-6,
                            # domain=NonNegativeReals,
                            units=units_meta("pressure"),
                            doc="Pressure change between inlet and waste")

    # Then, recovery and removal variables

    self.water_recovery = Var(time,
                              initialize=0.8,  # TODO: NEEDS TO BE DIFFERENT?
                              domain=NonNegativeReals,
                              units=pyunits.dimensionless,
                              bounds=(1e-8, 1.0000001),
                              doc="Water recovery fraction")
    self.removal_fraction = Var(time,
                                self.config.property_package.component_list,
                                domain=NonNegativeReals,
                                initialize=0.01,  # TODO: NEEDS TO BE DIFFERENT?
                                units=pyunits.dimensionless,
                                doc="Component removal fraction")

    special_list = ["reverse_osmosis"]  # , "anion_exchange_epa"]
    if unit_name not in special_list:

        if unit_name != "ro_deep":

            # print("includes pressure constraint in equations")

            @self.Constraint(time, doc="Outlet pressure equation")
            def outlet_pressure_constraint(b, t):
                return (b.pressure_in[t] + b.deltaP_outlet[t] ==
                        b.pressure_out[t])

            @self.Constraint(time, doc="Waste pressure equation")
            def waste_pressure_constraint(b, t):
                return (b.pressure_in[t] + b.deltaP_waste[t] ==
                        b.pressure_waste[t])

        if unit_name != "anion_exchange_epa":

            @self.Constraint(time, doc="Water recovery equation")
            def recovery_equation(b, t):
                return b.water_recovery[t] * b.flow_vol_in[t] == b.flow_vol_out[t]

        # Next, add constraints linking these
        @self.Constraint(time, doc="Overall flow balance")
        def flow_balance(b, t):
            return b.flow_vol_in[t] == b.flow_vol_out[t] + b.flow_vol_waste[t]

        @self.Constraint(time,
                         self.config.property_package.component_list,
                         doc="Component removal equation")
        def component_removal_equation(b, t, j):
            return (b.removal_fraction[t, j] *
                    b.flow_vol_in[t] * b.conc_mass_in[t, j] ==
                    b.flow_vol_waste[t] * b.conc_mass_waste[t, j])

    @self.Constraint(time,
                     self.config.property_package.component_list,
                     doc="Component mass balances")
    def component_mass_balance(b, t, j):
        return (b.flow_vol_in[t] * b.conc_mass_in[t, j] ==
                b.flow_vol_out[t] * b.conc_mass_out[t, j] +
                b.flow_vol_waste[t] * b.conc_mass_waste[t, j])

    @self.Constraint(time, doc="Outlet temperature equation")
    def outlet_temperature_constraint(b, t):
        return b.temperature_in[t] == b.temperature_out[t]

    @self.Constraint(time, doc="Waste temperature equation")
    def waste_temperature_constraint(b, t):
        return b.temperature_in[t] == b.temperature_waste[t]

    # The last step is to create Ports representing the three streams
    # Add an empty Port for the inlet
    self.inlet = Port(noruleinit=True, doc="Inlet Port")

    # Populate Port with inlet variables
    self.inlet.add(self.flow_vol_in, "flow_vol")
    self.inlet.add(self.conc_mass_in, "conc_mass")
    self.inlet.add(self.temperature_in, "temperature")
    self.inlet.add(self.pressure_in, "pressure")

    # Add Ports for outlet and waste streams
    self.outlet = Port(noruleinit=True, doc="Outlet Port")
    self.outlet.add(self.flow_vol_out, "flow_vol")
    self.outlet.add(self.conc_mass_out, "conc_mass")
    self.outlet.add(self.temperature_out, "temperature")
    self.outlet.add(self.pressure_out, "pressure")

    self.waste = Port(noruleinit=True, doc="Waste Port")
    self.waste.add(self.flow_vol_waste, "flow_vol")
    self.waste.add(self.conc_mass_waste, "conc_mass")
    self.waste.add(self.temperature_waste, "temperature")
    self.waste.add(self.pressure_waste, "pressure")


def initialization(self, *args, **kwargs):
    # All IDAES models are expected ot have an initialization routine
    # We will need to add one here and it will be fairly simple,
    # but I will skip it for now
    pass