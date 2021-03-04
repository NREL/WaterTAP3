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
Demonstration zeroth-order model for WaterTAP3
"""

# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyomo.environ import Block, Constraint, Var, units as pyunits
from pyomo.network import Port


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

import numpy as np


### MODULE NAME ###
module_name = "splitter_mar1"


##########################################
##########################################

# You don't really want to know what this decorator does
# Suffice to say it automates a lot of Pyomo boilerplate for you
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
    
    from unit_process_equations import initialization
    #unit_process_equations.get_base_unit_process()

    #build(up_name = "nanofiltration_twb")
    
    def build(self):
        
        import splitter_mar1 as unit_process_model
        
        # build always starts by calling super().build()
        # This triggers a lot of boilerplate in the background for you
        super(unit_process_model.UnitProcessData, self).build()

        # Next, get the base units of measurement from the property definition
        units_meta = self.config.property_package.get_metadata().get_derived_units        
        
        return print("adding splitter") #unit_process_equations.build_up(self, up_name_test = module_name)
    
    
    def get_split(self, outlet_list=None):

        
        #print(outlet_list)
        
#         if not hasattr(self.flowsheet(), "costing"):
#             self.flowsheet().get_costing(module=module, year=year)
            
            
        # Add ports and variables for outlets and inlets
        time = self.flowsheet().config.time
        units_meta = self.config.property_package.get_metadata().get_derived_units
        
        # Add ports
        for p in outlet_list:
            setattr(self, p, Port(noruleinit=True, doc="Outlet Port")) #ARIEL  

            setattr(self, ("flow_vol_%s" % p), Var(time,
                                    initialize=1,
                                    units=units_meta("volume")/units_meta("time"),
                                    doc="Volumetric flowrate of water out of unit"))

            setattr(self, ("conc_mass_%s" % p), Var(time,
                                     self.config.property_package.component_list,
                                     initialize=0,
                                     units=units_meta("mass")/units_meta("volume"),
                                     doc="Mass concentration of species at outlet"))

            setattr(self, ("pressure_%s" % p), Var(time,
                                    initialize=1e5,
                                    units=units_meta("pressure"),
                                    doc="Pressure at outlet"))

            setattr(self, ("temperature_%s" % p), Var(time,
                                       initialize=300,
                                       units=units_meta("temperature"),
                                       doc="Temperature at outlet"))

            getattr(self, p).add(getattr(self, ("temperature_%s" % p)), "temperature")
            getattr(self, p).add(getattr(self, ("pressure_%s" % p)), "pressure")
            getattr(self, p).add(getattr(self, ("conc_mass_%s" % p)), "conc_mass")
            getattr(self, p).add(getattr(self, ("flow_vol_%s" % p)), "flow_vol")

        self.inlet = Port(noruleinit=True, doc="Inlet Port") #ARIEL

        self.flow_vol_in = Var(time,
                                initialize=1,
                                units=units_meta("volume")/units_meta("time"),
                                doc="Volumetric flowrate of water out of unit")
        self.conc_mass_in = Var(time,
                                 self.config.property_package.component_list,
                                 initialize=0,
                                 units=units_meta("mass")/units_meta("volume"),
                                 doc="Mass concentration of species at outlet")
        self.temperature_in = Var(time,
                                   initialize=300,
                                   units=units_meta("temperature"),
                                   doc="Temperature at outlet")
        self.pressure_in = Var(time,
                                initialize=1e5,
                                units=units_meta("pressure"),
                                doc="Pressure at outlet")

        self.split_fraction = Var(time,
                                initialize=0.5,
                                units=units_meta("pressure"),
                                doc="split fraction")

        self.inlet.add(self.flow_vol_in, "flow_vol")
        self.inlet.add(self.conc_mass_in, "conc_mass")
        self.inlet.add(self.temperature_in, "temperature")
        self.inlet.add(self.pressure_in, "pressure")
        
        self.split_fraction.fix(1 / len(outlet_list))

        t = self.flowsheet().config.time.first() 
        
        for p in outlet_list:
            for j in self.config.property_package.component_list:
                setattr(self, ("%s_%s_eq" % (p, j)), Constraint(expr = self.conc_mass_in[t, j] 
                                                        == getattr(self, ("conc_mass_%s" % p))[t, j]))
            
        for p in outlet_list:
            setattr(self, ("%s_eq_flow" % p), Constraint(expr = self.split_fraction[t] * self.flow_vol_in[t]
                                                    == getattr(self, ("flow_vol_%s" % p))[t]))

        for p in outlet_list:
            setattr(self, ("%s_eq_temp" % (p)), Constraint(expr = self.temperature_in[t] 
                                                    == getattr(self, ("temperature_%s" % p))[t]))
                
        for p in outlet_list:
            setattr(self, ("%s_eq_pres" % (p)), Constraint(expr = self.pressure_in[t] 
                                                    == getattr(self, ("pressure_%s" % p))[t]))                
#         @self.Constraint(time,
#                          outlet_list,
#                          doc="Component removal equation")
#         def flow_balance(b, t, o):        
#             return self.split_fraction[t] * b.flow_vol_in[t] == getattr(b, ("flow_vol_%s" % o))[t]        


#         @self.Constraint(time,
#                          self.config.property_package.component_list,
#                          doc="Component mass balances")
#         def component_mass_balance(b, t, j):
#             component_sum = 0
#             for p in outlet_list:
#                 component_sum = getattr(b, ("flow_vol_%s" % p))[t] * getattr(b, ("conc_mass_%s" % p))[t, j] + component_sum

#             return component_sum == b.flow_vol_in[t]*b.conc_mass_in[t, j]       

#         @self.Constraint(time, doc="Outlet temperature equation")
#         def outlet_temperature_constraint(b, t):

#             temperature_sum = 0 
#             for p in outlet_list:
#                 temperature_sum = getattr(b, ("temperature_%s" % p))[t] + temperature_sum

#             return temperature_sum / len(outlet_list) == b.temperature_in[t]


#         @self.Constraint(time, doc="Outlet pressure equation")
#         def outlet_pressure_constraint(b, t):

#             pressure_sum = 0 
#             for p in outlet_list:
#                 pressure_sum = getattr(b, ("pressure_%s" % p))[t] + pressure_sum            

#             return pressure_sum / len(outlet_list) == b.pressure_in[t]  
        
        
        
        