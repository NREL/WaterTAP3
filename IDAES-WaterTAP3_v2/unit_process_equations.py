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
############################# Pyomo components are added with the add_component method# Pyomo components are added with the add_component method##################################################
"""
Demonstration zeroth-order model for WaterTAP3
"""

# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import Block, Constraint, Var, units as pyunits
from pyomo.network import Port

from pyomo.environ import PositiveReals #ariel

# Import IDAES cores
from idaes.core import (declare_process_block_class,
                        UnitModelBlockData,
                        useDefault)
from idaes.core.util.config import is_physical_parameter_block

from pyomo.environ import (
    Expression, Var, Param, NonNegativeReals, units as pyunits)

# Import WaterTAP# finanacilas module
import financials
from financials import * #ARIEL ADDED

from pyomo.environ import ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import Arc
from idaes.core import FlowsheetBlock

# Import properties and units from "WaterTAP Library"
from water_props import WaterParameterBlock

  
    
def build_up(self, up_name_test = None):
    
    if up_name_test == "nanofiltration_twb": import nanofiltration_twb as unit_process_model
    if up_name_test == "chlorination_twb": import chlorination_twb as unit_process_model
    if up_name_test == "media_filtration": import media_filtration as unit_process_model  
    if up_name_test == "coag_and_floc": import coag_and_floc as unit_process_model  
    if up_name_test == "lime_softening": import lime_softening as unit_process_model
    if up_name_test == "ro_deep": import ro_deep as unit_process_model 
    if up_name_test == "treated_storage_24_hr": import treated_storage_24_hr as unit_process_model
    if up_name_test == "sedimentation": import sedimentation as unit_process_model
    if up_name_test == "water_pumping_station": import water_pumping_station as unit_process_model
    if up_name_test == "sulfuric_acid_addition": import sulfuric_acid_addition as unit_process_model   
    if up_name_test == "sodium_bisulfite_addition": import sodium_bisulfite_addition as unit_process_model
    if up_name_test == "co2_addition": import co2_addition as unit_process_model
    if up_name_test == "ammonia_addition": import ammonia_addition as unit_process_model 
    if up_name_test == "municipal_drinking": import municipal_drinking as unit_process_model 
    if up_name_test == "sw_onshore_intake": import sw_onshore_intake as unit_process_model 
    if up_name_test == "holding_tank": import holding_tank as unit_process_model 
    if up_name_test == "tri_media_filtration": import tri_media_filtration as unit_process_model
    if up_name_test == "cartridge_filtration": import cartridge_filtration as unit_process_model    
    if up_name_test == "backwash_solids_handling": import backwash_solids_handling as unit_process_model
    if up_name_test == "surface_discharge": import surface_discharge as unit_process_model    
    if up_name_test == "landfill": import landfill as unit_process_model   
    if up_name_test == "coagulant_addition": import coagulant_addition as unit_process_model  
    if up_name_test == "ro_deep_scnd_pass": import ro_deep_scnd_pass as unit_process_model
        

    """
    The build method is the core of the unit model, and contains the rules
    for building the Vars and Constraints that make up the unit model.
    """
    # build always starts by calling super().build()
    # This triggers a lot of boilerplate in the background for you
    super(unit_process_model.UnitProcessData, self).build()

    # Next, get the base units of measurement from the property definition
    units_meta = self.config.property_package.get_metadata().get_derived_units

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
    if up_name_test == "chlorination_twb":
        unit_process_model.get_additional_variables(self, units_meta, time)
    if up_name_test == "ro_deep":
        unit_process_model.get_additional_variables(self, units_meta, time)
    if up_name_test == "ro_deep_scnd_pass":
        unit_process_model.get_additional_variables(self, units_meta, time)
        
    self.flow_vol_in = Var(time,
                           initialize=1,
                           units=units_meta("volume")/units_meta("time"),
                           doc="Volumetric flowrate of water into unit")
    self.conc_mass_in = Var(time,
                            self.config.property_package.component_list,
                            initialize=1e-5,
                            #bounds=(1e-6, 1e10),
                            units=units_meta("mass")/units_meta("volume"),
                            doc="Mass concentration of species at inlet")
    self.temperature_in = Var(time,
                              initialize=300,
                              units=units_meta("temperature"),
                              doc="Temperature at inlet")
    self.pressure_in = Var(time,
                           initialize=1e5,
                           units=units_meta("pressure"),
                           doc="Pressure at inlet")

    # Add similar variables for outlet and waste stream
    self.flow_vol_out = Var(time,
                            initialize=1,
                            units=units_meta("volume")/units_meta("time"),
                            doc="Volumetric flowrate of water out of unit")
    self.conc_mass_out = Var(time,
                             self.config.property_package.component_list,
                             initialize=0,
                             #bounds=(1e-6, 1e10),
                             units=units_meta("mass")/units_meta("volume"),
                             doc="Mass concentration of species at outlet")
    self.temperature_out = Var(time,
                               initialize=300,
                               units=units_meta("temperature"),
                               doc="Temperature at outlet")
    self.pressure_out = Var(time,
                            initialize=1e5,
                            units=units_meta("pressure"),
                            doc="Pressure at outlet")

    self.flow_vol_waste = Var(
        time,
        initialize=1,
        units=units_meta("volume")/units_meta("time"),
        doc="Volumetric flowrate of water in waste")
    self.conc_mass_waste = Var(
        time,
        self.config.property_package.component_list,
        initialize=0,
        #bounds=(1e-6, 1e10),
        units=units_meta("mass")/units_meta("volume"),
        doc="Mass concentration of species in waste")
    self.temperature_waste = Var(time,
                                 initialize=300,
                                 units=units_meta("temperature"),
                                 doc="Temperature of waste")
    self.pressure_waste = Var(time,
                              initialize=1e5,
                              units=units_meta("pressure"),
                              doc="Pressure of waste")

    # Next, add additional variables for unit performance
    self.deltaP_outlet = Var(time,
                             initialize=1e4,
                             units=units_meta("pressure"),
                             doc="Pressure change between inlet and outlet")
    self.deltaP_waste = Var(time,
                            initialize=1e4,
                            units=units_meta("pressure"),
                            doc="Pressure change between inlet and waste")

    # Then, recovery and removal variables
    self.water_recovery = Var(time,
                              initialize=0.8, #TODO: NEEDS TO BE DIFFERENT?
                              #within=PositiveReals,
                              units=pyunits.dimensionless,
                              bounds=(0.000001, 1.0000001),
                              doc="Water recovery fraction")
    self.removal_fraction = Var(time,
                                self.config.property_package.component_list,
                                initialize=0.01, #TODO: NEEDS TO BE DIFFERENT?
                                units=pyunits.dimensionless,
                                doc="Component removal fraction")

    # Next, add constraints linking these
    @self.Constraint(time, doc="Overall flow balance")
    def flow_balance(b, t):
        return b.flow_vol_in[t] == b.flow_vol_out[t] + b.flow_vol_waste[t]

    @self.Constraint(time,
                     self.config.property_package.component_list,
                     doc="Component mass balances")
    def component_mass_balance(b, t, j):
        return (b.flow_vol_in[t]*b.conc_mass_in[t, j] ==
                b.flow_vol_out[t]*b.conc_mass_out[t, j] +
                b.flow_vol_waste[t]*b.conc_mass_waste[t, j])

    @self.Constraint(time, doc="Outlet temperature equation")
    def outlet_temperature_constraint(b, t):
        return b.temperature_in[t] == b.temperature_out[t]

    @self.Constraint(time, doc="Waste temperature equation")
    def waste_temperature_constraint(b, t):
        return b.temperature_in[t] == b.temperature_waste[t]

    @self.Constraint(time, doc="Outlet pressure equation")
    def outlet_pressure_constraint(b, t):
        return (b.pressure_in[t] ==
                b.pressure_out[t] + b.deltaP_outlet[t])

    @self.Constraint(time, doc="Waste pressure equation")
    def waste_pressure_constraint(b, t):
        return (b.pressure_in[t] ==
                b.pressure_waste[t] + b.deltaP_waste[t])

    # Finally, add removal and recovery equations
    @self.Constraint(time, doc="Water recovery equation")
    def recovery_equation(b, t):
        return b.water_recovery[t] * b.flow_vol_in[t] == b.flow_vol_out[t]

    @self.Constraint(time,
                     self.config.property_package.component_list,
                     doc="Component removal equation")
    def component_removal_equation(b, t, j):
        return (b.removal_fraction[t, j] *
                b.flow_vol_in[t] * b.conc_mass_in[t, j] ==
                b.flow_vol_waste[t] * b.conc_mass_waste[t, j])

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