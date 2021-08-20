from idaes.core import (PhysicalParameterBlock, StateBlockData, declare_process_block_class)
from idaes.core.components import Component
from idaes.core.phases import LiquidPhase
from pyomo.environ import units as pyunits

from . import generate_constituent_list

__all__ = ['WaterParameterBlock',
           'WaterStateBlock']


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

        self.Liq = LiquidPhase()
        train_constituent_list = generate_constituent_list.run(self.parent_block())

        for constituent_name in train_constituent_list:
            setattr(self, constituent_name, Component())

    @classmethod
    def define_metadata(cls, obj):
        obj.add_default_units({
                'time': pyunits.s,
                'length': pyunits.m,
                'mass': pyunits.kg,
                'amount': pyunits.mol,
                'temperature': pyunits.K,
                'volume': pyunits.liter
                })


@declare_process_block_class("WaterStateBlock")
class WaterStateBlockData(StateBlockData):
    """
    This won't actually be used for most WaterTAP3 models, but is included to
    allow for future integration with ProteusLib and IDAES
    """

    def build(self):
        """
        Callable method for Block construction
        """
        return NotImplementedError()