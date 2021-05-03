# import sys
# sys.path.append('/Users/ksitterl/Documents/Python/watertap3/NAWI-WaterTAP3/src/watertapp3/build')
# sys.path.append('/Users/ksitterl/Documents/Python/watertap3/NAWI-WaterTAP3/src/watertapp3/wt_units')

# import watertap as wt
# import sys
# from pathlib import Path # if you haven't already done so
# file = Path(__file__).resolve()
# parent, root = file.parent, file.parents[1]
# sys.path.append(str(root))
#
# # Additionally remove the current file's directory from sys.path
# try:
#     sys.path.remove(str(parent))
# except ValueError: # Already removed
#     pass

from . import app3
from .app3 import *
from . import constituent_removal_water_recovery
from .constituent_removal_water_recovery import *
from . import cost_curves
from .cost_curves import *
from . import design
from .design import *
from . import display
from .display import *
# from . import excel_cleaning
from . import financials
from .financials import *
from . import get_graph_chars
from .get_graph_chars import *
from . import importfile
from .importfile import *
from . import mixer_example
from .mixer_example import *
# from mixer_example import Mixer1
from . import mixer_mar5
from .mixer_mar5 import *
from . import ml_regression
from .ml_regression import *
from . import module_import
from .module_import import *
from . import optimize_setup
from .optimize_setup import *
from . import post_processing
from .post_processing import *
from . import sensitivity_runs
from .sensitivity_runs import *
from . import split_test2
from .split_test2 import *
from . import splitter_mar1
from .splitter_mar1 import *
from . import unit_process_equations
from .unit_process_equations import *
from . import case_study_trains
from .case_study_trains import *
from . import generate_constituent_list
from .generate_constituent_list import *
from . import water_props
from .water_props import *
from . import watertap
from .watertap import *
import watertap3.wt_units as wt_units
import warnings

from pyomo.environ import Block, ConcreteModel, SolverFactory, TransformationFactory
from pyomo.network import Port, SequentialDecomposition
from idaes.core import FlowsheetBlock
from pyomo.common.config import ConfigBlock, ConfigValue, In
from idaes.core.util.model_statistics import degrees_of_freedom
import pyomo.environ as env
import ast

__all__ = ['ConcreteModel',
           'SolverFactory',
           'TransformationFactory',
           'SequentialDecomposition',
           'Block',
           'Port',
           'FlowsheetBlock',
           'ConfigBlock',
           'ConfigValue',
           'In',
           'degrees_of_freedom',
           'env',
           'ast',
           'warnings',
           *app3.__all__,
           *constituent_removal_water_recovery.__all__,
           *cost_curves.__all__,
           *design.__all__,
           *display.__all__,
           *financials.__all__,
           *get_graph_chars.__all__,
           *importfile.__all__,
           *mixer_example.__all__,
           *mixer_mar5.__all__,
           *ml_regression.__all__,
           *module_import.__all__,
           *optimize_setup.__all__,
           *post_processing.__all__,
           # *sensitivity_runs.__all__,
           *split_test2.__all__,
           *splitter_mar1.__all__,
           *case_study_trains.__all__,
           *generate_constituent_list.__all__,
           *water_props.__all__,
           *watertap.__all__
           # *wt_units.__all__
           ]

print('this is in the __init__ file for utils')