##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
##############################################################################

# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.network import Port
# Import IDAES cores
from idaes.core import (UnitModelBlockData, declare_process_block_class, useDefault)
from idaes.core.util.config import is_physical_parameter_block


__all__ = ['UnitProcess']

### MODULE NAME ###
module_name = "mixer_mar5"


@declare_process_block_class("UnitProcess")
class UnitProcessData(UnitModelBlockData):
       
    """
    This class describes the rules for a zeroth-order model for a unit
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

    #unit_process_equations.get_base_unit_process()

    #build(up_name = "nanofiltration_twb")
    
    def build(self):
        
        import mixer_mar5 as unit_process_model
        super(unit_process_model.UnitProcessData, self).build()
        units_meta = self.config.property_package.get_metadata().get_derived_units        
        
        return print("adding mixer")
    
    
    def get_mix(self, inlet_list=None):

        print(inlet_list)

        time = self.flowsheet().config.time
        units_meta = self.config.property_package.get_metadata().get_derived_units
        
        # Add ports
        for p in inlet_list:
            setattr(self, p, Port(noruleinit=True, doc="inlet Port")) #ARIEL  

            setattr(self, ("flow_vol_%s" % p), Var(time,
                                    initialize=1,
                                    units=units_meta("volume")/units_meta("time"),
                                    doc="Volumetric flowrate of water out of unit"))

            setattr(self, ("conc_mass_%s" % p), Var(time,
                                     self.config.property_package.component_list,
                                     initialize=0,
                                     units=units_meta("mass")/units_meta("volume"),
                                     doc="Mass concentration of species at inlet"))

            setattr(self, ("pressure_%s" % p), Var(time,
                                    initialize=1e5,
                                    units=units_meta("pressure"),
                                    doc="Pressure at inlet"))

            setattr(self, ("temperature_%s" % p), Var(time,
                                       initialize=300,
                                       units=units_meta("temperature"),
                                       doc="Temperature at inlet"))

            getattr(self, p).add(getattr(self, ("temperature_%s" % p)), "temperature")
            getattr(self, p).add(getattr(self, ("pressure_%s" % p)), "pressure")
            getattr(self, p).add(getattr(self, ("conc_mass_%s" % p)), "conc_mass")
            getattr(self, p).add(getattr(self, ("flow_vol_%s" % p)), "flow_vol")

        self.outlet = Port(noruleinit=True, doc="outlet Port") #ARIEL

        self.flow_vol_out = Var(time,
                                initialize=1,
                                units=units_meta("volume")/units_meta("time"),
                                doc="Volumetric flowrate of water out of unit")
        self.conc_mass_out = Var(time,
                                 self.config.property_package.component_list,
                                 initialize=0,
                                 units=units_meta("mass")/units_meta("volume"),
                                 doc="Mass concentration of species at inlet")
        self.temperature_out = Var(time,
                                   initialize=300,
                                   units=units_meta("temperature"),
                                   doc="Temperature at inlet")
        self.pressure_out = Var(time,
                                initialize=1e5,
                                units=units_meta("pressure"),
                                doc="Pressure at inlet")

#         self.split_fraction = Var(time,
#                                 initialize=0.5,
#                                 units=units_meta("pressure"),
#                                 doc="split fraction")

        self.outlet.add(self.flow_vol_out, "flow_vol")
        self.outlet.add(self.conc_mass_out, "conc_mass")
        self.outlet.add(self.temperature_out, "temperature")
        self.outlet.add(self.pressure_out, "pressure")

        t = self.flowsheet().config.time.first() 

        @self.Constraint(time, doc="Overall flow balance")
        def flow_balance(b, t):
            flow_vol_sum = 0 
            for p in inlet_list:
                flow_vol_sum = getattr(b, ("flow_vol_%s" % p))[t] + flow_vol_sum
            
            return flow_vol_sum == b.flow_vol_out[t]
        
        
        @self.Constraint(time,
                         self.config.property_package.component_list,
                         doc="Component mass balances")
        def component_mass_balance(b, t, j):
            
            component_sum = 0
            for p in inlet_list:
                component_sum = getattr(b, ("flow_vol_%s" % p))[t] * getattr(b, ("conc_mass_%s" % p))[t, j] + component_sum
                
            return component_sum == b.flow_vol_out[t]*b.conc_mass_out[t, j]       
        
        @self.Constraint(time, doc="Outlet temperature equation")
        def outlet_temperature_constraint(b, t):
            
            temperature_sum = 0 
            for p in inlet_list:
                temperature_sum = getattr(b, ("temperature_%s" % p))[t] + temperature_sum
            
            return temperature_sum / len(inlet_list) == b.temperature_out[t]
        
        
        @self.Constraint(time, doc="Outlet pressure equation")
        def outlet_pressure_constraint(b, t):
            
            pressure_sum = 0 
            for p in inlet_list:
                pressure_sum = getattr(b, ("pressure_%s" % p))[t] + pressure_sum            
            
            return pressure_sum / len(inlet_list) == b.pressure_out[t]

        
        
        
        