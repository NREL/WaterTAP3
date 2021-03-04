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
##############################################################################
"""
Demonstration source model for WaterTAP3. This is the same as a unit process, but can be simplified and/or new features added.
"""

# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import Block, Constraint, Var, units as pyunits
from pyomo.network import Port
from pyomo.environ import PositiveReals, NonNegativeReals
# Import IDAES cores
from idaes.core import (declare_process_block_class,
                        UnitModelBlockData,
                        useDefault)
from idaes.core.util.config import is_physical_parameter_block

# Import WaterTAP# finanacilas module
import financials

module_name = "source_example"

# You don't really want to know what this decorator does
# Suffice to say it automates a lot of Pyomo boilerplate for you
@declare_process_block_class("UnitProcess")
class UnitProcessData(UnitModelBlockData):
    """
    This class describes the rules for a zeroth-order model for a NF unit
    """
    # The Config Block is used tpo process arguments from when the model is
    # instantiated. In IDAES, this serves two purposes:
    #     1. Allows us to separate physical properties from unit models
    #     2. Lets us give users options for configuring complex units
    # For WaterTAP3, this will mainly be boilerplate to keep things consistent
    # with ProteusLib and IDAES.
    # The dynamic and has_holdup options are expected arguments which must exist
    # The property package arguments let us define different sets of contaminants
    # without needing to write a new model.
    CONFIG = ConfigBlock()
    CONFIG.declare("dynamic", ConfigValue(
        domain=In([False]),
        default=False,
        description="Dynamic model flag - must be False",
        doc="""Indicates whether this model will be dynamic or not,
**default** = False. Equilibrium Reactors do not support dynamic behavior."""))
    CONFIG.declare("has_holdup", ConfigValue(
        default=False,
        domain=In([False]),
        description="Holdup construction flag - must be False",
        doc="""Indicates whether holdup terms should be constructed or not.
**default** - False. Equilibrium reactors do not have defined volume, thus
this must be False."""))
    CONFIG.declare("property_package", ConfigValue(
        default=useDefault,
        domain=is_physical_parameter_block,
        description="Property package to use for control volume",
        doc="""Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PhysicalParameterObject** - a PhysicalParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(
        implicit=True,
        description="Arguments to use for constructing property packages",
        doc="""A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see property package for documentation.}"""))
    
    from unit_process_equations import initialization
    
    def build(self):
        
        import source_example as unit_process_model
        
        # build always starts by calling super().build()
        # This triggers a lot of boilerplate in the background for you
        super(unit_process_model.UnitProcessData, self).build()        
        
        units_meta = self.config.property_package.get_metadata().get_derived_units
        
        return print("adding source")
    
    def set_source(self): #, unit_params = None): #, module=financials, cost_method="wt", year=None):

        

        # Next, get the base units of measurement from the property definition
        units_meta = self.config.property_package.get_metadata().get_derived_units

        # Also need to get time domain
        # This will not be used for WaterTAP3, but will be needed to integrate
        # with ProteusLib dynamic models
        time = self.flowsheet().config.time       
        
        # add inlet ports
        self.inlet = Port(noruleinit=True, doc="Inlet Port") #ARIEL

        self.flow_vol_in = Var(time,
                               initialize=1,
                               domain=NonNegativeReals,
                               units=units_meta("volume")/units_meta("time"),
                               doc="Volumetric flowrate of water into unit")
        self.conc_mass_in = Var(time,
                                self.config.property_package.component_list,
                                domain=NonNegativeReals,
                                initialize=1e-5,
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

        
        
        # add outlet ports
        self.outlet = Port(noruleinit=True, doc="outlet Port") #ARIEL

        # Add similar variables for outlet and waste stream
        self.flow_vol_out = Var(time,
                                initialize=1,
                                domain=NonNegativeReals,
                                units=units_meta("volume")/units_meta("time"),
                                doc="Volumetric flowrate of water out of unit")
        self.conc_mass_out = Var(time,
                                 self.config.property_package.component_list,
                                 initialize=0,
                                 domain=NonNegativeReals,
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


        
        # Populate Port with inlet variables
        self.inlet.add(self.flow_vol_in, "flow_vol")
        self.inlet.add(self.conc_mass_in, "conc_mass")
        self.inlet.add(self.temperature_in, "temperature")
        self.inlet.add(self.pressure_in, "pressure")

        # Add Ports for outlet and waste streams
        self.outlet.add(self.flow_vol_out, "flow_vol")
        self.outlet.add(self.conc_mass_out, "conc_mass")
        self.outlet.add(self.temperature_out, "temperature")
        self.outlet.add(self.pressure_out, "pressure")
        
        t = self.flowsheet().config.time.first()
        
        self.temperature_in.fix(300)
        self.pressure_in.fix(1)

        for j in self.config.property_package.component_list:
            setattr(self, ("%s_eq" % j), Constraint(expr = self.conc_mass_in[t, j] 
                                                    == self.conc_mass_out[t, j]))

        self.eq_flow = Constraint(expr = self.flow_vol_in[t] == self.flow_vol_out[t])

        self.eq_temp = Constraint(expr = self.temperature_in[t] == self.temperature_out[t])

        self.eq_pres = Constraint(expr = self.pressure_in[t] == self.pressure_out[t])                
            
            
        
#         self.flow_vol_in = Var(time,
#                                initialize=1,
#                                units=units_meta("volume")/units_meta("time"),
#                                doc="Volumetric flowrate of water into unit")
#         self.conc_mass_in = Var(time,
#                                 self.config.property_package.component_list,
#                                 initialize=0,
#                                 units=units_meta("mass")/units_meta("volume"),
#                                 doc="Mass concentration of species at inlet")
#         self.temperature_in = Var(time,
#                                   initialize=300,
#                                   units=units_meta("temperature"),
#                                   doc="Temperature at inlet")
#         self.pressure_in = Var(time,
#                                initialize=1e5,
#                                units=units_meta("pressure"),
#                                doc="Pressure at inlet")

#         # Add similar variables for outlet and waste stream
#         self.flow_vol_out = Var(time,
#                                 initialize=1,
#                                 units=units_meta("volume")/units_meta("time"),
#                                 doc="Volumetric flowrate of water out of unit")
#         self.conc_mass_out = Var(time,
#                                  self.config.property_package.component_list,
#                                  initialize=0,
#                                  units=units_meta("mass")/units_meta("volume"),
#                                  doc="Mass concentration of species at outlet")
#         self.temperature_out = Var(time,
#                                    initialize=300,
#                                    units=units_meta("temperature"),
#                                    doc="Temperature at outlet")
#         self.pressure_out = Var(time,
#                                 initialize=1e5,
#                                 units=units_meta("pressure"),
#                                 doc="Pressure at outlet")

#         self.flow_vol_waste = Var(
#             time,
#             initialize=1,
#             units=units_meta("volume")/units_meta("time"),
#             doc="Volumetric flowrate of water in waste")
#         self.conc_mass_waste = Var(
#             time,
#             self.config.property_package.component_list,
#             initialize=0,
#             units=units_meta("mass")/units_meta("volume"),
#             doc="Mass concentration of species in waste")
        
#         self.temperature_waste = Var(time,
#                                      initialize=300,
#                                      units=units_meta("temperature"),
#                                      doc="Temperature of waste")
#         self.pressure_waste = Var(time,
#                                   initialize=1e5,
#                                   units=units_meta("pressure"),
#                                   doc="Pressure of waste")

#         # Next, add additional variables for unit performance
#         self.deltaP_outlet = Var(time,
#                                  initialize=1e4,
#                                  units=units_meta("pressure"),
#                                  doc="Pressure change between inlet and outlet")
#         self.deltaP_waste = Var(time,
#                                 initialize=1e4,
#                                 units=units_meta("pressure"),
#                                 doc="Pressure change between inlet and waste")

#         # Then, recovery and removal variables
#         self.water_recovery = Var(time,
#                                   initialize=1.0,
#                                   units=pyunits.dimensionless,
#                                   doc="Water recovery fraction")
#         self.removal_fraction = Var(time,
#                                     self.config.property_package.component_list,
#                                     initialize=1e4,
#                                     units=pyunits.dimensionless,
#                                     doc="Component removal fraction")

#         # Next, add constraints linking these
#         @self.Constraint(time, doc="Overall flow balance")
#         def flow_balance(b, t):
#             return b.flow_vol_in[t] == b.flow_vol_out[t] + b.flow_vol_waste[t]

#         @self.Constraint(time,
#                          self.config.property_package.component_list,
#                          doc="Component mass balances")
#         def component_mass_balance(b, t, j):
#             return (b.flow_vol_in[t]*b.conc_mass_in[t, j] ==
#                     b.flow_vol_out[t]*b.conc_mass_out[t, j] +
#                     b.flow_vol_waste[t]*b.conc_mass_waste[t, j])

#         @self.Constraint(time, doc="Outlet temperature equation")
#         def outlet_temperature_constraint(b, t):
#             return b.temperature_in[t] == b.temperature_out[t]

#         @self.Constraint(time, doc="Waste temperature equation")
#         def waste_temperature_constraint(b, t):
#             return b.temperature_in[t] == b.temperature_waste[t]

#         @self.Constraint(time, doc="Outlet pressure equation")
#         def outlet_pressure_constraint(b, t):
#             return (b.pressure_in[t] ==
#                     b.pressure_out[t] + b.deltaP_outlet[t])

#         @self.Constraint(time, doc="Waste pressure equation")
#         def waste_pressure_constraint(b, t):
#             return (b.pressure_in[t] ==
#                     b.pressure_waste[t])

#         # Finally, add removal and recovery equations
#         @self.Constraint(time, doc="Water recovery equation")
#         def recovery_equation(b, t):
#             return b.water_recovery[t] * b.flow_vol_in[t] == b.flow_vol_out[t]

#         @self.Constraint(time,
#                          self.config.property_package.component_list,
#                          doc="Component removal equation")
#         def component_removal_equation(b, t, j):
#             return (b.removal_fraction[t, j] *
#                     b.flow_vol_in[t] * b.conc_mass_in[t, j] ==
#                     b.flow_vol_waste[t] * b.conc_mass_waste[t, j])

#         # The last step is to create Ports representing the three streams
#         # Add an empty Port for the inlet
#         self.inlet = Port(noruleinit=True, doc="Inlet Port")

#         # Populate Port with inlet variables
#         self.inlet.add(self.flow_vol_in, "flow_vol")
#         self.inlet.add(self.conc_mass_in, "conc_mass")
#         self.inlet.add(self.temperature_in, "temperature")
#         self.inlet.add(self.pressure_in, "pressure")

#         # Add Ports for outlet and waste streams
#         self.outlet = Port(noruleinit=True, doc="Outlet Port")
#         self.outlet.add(self.flow_vol_out, "flow_vol")
#         self.outlet.add(self.conc_mass_out, "conc_mass")
#         self.outlet.add(self.temperature_out, "temperature")
#         self.outlet.add(self.pressure_out, "pressure")
#         #self.outlet.add(self.flow_mass_comp, "flow_mass_comp") # TODO for pump
        
        
#         self.waste = Port(noruleinit=True, doc="Waste Port")
#         self.waste.add(self.flow_vol_waste, "flow_vol")
#         self.waste.add(self.conc_mass_waste, "conc_mass")
#         self.waste.add(self.temperature_waste, "temperature")
#         self.waste.add(self.pressure_waste, "pressure")

#     def initialization(self, *args, **kwargs):
#         # All IDAES models are expected ot have an initialization routine
#         # We will need to add one here and it will be fairly simple,
#         # but I will skip it for now
#         pass

#     def get_costing(self, module=financials, cost_method="wt", year=None):
#         """
#         We need a get_costing method here to provide a point to call the
#         costing methods, but we call out to an external consting module
#         for the actual calculations. This lets us easily swap in different
#         methods if needed.

#         Within IDAES, the year argument is used to set the initial value for
#         the cost index when we build the model.
#         """
#         # First, check to see if global costing module is in place
#         # Construct it if not present and pass year argument
#         if not hasattr(self.flowsheet(), "costing"):
#             self.flowsheet().get_costing(module=module, year=year)

#         # Next, add a sub-Block to the unit model to hold the cost calculations
#         # This is to let us separate costs from model equations when solving
#         self.costing = Block()
#         # Then call the appropriate costing function out of the costing module
#         # The first argument is the Block in which to build the equations
#         # Can pass additional arguments a needed
#         module.up_costing(self.costing,
#                           cost_method=cost_method)
