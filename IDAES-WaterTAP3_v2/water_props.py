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
Demonstration property package for WaterTAP3

For WaterTAP3 models, this package primarily needs to define the following:
    - a trivial phase list
    - components in the system for removal
    - base units of measurement
"""

# Import Pyomo libraries
from pyomo.environ import units

# Import IDAES cores
from idaes.core import (declare_process_block_class,
                        PhysicalParameterBlock,
                        StateBlockData)
from idaes.core.phases import LiquidPhase
from idaes.core.components import Component
import pandas as pd


# You don't really want to know what this decorator does
# Suffice to say it automates a lot of Pyomo boilerplate for you
@declare_process_block_class("WaterParameterBlock")
class PhysicalParameterData(PhysicalParameterBlock):
    """
    Property Parameter Block Class

    Define component and phase lists, along with base units
    """

    def build(self):
        '''
        Callable method for Block construction.
        '''
        super(PhysicalParameterData, self).build()

        self._state_block_class = WaterStateBlock

        # Add Phase objects
        self.Liq = LiquidPhase()

        # Add Component objects - only include contaminants, etc here
        # Water is assumed to always be present
        
        ### MAKE THIS BASED ON THE DATA INPUT?!?! ###
        import generate_constituent_list
        train_constituent_list = generate_constituent_list.run(self.parent_block())
        
        for constituent_name in train_constituent_list:
        #for constituent_name in ["TOC", "nitrates", "TDS"]:
            setattr(self, constituent_name, Component())


    @classmethod
    def define_metadata(cls, obj):
        obj.add_default_units({'time': units.s,
                               'length': units.m,
                               'mass': units.kg,
                               'amount': units.mol,
                               'temperature': units.K})


@declare_process_block_class("WaterStateBlock")
class WaterStateBlockData(StateBlockData):
    """
    This won;t actually be used for most WaterTAP3 models, but is included to
    allow for future integration with ProteusLib and IDAES
    """

    def build(self):
        """
        Callable method for Block construction
        """
        return NotImplementedError()
