import sys
sys.path.append('/Users/ksitterl/Documents/Python/watertap3/NAWI-WaterTAP3/watertap3/watertap3')
sys.path.append('/Users/ksitterl/Documents/Python/watertap3/NAWI-WaterTAP3/watertap3/watertap3/build')
sys.path.append('/Users/ksitterl/Documents/Python/watertap3/NAWI-WaterTAP3/watertap3/watertap3/wt_units')

from idaes.core import PhysicalParameterBlock
from idaes.core import StateBlock
from idaes.core import StateBlockData
from idaes.core import declare_process_block_class
from idaes.core.util.model_statistics import degrees_of_freedom
from pyomo.environ import ConcreteModel
from pyomo.environ import Constraint
from pyomo.environ import Expression
from pyomo.environ import Param
from pyomo.environ import Set
from pyomo.environ import Var
from pyomo.environ import units as pyunits
from pyomo.opt import SolverFactory


from . import wt_units
from . import utils

__all__ = [
           'ConcreteModel',
           'Constraint',
           'Expression',
           'Var',
           'Set',
           'Param',
           'PhysicalParameterBlock',
           'StateBlock',
           'StateBlockData',
           'SolverFactory',
           'degrees_of_freedom',
           'declare_process_block_class',
           'pyunits',
           *utils.__all__,
           *wt_units.__all__
        ]

print('this is in the __init__ file for watertap3')

