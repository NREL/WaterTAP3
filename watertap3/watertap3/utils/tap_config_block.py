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

# Import IDAES cores
from idaes.core import (useDefault)
from idaes.core.util.config import is_physical_parameter_block

# Import WaterTAP financials module

# Import properties and units from "WaterTAP Library"


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
    
    
    